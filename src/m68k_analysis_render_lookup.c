#include "m68k_render_lookup_internal.h"
#include "m68k_bitset.h"
#include "m68k_disassembler.h"
#include "generated/mac_os_runtime.h"

#include <stdlib.h>
#include <time.h>

#include "m68k_affine_entry_value.inc"

/* Shared platform/source-analysis enrichment for M68kRenderLookup. */
uint32_t render_section_extent(const M68kDecodeSectionIR *section) {
  if (section == NULL) return 0U;
  return section->allocation_size > section->size ? section->allocation_size : section->size;
}

int accepted_start_at(const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t offset) {
  return section != NULL && accepted_start != NULL && offset < section->size && accepted_start[offset] != 0U;
}

uint32_t lookup_code_block_start_before_or_at(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->block_start_before_or_at == NULL ||
      lookup->block_start_before_or_at_extents == NULL ||
      lookup->block_start_before_or_at[section_index] == NULL ||
      lookup->block_start_before_or_at_extents[section_index] == 0U) {
    return 0U;
  }
  if (offset >= lookup->block_start_before_or_at_extents[section_index]) {
    offset = lookup->block_start_before_or_at_extents[section_index] - 1U;
  }
  return lookup->block_start_before_or_at[section_index][offset];
}

static double elapsed_seconds_local(clock_t start, clock_t end) {
  return (double)(end - start) / (double)CLOCKS_PER_SEC;
}

static const char *render_lookup_amiga_library_base_name_for_library_name(const char *library_name) {
  const char *base_name = platform_facts_v2_library_base_name_for_library_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    library_name);
  return base_name != NULL && base_name[0] != '\0' ? base_name : NULL;
}

static const char *render_lookup_amiga_library_base_name_for_name(const char *name) {
  const char *base_name = platform_facts_v2_library_base_name_for_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, name);
  return base_name != NULL && base_name[0] != '\0' ? base_name : NULL;
}

static int render_lookup_amiga_library_or_base_name_known(const char *name) {
  return render_lookup_amiga_library_base_name_for_name(name) != NULL;
}

static int analysis_accepted_byte_at(const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes,
    uint32_t offset) {
  return section != NULL && accepted_bytes != NULL && offset < section->size && accepted_bytes[offset] != 0U;
}

static const M68kSimFormMetadata *analysis_cfg_candidate_metadata(const M68kDecodeCandidate *candidate,
    M68kInstructionIR *instruction) {
  if (candidate == NULL || instruction == NULL) return NULL;
  if (m68k_decode_candidate_to_instruction(candidate, instruction) != 0) return NULL;
  return m68k_sim_metadata_for_instruction(instruction);
}

/* CFG coordinates are source coordinates. Decode-only absolute targets are raw
 * operand values until runtime-address facts or object relocations identify the
 * source location. Resolve once for both block boundaries and emitted edges. */
static const M68kFact *analysis_operand_relocation_ref(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, size_t operand_index);

static int analysis_cfg_control_target(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeCandidate *candidate, uint8_t *out_kind, uint32_t *out_offset) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata = analysis_cfg_candidate_metadata(candidate, &instruction);
  const M68kDecodeTarget *decoded_target = NULL;
  const M68kFact *relocation;
  uint32_t resolved_offset = UINT32_MAX;
  size_t resolved_section = SIZE_MAX;
  size_t index;
  uint8_t operand_index;
  int have_ref = 0;
  int ambiguous = 0;
  int absolute_operand;
  *out_offset = UINT32_MAX;
  if (metadata == NULL || (metadata->flow_kind != M68K_SIM_FLOW_CALL &&
      metadata->flow_kind != M68K_SIM_FLOW_JUMP && metadata->flow_kind != M68K_SIM_FLOW_BRANCH)) return 0;
  *out_kind = metadata->flow_kind == M68K_SIM_FLOW_CALL ? M68K_CFG_EDGE_CALL :
    metadata->flow_kind == M68K_SIM_FLOW_JUMP || !metadata->flow_conditional ?
      M68K_CFG_EDGE_JUMP : M68K_CFG_EDGE_BRANCH;
  operand_index = metadata->target_operand_index;
  if (operand_index >= candidate->operand_count || operand_index >= M68K_DECODE_IR_MAX_OPERANDS) return 1;
  for (index = 0U; index < candidate->target_count; ++index) {
    const M68kDecodeTarget *target = &candidate->targets[index];
    if (target->kind != M68K_DECODE_TARGET_BRANCH && target->kind != M68K_DECODE_TARGET_CALL &&
        target->kind != M68K_DECODE_TARGET_JUMP) continue;
    if (!target->has_operand) return 1;
    if (target->operand_index != operand_index) continue;
    if (decoded_target != NULL && (decoded_target->has_section != target->has_section ||
        decoded_target->section_index != target->section_index || decoded_target->offset != target->offset)) return 1;
    decoded_target = target;
  }
  absolute_operand = candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_EA &&
    candidate->operands[operand_index].ea_mode == 7U && candidate->operands[operand_index].ea_reg <= 1U;
  /* An indirect operand's runtime reference can identify its table/base, not
   * the eventual branch destination. Do not promote it into a direct edge. */
  if (decoded_target == NULL && !absolute_operand) return 1;
  for (index = 0U; index < section_analysis->runtime_address_ref_count; ++index) {
    const M68kRuntimeAddressRefIR *ref = &section_analysis->runtime_address_refs[index];
    if (ref->offset != candidate->offset) continue;
    if (ref->operand_index == UINT32_MAX) {
      ambiguous = 1;
      continue;
    }
    if (ref->operand_index != operand_index) continue;
    if (!ref->has_target) {
      ambiguous = 1;
      continue;
    }
    if (have_ref && (resolved_section != ref->target_section_index || resolved_offset != ref->target_offset))
      ambiguous = 1;
    resolved_section = ref->target_section_index;
    resolved_offset = ref->target_offset;
    have_ref = 1;
  }
  if (ambiguous) return 1;
  if (have_ref) {
    /* Cross-section edges need an explicit section identity in the CFG schema;
     * until then retain an unresolved transfer, never a same-offset alias. */
    if (resolved_section == section->section_index && resolved_offset < render_section_extent(section))
      *out_offset = resolved_offset;
    return 1;
  }
  relocation = analysis_operand_relocation_ref(lookup, section->section_index, candidate, operand_index);
  if (relocation != NULL) {
    if (relocation->target_section_index == section->section_index &&
        relocation->target_offset < render_section_extent(section)) *out_offset = relocation->target_offset;
    return 1;
  }
  if (absolute_operand) {
    int identity_view = 0;
    /* Numeric in-bounds is not an address-domain proof. Only a policy view
     * explicitly identifying these source coordinates with runtime addresses
     * permits the legacy local-offset absolute form without a reference fact.
     * Competing/copy views remain unresolved rather than guessing a phase. */
    if (decoded_target == NULL) return 1;
    for (index = 0U; index < section_analysis->runtime_view_count; ++index) {
      const M68kRuntimeViewIR *view = &section_analysis->runtime_views[index];
      if (view->kind != M68K_FACT_RUNTIME_RANGE_KIND_POLICY || view->runtime_address != view->storage_offset)
        return 1;
      if (candidate->offset >= view->storage_offset && candidate->offset - view->storage_offset < view->size &&
          decoded_target->offset >= view->storage_offset && decoded_target->offset - view->storage_offset < view->size)
        identity_view = 1;
    }
    if (!identity_view) return 1;
  }
  if (decoded_target != NULL && decoded_target->has_section &&
      decoded_target->section_index == section->section_index) *out_offset = decoded_target->offset;
  return 1;
}

static int analysis_cfg_append_edge(M68kSectionAnalysisIR *section_analysis, size_t source_block_index,
    uint32_t source_offset, uint32_t target_offset, uint8_t kind) {
  M68kCfgEdgeIR edge;
  memset(&edge, 0, sizeof(edge));
  edge.source_block_index = source_block_index;
  edge.target_block_index = SIZE_MAX;
  edge.source_offset = source_offset;
  edge.target_offset = target_offset;
  edge.kind = kind;
  return m68k_ir_section_analysis_append_edge(section_analysis, &edge);
}

static size_t analysis_cfg_block_index_for_offset(const M68kSectionAnalysisIR *section_analysis,
    uint32_t target_offset) {
  size_t lo = 0U;
  size_t hi;
  if (section_analysis == NULL) return SIZE_MAX;
  hi = section_analysis->block_count;
  while (lo < hi) {
    size_t mid = lo + ((hi - lo) / 2U);
    uint32_t block_offset = section_analysis->blocks[mid].start_offset;
    if (block_offset == target_offset) return mid;
    if (block_offset < target_offset) {
      lo = mid + 1U;
    } else {
      hi = mid;
    }
  }
  return SIZE_MAX;
}

/* Code discovery records the source instruction for each traced indirect
 * destination. Consume those canonical source coordinates, never the address
 * of a pointer table or a representative recovered-site target. The facts do
 * not assert completeness across callers or mutable stores, so the caller
 * retains the unresolved edge alongside these known destinations. */
static int analysis_cfg_append_indirect_destinations(M68kSectionAnalysisIR *section_analysis,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *candidate, uint8_t kind) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  uint32_t source_offset = candidate->offset;
  size_t operand_index;
  size_t index;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata == NULL || (metadata->flow_kind != M68K_SIM_FLOW_CALL &&
      metadata->flow_kind != M68K_SIM_FLOW_JUMP)) return 0;
  operand_index = metadata->target_operand_index;
  if (operand_index >= candidate->operand_count || operand_index >= M68K_DECODE_IR_MAX_OPERANDS ||
      candidate->operand_kinds[operand_index] != M68K_ASM_OPERAND_EA ||
      (candidate->operands[operand_index].ea_mode == 7U &&
       candidate->operands[operand_index].ea_reg <= 1U)) return 0;
  for (index = 0U; index < section_analysis->code_start_ref_count; ++index) {
    const M68kCodeStartRefIR *ref = &section_analysis->code_start_refs[index];
    size_t edge_index;
    int duplicate = 0;
    if (ref->reason != M68K_FACT_CODE_START_REASON_CONTROL_TARGET ||
        ref->source_section_index != section->section_index || ref->source_offset != source_offset ||
        !accepted_start_at(section, accepted_start, ref->offset)) continue;
    for (edge_index = section_analysis->edge_count; edge_index > 0U; ) {
      const M68kCfgEdgeIR *edge = &section_analysis->edges[--edge_index];
      if (edge->source_offset != source_offset) break;
      if (edge->kind == kind && edge->target_offset == ref->offset) { duplicate = 1; break; }
    }
    if (!duplicate && analysis_cfg_append_edge(section_analysis, section_analysis->block_count,
        source_offset, ref->offset, kind) != 0) return -1;
  }
  return 0;
}

static int analysis_cfg_resolve_edge_targets(M68kSectionAnalysisIR *section_analysis) {
  size_t edge_index;
  if (section_analysis == NULL) return -1;
  for (edge_index = 0U; edge_index < section_analysis->edge_count; ++edge_index) {
    M68kCfgEdgeIR *edge = &section_analysis->edges[edge_index];
    edge->target_block_index = SIZE_MAX;
    if (edge->target_offset == UINT32_MAX) continue;
    edge->target_block_index = analysis_cfg_block_index_for_offset(section_analysis, edge->target_offset);
  }
  return 0;
}

static int analysis_cfg_lookup_block_start_at(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  return lookup != NULL && section_index < lookup->section_count && lookup->block_starts != NULL &&
    lookup->block_start_extents != NULL && lookup->block_starts[section_index] != NULL &&
    offset < lookup->block_start_extents[section_index] && lookup->block_starts[section_index][offset] != 0U;
}

static uint32_t analysis_platform_opcode_size_at(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t offset) {
  PlatformFactsV2ResolvedCall call_info;
  uint16_t opcode;
  if (lookup == NULL || lookup->object == NULL || section == NULL || section->data == NULL ||
      offset + 2U > section->size) {
    return 0U;
  }
  opcode = m68k_read_u16be(section->data + offset);
  return platform_facts_v2_resolve_opcode_call(lookup->object->platform_backend_kind, opcode, &call_info) ? 2U : 0U;
}

static int analysis_cfg_build_block_start_map(const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const uint8_t *accepted_bytes,
    const M68kSectionAnalysisIR *section_analysis, uint8_t *block_starts, uint32_t render_extent) {
  uint32_t offset = 0U;
  size_t code_start_index;
  if (section == NULL || accepted_start == NULL || accepted_bytes == NULL || block_starts == NULL) return -1;
  /* Policy and manually established entry points are executable boundaries even
   * when they immediately follow a terminal instruction.  CFG construction
   * must consume the same code-start facts exported by source analysis. */
  if (section_analysis != NULL) {
    for (code_start_index = 0U; code_start_index < section_analysis->code_start_ref_count;
         ++code_start_index) {
      const M68kCodeStartRefIR *code_start = &section_analysis->code_start_refs[code_start_index];
      if (code_start->offset < render_extent && accepted_start_at(section, accepted_start, code_start->offset))
        block_starts[code_start->offset] = 1U;
    }
  }
  while (offset < render_extent) {
    const M68kDecodeCandidate *candidate;
    uint32_t next_offset;
    uint32_t target_offset;
    uint8_t edge_kind;
    int has_control_target;
    if (!accepted_start_at(section, accepted_start, offset)) {
      ++offset;
      continue;
    }
    candidate = find_candidate_at_offset_local(section, offset);
    if (candidate == NULL || candidate->byte_count == 0U || candidate->byte_count > render_extent - offset) {
      uint32_t platform_opcode_size = analysis_platform_opcode_size_at(lookup, section, offset);
      if (platform_opcode_size == 0U || platform_opcode_size > render_extent - offset) return -1;
      if (offset == 0U || !analysis_accepted_byte_at(section, accepted_bytes, offset - 1U) ||
          analysis_cfg_lookup_block_start_at(lookup, section->section_index, offset)) {
        block_starts[offset] = 1U;
      }
      offset += platform_opcode_size;
      continue;
    }
    if (offset == 0U || !analysis_accepted_byte_at(section, accepted_bytes, offset - 1U) ||
        analysis_cfg_lookup_block_start_at(lookup, section->section_index, offset)) {
      block_starts[offset] = 1U;
    }
    next_offset = offset + candidate->byte_count;
    has_control_target = analysis_cfg_control_target(lookup, section, section_analysis, candidate,
      &edge_kind, &target_offset);
    if (has_control_target && target_offset < render_extent &&
        accepted_start_at(section, accepted_start, target_offset)) block_starts[target_offset] = 1U;
    if (has_control_target && render_cfg_candidate_has_fallthrough(candidate) &&
        next_offset < render_extent && accepted_start_at(section, accepted_start, next_offset)) {
      block_starts[next_offset] = 1U;
    }
    offset = next_offset;
  }
  return 0;
}

int m68k_analysis_render_lookup_append_cfg_for_section(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const uint8_t *accepted_bytes,
    Arena *scratch_arena, M68kSectionAnalysisIR *section_analysis) {
  ArenaMark scratch_mark;
  uint32_t render_extent;
  uint8_t *block_starts = NULL;
  uint32_t offset = 0U;
  int result = -1;
  if (section == NULL || scratch_arena == NULL || section_analysis == NULL) return -1;
  render_extent = render_section_extent(section);
  if (render_extent == 0U) return 0;
  scratch_mark = arena_mark(scratch_arena);
  block_starts = (uint8_t *)arena_calloc(scratch_arena, render_extent, sizeof(*block_starts));
  if (block_starts == NULL) return -1;
  if (analysis_cfg_build_block_start_map(lookup, section, accepted_start, accepted_bytes, section_analysis,
      block_starts, render_extent) != 0) {
    goto cleanup;
  }
  while (offset < render_extent) {
    M68kCfgBlockIR block;
    uint32_t cursor;
    if (!accepted_start_at(section, accepted_start, offset) || block_starts[offset] == 0U) {
      ++offset;
      continue;
    }
    memset(&block, 0, sizeof(block));
    block.start_offset = offset;
    block.certainty = M68K_CODE_CERTAIN;
    block.edge_start = section_analysis->edge_count;
    cursor = offset;
    while (cursor < render_extent && accepted_start_at(section, accepted_start, cursor)) {
      const M68kDecodeCandidate *candidate = find_candidate_at_offset_local(section, cursor);
      uint32_t next_offset;
      uint32_t target_offset;
      uint8_t edge_kind;
      int has_control_target;
      int has_fallthrough;
      if (candidate == NULL || candidate->byte_count == 0U || candidate->byte_count > render_extent - cursor) {
        uint32_t platform_opcode_size = analysis_platform_opcode_size_at(lookup, section, cursor);
        if (platform_opcode_size == 0U || platform_opcode_size > render_extent - cursor) goto cleanup;
        cursor += platform_opcode_size;
        continue;
      }
      next_offset = cursor + candidate->byte_count;
      has_control_target = analysis_cfg_control_target(lookup, section, section_analysis, candidate,
        &edge_kind, &target_offset);
      has_fallthrough = render_cfg_candidate_has_fallthrough(candidate);
      if (has_control_target && analysis_cfg_append_edge(section_analysis, section_analysis->block_count,
          cursor, target_offset, edge_kind) != 0) goto cleanup;
      if (has_control_target && target_offset == UINT32_MAX &&
          analysis_cfg_append_indirect_destinations(section_analysis, section, accepted_start,
            candidate, edge_kind) != 0) goto cleanup;
      if (has_control_target) {
        if (has_fallthrough && next_offset < render_extent && accepted_start_at(section, accepted_start, next_offset) &&
            analysis_cfg_append_edge(section_analysis, section_analysis->block_count, cursor, next_offset,
              M68K_CFG_EDGE_FALLTHROUGH) != 0) {
          goto cleanup;
        }
        cursor = next_offset;
        break;
      }
      if (!has_fallthrough) {
        if (analysis_cfg_append_edge(section_analysis, section_analysis->block_count, cursor, UINT32_MAX,
            M68K_CFG_EDGE_RETURN) != 0) {
          goto cleanup;
        }
        cursor = next_offset;
        break;
      }
      if (next_offset >= render_extent || !accepted_start_at(section, accepted_start, next_offset) ||
          block_starts[next_offset] != 0U) {
        if (next_offset < render_extent && accepted_start_at(section, accepted_start, next_offset) &&
            analysis_cfg_append_edge(section_analysis, section_analysis->block_count, cursor, next_offset,
              M68K_CFG_EDGE_FALLTHROUGH) != 0) {
          goto cleanup;
        }
        cursor = next_offset;
        break;
      }
      cursor = next_offset;
    }
    block.end_offset = cursor;
    block.edge_count = section_analysis->edge_count - block.edge_start;
    if (m68k_ir_section_analysis_append_block(section_analysis, &block) != 0) goto cleanup;
    offset = cursor > offset ? cursor : offset + 1U;
  }
  if (analysis_cfg_resolve_edge_targets(section_analysis) != 0) goto cleanup;
  result = 0;

cleanup:
  arena_rewind(scratch_arena, scratch_mark);
  return result;
}

int lookup_structured_long_table_targets_offset(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset) {
  return (render_lookup_boundary_flags(lookup, section_index, offset) &
    M68K_RENDER_BOUNDARY_LONG_TABLE_TARGET) != 0U;
}

static int lookup_inferred_runtime_data_class_value(const M68kRenderLookup *lookup, uint32_t runtime_address) {
  size_t index;
  if (lookup == NULL || runtime_address == 0U) return 0;
  for (index = 0U; index < lookup->inferred_runtime_address_ref_count; ++index) {
    const M68kRenderInferredRuntimeAddressRef *entry = &lookup->inferred_runtime_address_refs[index];
    if (entry->ref.has_runtime_address && entry->ref.runtime_address == runtime_address &&
        entry->data_class_flags != 0U) {
      return 1;
    }
  }
  return 0;
}

int lookup_label_statement_ref_is_semantic_runtime_data(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset) {
  uint32_t runtime_address = 0U;
  if (lookup == NULL) return 0;
  if (lookup_source_runtime_address(lookup, section_index, offset, &runtime_address) &&
      lookup_inferred_runtime_data_class_value(lookup, runtime_address)) {
    return 1;
  }
  return lookup_inferred_runtime_data_class_value(lookup, offset);
}

static int lookup_label_has_target_ref(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->label_target_refs == NULL ||
      lookup->label_target_ref_extents == NULL || offset > lookup->label_target_ref_extents[section_index] ||
      lookup->label_target_refs[section_index] == NULL) {
    return 0;
  }
  return lookup->label_target_refs[section_index][offset] != 0U;
}

static int lookup_policy_has_custom_struct_named(const M68kRenderLookup *lookup, const char *struct_name) {
  uint16_t index;
  if (lookup == NULL || lookup->policy == NULL || lookup->policy->custom_structs == NULL ||
      struct_name == NULL || struct_name[0] == '\0') {
    return 0;
  }
  for (index = 0U; index < lookup->policy->custom_struct_count && index < M68K_ANALYSIS_CUSTOM_STRUCT_LIMIT;
       ++index) {
    if (strcmp(lookup->policy->custom_structs[index].name, struct_name) == 0) return 1;
  }
  return 0;
}

static int lookup_structured_item_has_generated_custom_field_label(const M68kAnalysisStructuredDataItem *item) {
  const char *field;
  const char *digits;
  if (item == NULL || item->label[0] == '\0' || item->field_name[0] == '\0') return 0;
  field = strstr(item->label, item->field_name);
  if (field == NULL || field == item->label || field[-1] != '_') return 0;
  field += strlen(item->field_name);
  if (*field == '\0') return 1;
  if (*field != '_') return 0;
  digits = field + 1;
  if (*digits == '\0') return 0;
  while (*digits >= '0' && *digits <= '9') ++digits;
  return *digits == '\0';
}

static int lookup_policy_structured_item_targets_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  uint16_t index;
  if (lookup == NULL || lookup->policy == NULL) return 0;
  for (index = 0U; index < lookup->policy->structured_data_item_count &&
       index < M68K_ANALYSIS_STRUCTURED_DATA_ITEM_LIMIT; ++index) {
    const M68kAnalysisStructuredDataItem *item = &lookup->policy->structured_data_items[index];
    if (item->has_target != 0U && item->target_section == section_index && item->target_offset == offset) return 1;
  }
  return 0;
}

int lookup_structured_field_has_explicit_label(const M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *item, size_t section_index, uint32_t offset) {
  char name[128];
  uint16_t index;
  if (item == NULL || item->offset != offset || item->field_name[0] == '\0') return 0;
  /* Expanded fields carry an automatic instance_field label. A separately
     named source anchor at that exact field boundary remains a declaration. */
  if (format_lookup_asm_label_with_generation(lookup, name, sizeof(name), section_index, offset) != 0U) return 0;
  if (strcmp(name, item->label) != 0) return 1;
  if (lookup->policy == NULL) return 0;
  for (index = 0U; index < lookup->policy->named_label_count && index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++index) {
    const M68kAnalysisNamedLabel *label = &lookup->policy->named_labels[index];
    if (label->is_source_declaration && label->domain == M68K_ANALYSIS_LABEL_DOMAIN_SOURCE &&
        label->offset == offset &&
        (label->has_section_index ? label->section_index == section_index : section_index == 0U) &&
        strcmp(label->name, name) == 0) return 1;
  }
  return 0;
}

int lookup_should_emit_label_statement(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, size_t section_index, uint32_t offset) {
  const M68kAnalysisStructuredDataItem *item;
  if (!lookup_has_renderable_label(lookup, section_index, offset)) return 0;
  item = lookup_structured_data_item_at_offset(lookup, section_index, offset);
  if (item != NULL && lookup_policy_has_custom_struct_named(lookup, item->struct_name) &&
      lookup_structured_item_has_generated_custom_field_label(item) &&
      !lookup_structured_field_has_explicit_label(lookup, item, section_index, offset) &&
      !lookup_label_has_target_ref(lookup, section_index, offset) &&
      !lookup_label_has_statement_ref(lookup, section_index, offset) &&
      !lookup_policy_structured_item_targets_offset(lookup, section_index, offset)) {
    return 0;
  }
  if (lookup_label_has_explicit_name(lookup, section_index, offset)) return 1;
  if (accepted_start_at(section, accepted_start, offset)) return 1;
  if (lookup_structured_data_item_at_offset(lookup, section_index, offset) != NULL) return 1;
  if (lookup_label_has_statement_ref(lookup, section_index, offset) &&
      lookup_label_has_target_ref(lookup, section_index, offset))
    return 1;
  if (lookup_label_has_statement_ref(lookup, section_index, offset) &&
      !lookup_label_statement_ref_is_semantic_runtime_data(lookup, section_index, offset))
    return 1;
  return 0;
}

static int analysis_append_durable_label_origins(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t offset, M68kSectionAnalysisIR *section_analysis);

int m68k_analysis_render_lookup_append_labels_for_section(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    M68kSectionAnalysisIR *section_analysis) {
  uint32_t offset;
  uint32_t render_extent;
  if (lookup == NULL || section == NULL || section_analysis == NULL) return -1;
  render_extent = render_section_extent(section);
  for (offset = 0U; offset < render_extent; ++offset) {
      if (!lookup_should_emit_label_statement(lookup, section, accepted_start, section->section_index, offset))
        continue;
      if (m68k_ir_section_analysis_add_label(section_analysis, offset) != 0) return -1;
      if (analysis_append_durable_label_origins(lookup, section, offset, section_analysis) != 0) return -1;
    }
    if (lookup_has_renderable_label(lookup, section->section_index, render_extent) &&
        m68k_ir_section_analysis_add_label(section_analysis, render_extent) != 0) {
      return -1;
    }
    if (lookup_has_renderable_label(lookup, section->section_index, render_extent) &&
        analysis_append_durable_label_origins(lookup, section, render_extent, section_analysis) != 0) {
      return -1;
    }
    return 0;
  }

static int analysis_runtime_range_is_materialized(const M68kRenderLookup *lookup, const M68kFact *range) {
  uint8_t materialized = 0U;
  (void)lookup_runtime_range_materialization(lookup, range, &materialized, NULL, NULL);
  return materialized != 0U;
}

static int analysis_lookup_section_has_runtime_range(const M68kRenderLookup *lookup, size_t section_index) {
  size_t index;
  if (lookup == NULL || lookup->runtime_address_ranges == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    if (fact != NULL && fact->section_index == section_index && fact->size != 0U) return 1;
  }
  return 0;
}

static int analysis_lookup_materialized_runtime_address_source_offset(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t runtime_address, uint32_t *out_source_offset) {
  size_t index;
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (lookup == NULL || out_source_offset == NULL || section_index >= lookup->section_count) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *range = lookup->runtime_address_ranges[index].fact;
    uint32_t delta;
    uint32_t source_offset;
    if (!analysis_runtime_range_is_materialized(lookup, range) || range->section_index != section_index ||
        !range->has_runtime_address || runtime_address < range->runtime_address) {
      continue;
    }
    delta = runtime_address - range->runtime_address;
    if (delta >= range->size || range->offset > UINT32_MAX - delta) continue;
    source_offset = range->offset + delta;
    if (lookup->label_extents == NULL || source_offset >= lookup->label_extents[section_index]) continue;
    *out_source_offset = source_offset;
    return 1;
  }
  return 0;
}

static const char *analysis_lookup_policy_label_name(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint8_t domain) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (policy == NULL) return NULL;
  for (index = 0U; index < policy->named_label_count && index < M68K_ANALYSIS_NAMED_LABEL_LIMIT; ++index) {
    const M68kAnalysisNamedLabel *label = &policy->named_labels[index];
    if (label->name[0] == '\0' || label->offset != offset) continue;
    if (label->domain != domain) continue;
    if (label->has_section_index) {
      if (label->section_index != section_index) continue;
    } else if (section_index != 0U) {
      continue;
    }
    return label->name;
  }
  return NULL;
}

static int analysis_lookup_has_policy_label(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  const char *name = analysis_lookup_policy_label_name(lookup, section_index, offset,
    M68K_ANALYSIS_LABEL_DOMAIN_SOURCE);
  return name != NULL && name[0] != '\0';
}

static const char *analysis_lookup_object_symbol_label_name(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset) {
  size_t index;
  const M68kObject *object = lookup != NULL ? lookup->object : NULL;
  if (lookup != NULL && section_index < lookup->section_count && lookup->object_symbol_labels != NULL &&
      lookup->object_symbol_label_extents != NULL && offset <= lookup->object_symbol_label_extents[section_index] &&
      lookup->object_symbol_labels[section_index] != NULL) {
    return lookup->object_symbol_labels[section_index][offset];
  }
  if (object == NULL) return NULL;
  for (index = 0U; index < object->symbol_count; ++index) {
    const M68kSymbol *symbol = &object->symbols[index];
    if (!symbol->defined || symbol->section_index != section_index || symbol->value != offset) continue;
    if (!asm_symbol_name_is_safe_local(symbol->name)) continue;
    return symbol->name;
  }
  return NULL;
}

static int analysis_append_durable_label_origins(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t offset, M68kSectionAnalysisIR *section_analysis) {
  M68kSymbolOriginIR origin;
  const char *name;
  if (lookup == NULL || section == NULL || section_analysis == NULL) return -1;
  name = analysis_lookup_policy_label_name(lookup, section->section_index, offset,
    M68K_ANALYSIS_LABEL_DOMAIN_SOURCE);
  if (name != NULL && name[0] != '\0') {
    memset(&origin, 0, sizeof(origin));
    origin.symbol_name = (char *)name;
    origin.offset = offset;
    origin.source_section_index = (uint32_t)section->section_index;
    origin.source_offset = offset;
    origin.origin_kind = M68K_SYMBOL_ORIGIN_MANUAL_LABEL;
    origin.confidence = M68K_FACT_CONFIDENCE_REQUIRED;
    if (m68k_ir_section_analysis_append_symbol_origin(section_analysis, &origin) != 0) return -1;
  }
  name = analysis_lookup_object_symbol_label_name(lookup, section->section_index, offset);
  if (name == NULL || name[0] == '\0') return 0;
  memset(&origin, 0, sizeof(origin));
  origin.symbol_name = (char *)name;
  origin.offset = offset;
  origin.source_section_index = (uint32_t)section->section_index;
  origin.source_offset = offset;
  origin.origin_kind = M68K_SYMBOL_ORIGIN_OBJECT_SYMBOL;
  origin.confidence = M68K_FACT_CONFIDENCE_REQUIRED;
  return m68k_ir_section_analysis_append_symbol_origin(section_analysis, &origin);
}

static uint8_t analysis_orphan_missing_inbound_for_renderable_label(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset) {
  if (analysis_lookup_has_policy_label(lookup, section_index, offset))
    return M68K_ORPHAN_CODE_SIGNAL_INBOUND_POLICY_SEED;
  if (analysis_lookup_object_symbol_label_name(lookup, section_index, offset) != NULL)
    return M68K_ORPHAN_CODE_SIGNAL_INBOUND_METADATA;
  return M68K_ORPHAN_CODE_SIGNAL_INBOUND_UNKNOWN;
}

static int analysis_orphan_candidate_range_is_blocked(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset, uint32_t size,
    int allow_structured_data_overlap) {
  uint32_t cursor;
  if (section == NULL || size == 0U || size > section->size - offset) return 1;
  for (cursor = offset; cursor < offset + size; ++cursor) {
    if (analysis_accepted_byte_at(section, accepted_bytes, cursor)) return 1;
    if (!allow_structured_data_overlap) {
      M68kRenderRangeOwnershipView range;
      if (lookup_range_ownership_covering_offset(lookup, section->section_index, cursor, &range)) return 1;
    }
  }
  return 0;
}

static uint8_t analysis_orphan_cpu_ceiling(uint8_t max_cpu) {
  return max_cpu <= M68K_ASM_CPU_68060 ? max_cpu : M68K_ASM_CPU_68060;
}

static M68kDisasmResult analysis_orphan_disassemble_for_cpu_ceiling(const uint8_t *data, size_t size,
    uint8_t max_cpu) {
  M68kDisasmResult decoded;
  uint8_t cpu;
  memset(&decoded, 0, sizeof(decoded));
  for (cpu = M68K_ASM_CPU_68000; cpu <= analysis_orphan_cpu_ceiling(max_cpu); ++cpu) {
    decoded = m68k_disassemble_one_for_cpu(data, size, cpu, m68k_diag_sink(NULL));
    if (decoded.byte_count != 0U) return decoded;
    if (cpu == M68K_ASM_CPU_68060) break;
  }
  return decoded;
}

static const M68kDecodeCandidate *analysis_orphan_decode_candidate_at_offset(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t offset, M68kDecodeCandidate *decoded_candidate) {
  const M68kDecodeCandidate *candidate;
  M68kDisasmResult decoded;
  uint8_t max_cpu = M68K_ASM_CPU_68000;
  size_t operand_index;
  if (section == NULL || decoded_candidate == NULL) return NULL;
  candidate = find_candidate_at_offset_local(section, offset);
  if (candidate != NULL) return candidate;
  if (section->data == NULL || offset >= section->size) return NULL;
  if (lookup != NULL && lookup->policy != NULL && lookup->policy->max_cpu != 0U)
    max_cpu = lookup->policy->max_cpu;
  decoded = analysis_orphan_disassemble_for_cpu_ceiling(section->data + offset, section->size - offset, max_cpu);
  if (decoded.byte_count == 0U || decoded.byte_count > UINT8_MAX) return NULL;
  memset(decoded_candidate, 0, sizeof(*decoded_candidate));
  decoded_candidate->offset = offset;
  decoded_candidate->asm_form_index = decoded.asm_form_index;
  decoded_candidate->disasm_form_index = decoded.disasm_form_index;
  decoded_candidate->mnemonic_id = decoded.mnemonic_id;
  decoded_candidate->target_cpu = decoded.target_cpu;
  decoded_candidate->has_coprocessor_id = decoded.has_coprocessor_id;
  decoded_candidate->coprocessor_id = decoded.coprocessor_id;
  decoded_candidate->byte_count = (uint8_t)decoded.byte_count;
  decoded_candidate->size_suffix = decoded.size_suffix;
  decoded_candidate->operand_count = (uint8_t)(decoded.operand_count > M68K_DECODE_IR_MAX_OPERANDS
    ? M68K_DECODE_IR_MAX_OPERANDS : decoded.operand_count);
  for (operand_index = 0U; operand_index < decoded.operand_count &&
       operand_index < M68K_DECODE_IR_MAX_OPERANDS; ++operand_index) {
    decoded_candidate->operand_kinds[operand_index] = decoded.operand_kinds[operand_index];
    decoded_candidate->operands[operand_index] = decoded.operands[operand_index];
  }
  return decoded_candidate;
}

static int analysis_absolute_ref_access_kind(uint8_t access_kind) {
  return access_kind == M68K_SIM_ACCESS_MEMORY_READ ||
    access_kind == M68K_SIM_ACCESS_MEMORY_WRITE ||
    access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS ||
    access_kind == M68K_SIM_ACCESS_BRANCH_TARGET;
}

static uint32_t analysis_instruction_access_width(const M68kInstructionIR *instruction, uint8_t access_kind) {
  if (instruction == NULL || access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS ||
      access_kind == M68K_SIM_ACCESS_BRANCH_TARGET) {
    return 0U;
  }
  if (instruction->size_suffix == 'b') return 1U;
  if (instruction->size_suffix == 'w') return 2U;
  if (instruction->size_suffix == 'l') return 4U;
  return 0U;
}

static const M68kFact *analysis_operand_relocation_ref(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, size_t operand_index) {
  M68kAsmOperandValue operands[M68K_DECODE_IR_MAX_OPERANDS];
  size_t index;
  size_t begin;
  size_t end;
  uint32_t cursor;
  if (lookup == NULL || candidate == NULL || operand_index >= candidate->operand_count ||
      candidate->operand_count > M68K_DECODE_IR_MAX_OPERANDS) {
    return NULL;
  }
  for (index = 0U; index < candidate->operand_count; ++index) {
    operands[index] = candidate->operands[index];
    operands[index].kind = candidate->operand_kinds[index];
  }
  begin = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, operands, candidate->operand_count,
    candidate->size_suffix, operand_index, 0);
  end = m68k_asm_operand_relative_base_offset(candidate->asm_form_index, operands, candidate->operand_count,
    candidate->size_suffix, operand_index, 1);
  if (begin > end || begin > UINT32_MAX - candidate->offset || end > UINT32_MAX - candidate->offset) return NULL;
  for (cursor = candidate->offset + (uint32_t)begin; cursor < candidate->offset + (uint32_t)end; ++cursor) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, cursor);
    if (relocation != NULL) return relocation;
  }
  return NULL;
}

static void analysis_classify_orphan_absolute_operand_observation(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint8_t platform_kind, uint32_t address,
    M68kAddressObservationIR *observation) {
  uint8_t platform_owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_UNKNOWN;
  uint32_t platform_owner_offset = 0U;
  uint32_t source_offset = 0U;
  if (observation == NULL) return;
  observation->owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_ABSOLUTE_MEMORY;
  observation->owner_offset = address;
  if (platform_facts_v2_absolute_memory_owner(platform_kind, address, &platform_owner_kind,
      &platform_owner_offset)) {
    observation->owner_kind = platform_owner_kind;
    observation->owner_offset = platform_owner_offset;
    return;
  }
  if (m68k_cpu_find_exception_vector_by_address(address) != NULL ||
      platform_facts_v2_is_callback_vector_slot(platform_kind, address)) {
    observation->owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_CPU_VECTOR;
    observation->owner_offset = 0U;
    return;
  }
  if (section != NULL &&
      analysis_lookup_materialized_runtime_address_source_offset(lookup, section->section_index, address,
        &source_offset)) {
    observation->owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_RUNTIME_RANGE;
    observation->owner_offset = source_offset;
    return;
  }
  if (section != NULL && !analysis_lookup_section_has_runtime_range(lookup, section->section_index) &&
      address < section->size) {
    observation->owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_SECTION_STORAGE;
    observation->owner_offset = address;
  }
}

static int analysis_append_orphan_absolute_operand_observations_for_signal(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kOrphanCodeSignalIR *signal,
    M68kSectionAnalysisIR *section_analysis) {
  uint32_t cursor;
  uint8_t platform_kind = M68K_PLATFORM_BACKEND_UNKNOWN;
  if (section == NULL || signal == NULL || section_analysis == NULL || signal->size == 0U ||
      signal->offset > section->size || signal->size > section->size - signal->offset) {
    return -1;
  }
  if (lookup != NULL && lookup->object != NULL) platform_kind = lookup->object->platform_backend_kind;
  cursor = signal->offset;
  while (cursor < signal->offset + signal->size) {
    M68kDecodeCandidate decoded_candidate;
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    size_t operand_index;
    candidate = analysis_orphan_decode_candidate_at_offset(lookup, section, cursor, &decoded_candidate);
    if (candidate == NULL || candidate->byte_count == 0U ||
        candidate->byte_count > signal->offset + signal->size - cursor) {
      return -1;
    }
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return -1;
    metadata = m68k_sim_metadata_for_instruction(&instruction);
    if (metadata == NULL) return -1;
    for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U &&
         operand_index < instruction.operand_count; ++operand_index) {
      uint32_t address = 0U;
      uint8_t access_kind = metadata->operand_access_kinds[operand_index];
      const M68kFact *relocation;
      M68kAddressObservationIR observation;
      if (!analysis_absolute_ref_access_kind(access_kind)) continue;
      if (!m68k_asm_operand_absolute_value(candidate->operand_kinds[operand_index],
          &candidate->operands[operand_index], &address)) {
        continue;
      }
      memset(&observation, 0, sizeof(observation));
      observation.offset = candidate->offset;
      observation.operand_index = (uint32_t)operand_index;
      observation.raw_value = address;
      observation.address = address;
      observation.access_width = analysis_instruction_access_width(&instruction, access_kind);
      observation.access_kind = access_kind;
      observation.source = M68K_ADDRESS_OBSERVATION_SOURCE_ABSOLUTE_OPERAND;
      observation.has_address = 1U;
      observation.confidence = signal->confidence;
      observation.conflict_state = M68K_ANALYSIS_CONFLICT_STATE_UNRESOLVED;
      relocation = analysis_operand_relocation_ref(lookup, section->section_index, candidate, operand_index);
      if (relocation != NULL) {
        observation.owner_kind = M68K_ABSOLUTE_MEMORY_OWNER_SECTION_STORAGE;
        observation.owner_offset = relocation->target_offset;
        observation.target_section_index = relocation->target_section_index > UINT32_MAX ? UINT32_MAX :
          (uint32_t)relocation->target_section_index;
        observation.target_offset = relocation->target_offset;
        observation.has_target = 1U;
      } else {
        analysis_classify_orphan_absolute_operand_observation(lookup, section, platform_kind, address,
          &observation);
      }
      if (m68k_ir_section_analysis_append_address_observation(section_analysis, &observation) != 0) return -1;
    }
    cursor += candidate->byte_count;
  }
  return 0;
}

static int analysis_orphan_signal_has_vector_evidence(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kOrphanCodeSignalIR *signal) {
  uint32_t cursor;
  uint8_t platform_kind = M68K_PLATFORM_BACKEND_UNKNOWN;
  if (section == NULL || signal == NULL || signal->size == 0U ||
      signal->offset > section->size || signal->size > section->size - signal->offset) {
    return 0;
  }
  if (lookup != NULL && lookup->object != NULL) platform_kind = lookup->object->platform_backend_kind;
  cursor = signal->offset;
  while (cursor < signal->offset + signal->size) {
    M68kDecodeCandidate decoded_candidate;
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    size_t operand_index;
    candidate = analysis_orphan_decode_candidate_at_offset(lookup, section, cursor, &decoded_candidate);
    if (candidate == NULL || candidate->byte_count == 0U ||
        candidate->byte_count > signal->offset + signal->size - cursor) {
      return 0;
    }
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
    metadata = m68k_sim_metadata_for_instruction(&instruction);
    if (metadata == NULL) return 0;
    for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < 4U; ++operand_index) {
      uint32_t address = 0U;
      uint8_t access_kind = metadata->operand_access_kinds[operand_index];
      if (!analysis_absolute_ref_access_kind(access_kind)) continue;
      if (!m68k_asm_operand_absolute_value(candidate->operand_kinds[operand_index],
          &candidate->operands[operand_index], &address)) {
        continue;
      }
      if (analysis_operand_relocation_ref(lookup, section->section_index, candidate, operand_index) != NULL)
        continue;
      if (m68k_cpu_find_exception_vector_by_address(address) != NULL ||
          platform_facts_v2_is_callback_vector_slot(platform_kind, address)) {
        return 1;
      }
    }
    cursor += candidate->byte_count;
  }
  return 0;
}

static int analysis_orphan_lvo_matches_amiga_api(int16_t lvo) {
  size_t index;
  for (index = 0U;; ++index) {
    const AmigaOsLibraryVectorInfo *vector = amiga_os_library_vector_at(index);
    if (vector == NULL) return 0;
    if (vector->lvo == lvo) return 1;
  }
}

static int analysis_orphan_signal_has_api_evidence(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kOrphanCodeSignalIR *signal) {
  uint32_t cursor;
  if (lookup == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
      section == NULL || signal == NULL || signal->size == 0U ||
      signal->offset > section->size || signal->size > section->size - signal->offset) {
    return 0;
  }
  cursor = signal->offset;
  while (cursor < signal->offset + signal->size) {
    M68kDecodeCandidate decoded_candidate;
    const M68kDecodeCandidate *candidate;
    int16_t lvo = 0;
    candidate = analysis_orphan_decode_candidate_at_offset(lookup, section, cursor, &decoded_candidate);
    if (candidate == NULL || candidate->byte_count == 0U ||
        candidate->byte_count > signal->offset + signal->size - cursor) {
      return 0;
    }
    if (candidate_calls_a6_lvo(candidate, &lvo) && analysis_orphan_lvo_matches_amiga_api(lvo)) return 1;
    cursor += candidate->byte_count;
  }
  return 0;
}

static void analysis_orphan_signal_attach_nearby_data_context(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, M68kOrphanCodeSignalIR *signal) {
  const M68kAnalysisStructuredDataItem *item = NULL;
  uint32_t role_flags = 0U;
  if (lookup == NULL || section == NULL || signal == NULL) return;
  item = lookup_structured_data_item_covering_offset(lookup, section->section_index, signal->offset);
  role_flags = item != NULL ? item->semantic_role_flags : 0U;
  if (role_flags != 0U) {
    signal->nearby_data_flags = role_flags;
    signal->nearby_data_table_kind_id = item->table_kind_id;
    signal->nearby_data_offset = item->offset;
    signal->nearby_data_distance = 0U;
    signal->nearby_data_relation = M68K_ORPHAN_CODE_SIGNAL_NEARBY_DATA_OVERLAP;
    return;
  }
  if (signal->size <= section->size - signal->offset) {
    uint32_t after_offset = signal->offset + signal->size;
    if (after_offset < section->size)
      item = lookup_structured_data_item_at_offset(lookup, section->section_index, after_offset);
    if (item != NULL) {
      role_flags = item != NULL ? item->semantic_role_flags : 0U;
      if (role_flags != 0U) {
        signal->nearby_data_flags = role_flags;
        signal->nearby_data_table_kind_id = item->table_kind_id;
        signal->nearby_data_offset = item->offset;
        signal->nearby_data_distance = item->offset > after_offset ? item->offset - after_offset : 0U;
        signal->nearby_data_relation = M68K_ORPHAN_CODE_SIGNAL_NEARBY_DATA_AFTER;
        return;
      }
    }
  }
  if (signal->offset > 0U) {
    item = lookup_structured_data_item_covering_offset(lookup, section->section_index, signal->offset - 1U);
    role_flags = item != NULL ? item->semantic_role_flags : 0U;
    if (role_flags != 0U) {
      signal->nearby_data_flags = role_flags;
      signal->nearby_data_table_kind_id = item->table_kind_id;
      signal->nearby_data_offset = item->offset;
      signal->nearby_data_distance = signal->offset > item->offset &&
        signal->offset - item->offset > item->size
        ? signal->offset - item->offset - item->size
        : 0U;
      signal->nearby_data_relation = M68K_ORPHAN_CODE_SIGNAL_NEARBY_DATA_BEFORE;
    }
  }
}

static void analysis_orphan_signal_refine_missing_inbound(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, M68kOrphanCodeSignalIR *signal) {
  if (signal == NULL) return;
  if (signal->missing_inbound != M68K_ORPHAN_CODE_SIGNAL_INBOUND_UNKNOWN &&
      signal->missing_inbound != M68K_ORPHAN_CODE_SIGNAL_INBOUND_METADATA)
    return;
  if (analysis_orphan_signal_has_vector_evidence(lookup, section, signal)) {
    signal->missing_inbound = M68K_ORPHAN_CODE_SIGNAL_INBOUND_VECTOR;
  } else if (analysis_orphan_signal_has_api_evidence(lookup, section, signal)) {
    signal->missing_inbound = M68K_ORPHAN_CODE_SIGNAL_INBOUND_API;
  } else if ((signal->nearby_data_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE) != 0U &&
      (signal->nearby_data_table_kind_id == M68K_ANALYSIS_TABLE_KIND_RELATIVE_CODE_DISPATCH ||
       signal->nearby_data_table_kind_id == M68K_ANALYSIS_TABLE_KIND_ABSOLUTE_CODE_DISPATCH)) {
    signal->missing_inbound = M68K_ORPHAN_CODE_SIGNAL_INBOUND_JUMP_TABLE;
  }
}

static void analysis_orphan_signal_set_arbitration_flags(M68kOrphanCodeSignalIR *signal,
    int suppressed_by_structured_data) {
  if (signal == NULL) return;
  if (signal->reason == M68K_ORPHAN_CODE_SIGNAL_TERMINAL_DECODE) {
    signal->arbitration_flags |= M68K_ORPHAN_CODE_SIGNAL_ARBITRATION_REPORT_ONLY_CODE_SHAPE;
  }
  if (suppressed_by_structured_data) {
    signal->arbitration_flags |= M68K_ORPHAN_CODE_SIGNAL_ARBITRATION_SUPPRESSED_BY_STRUCTURED_DATA;
  }
  if (signal->reason == M68K_ORPHAN_CODE_SIGNAL_TERMINAL_DECODE &&
      signal->missing_inbound == M68K_ORPHAN_CODE_SIGNAL_INBOUND_UNKNOWN) {
    signal->arbitration_flags |= M68K_ORPHAN_CODE_SIGNAL_ARBITRATION_NEGATIVE_WEAK_TEXT_EVIDENCE;
  }
}

static int analysis_orphan_start_has_non_control_runtime_address_ref(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t offset) {
  size_t index;
  int saw_ref = 0;
  if (lookup == NULL || section == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_ref_count; ++index) {
    const M68kFact *ref = lookup->runtime_address_refs[index].fact;
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    const M68kDecodeCandidate *candidate;
    size_t operand_index;
    if (ref == NULL || ref->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
        ref->target_section_index != section->section_index || ref->target_offset != offset ||
        ref->section_index != section->section_index) {
      continue;
    }
    if (ref->reason == UINT32_MAX) continue;
    operand_index = (size_t)ref->reason;
    candidate = find_candidate_at_offset_local(section, ref->offset);
    if (candidate == NULL || operand_index >= candidate->operand_count) continue;
    metadata = analysis_cfg_candidate_metadata(candidate, &instruction);
    if (metadata == NULL || operand_index >= instruction.operand_count) continue;
    saw_ref = 1;
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_BRANCH_TARGET &&
        metadata->operand_result_kinds[operand_index] == M68K_SIM_RESULT_CONTROL_TARGET) {
      return 0;
    }
  }
  return saw_ref;
}

int m68k_analysis_render_lookup_append_orphan_code_signals_for_section(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const uint8_t *accepted_bytes,
    M68kSectionAnalysisIR *section_analysis) {
  uint32_t render_extent;
  uint32_t offset = 0U;
  if (section == NULL || section_analysis == NULL || accepted_start == NULL || accepted_bytes == NULL) return -1;
  if (section->kind != M68K_SECTION_CODE) return 0;
  render_extent = render_section_extent(section);
  while (offset < render_extent) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    uint32_t start = offset;
    uint32_t cursor = offset;
    uint32_t instruction_count = 0U;
    uint8_t terminal_flow_kind = 0U;
    uint8_t required_cpu = M68K_ASM_CPU_68000;
    uint32_t terminal_offset = 0U;
    int has_accepted_code_boundary = offset > 0U && analysis_accepted_byte_at(section, accepted_bytes, offset - 1U);
    int has_renderable_label = lookup_has_renderable_label(lookup, section->section_index, offset);
    const M68kAnalysisStructuredDataItem *structured_item_at_start = NULL;
    uint32_t runtime_address = 0U;
    int has_runtime_view = lookup_source_runtime_address(lookup, section->section_index, offset,
      &runtime_address);
    int has_non_control_runtime_address_ref = !has_accepted_code_boundary &&
      analysis_orphan_start_has_non_control_runtime_address_ref(lookup, section, offset);
    if (!(has_accepted_code_boundary || has_renderable_label) ||
        accepted_start_at(section, accepted_start, offset) ||
        analysis_accepted_byte_at(section, accepted_bytes, offset)) {
      ++offset;
      continue;
    }
    structured_item_at_start = lookup_structured_data_item_covering_offset(lookup, section->section_index, offset);
    while (cursor < render_extent && instruction_count < 8U) {
      M68kDecodeCandidate decoded_candidate;
      uint32_t next_offset;
      candidate = analysis_orphan_decode_candidate_at_offset(lookup, section, cursor, &decoded_candidate);
      if (candidate == NULL || candidate->byte_count == 0U || candidate->byte_count > render_extent - cursor)
        break;
      next_offset = cursor + candidate->byte_count;
      if (analysis_orphan_candidate_range_is_blocked(lookup, section, accepted_bytes, cursor,
          candidate->byte_count, structured_item_at_start != NULL)) {
        break;
      }
      ++instruction_count;
      if (candidate->target_cpu > required_cpu) required_cpu = candidate->target_cpu;
      metadata = analysis_cfg_candidate_metadata(candidate, &instruction);
      if (metadata == NULL) break;
      if (!render_cfg_candidate_has_fallthrough(candidate)) {
        terminal_flow_kind = metadata->flow_kind;
        terminal_offset = cursor;
        break;
      }
      cursor = next_offset;
    }
    if (terminal_flow_kind != 0U && instruction_count >= 2U) {
      M68kOrphanCodeSignalIR signal;
      M68kDecodeCandidate terminal_decoded_candidate;
      const M68kDecodeCandidate *terminal_candidate;
      memset(&signal, 0, sizeof(signal));
      terminal_candidate = analysis_orphan_decode_candidate_at_offset(lookup, section, terminal_offset,
        &terminal_decoded_candidate);
      if (terminal_candidate == NULL) return -1;
      signal.offset = start;
      signal.size = (terminal_offset - start) + terminal_candidate->byte_count;
      signal.terminal_offset = terminal_offset;
      signal.terminal_flow_kind = terminal_flow_kind;
      signal.reason = M68K_ORPHAN_CODE_SIGNAL_TERMINAL_DECODE;
      signal.status = structured_item_at_start != NULL || has_non_control_runtime_address_ref
        ? M68K_ORPHAN_CODE_SIGNAL_SUPPRESSED
        : M68K_ORPHAN_CODE_SIGNAL_UNRESOLVED;
      signal.confidence = instruction_count >= 4U ? 90U : 70U;
      signal.required_cpu = required_cpu;
      signal.instruction_count = instruction_count > UINT8_MAX ? UINT8_MAX : (uint8_t)instruction_count;
      if (has_renderable_label && has_non_control_runtime_address_ref) {
        signal.context = M68K_ORPHAN_CODE_SIGNAL_CONTEXT_RENDERABLE_LABEL;
        signal.missing_inbound = analysis_orphan_missing_inbound_for_renderable_label(lookup,
          section->section_index, offset);
      } else if (has_runtime_view) {
        signal.context = M68K_ORPHAN_CODE_SIGNAL_CONTEXT_RUNTIME_VIEW;
        signal.missing_inbound = M68K_ORPHAN_CODE_SIGNAL_INBOUND_UNKNOWN;
      } else if (has_renderable_label) {
        signal.context = M68K_ORPHAN_CODE_SIGNAL_CONTEXT_RENDERABLE_LABEL;
        signal.missing_inbound = analysis_orphan_missing_inbound_for_renderable_label(lookup,
          section->section_index, offset);
      } else {
        signal.context = M68K_ORPHAN_CODE_SIGNAL_CONTEXT_ACCEPTED_CODE_BOUNDARY;
        signal.missing_inbound = M68K_ORPHAN_CODE_SIGNAL_INBOUND_UNKNOWN;
      }
      analysis_orphan_signal_attach_nearby_data_context(lookup, section, &signal);
      analysis_orphan_signal_refine_missing_inbound(lookup, section, &signal);
      analysis_orphan_signal_set_arbitration_flags(&signal, structured_item_at_start != NULL);
      signal.detail = structured_item_at_start != NULL
        ? "decoded terminal island suppressed by accepted structured data"
        : has_non_control_runtime_address_ref
        ? "decoded terminal island suppressed by non-control runtime address reference"
        : "decoded instruction island ends in generated terminal flow";
      if (m68k_ir_section_analysis_append_orphan_code_signal(section_analysis, &signal) != 0) return -1;
      if (analysis_append_orphan_absolute_operand_observations_for_signal(lookup, section, &signal,
          section_analysis) != 0) {
        return -1;
      }
      offset = start + signal.size;
      continue;
    }
    ++offset;
  }
  return 0;
}

static int instruction_has_call_flow_local(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  if (instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  return metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_CALL;
}

static int instruction_has_call_or_jump_flow_local(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  if (instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  return metadata != NULL &&
    (metadata->flow_kind == M68K_SIM_FLOW_CALL || metadata->flow_kind == M68K_SIM_FLOW_JUMP);
}

static int instruction_has_terminal_state_flow_local(const M68kInstructionIR *instruction) {
  return platform_instruction_has_terminal_state_flow(instruction);
}

static int candidate_has_call_flow_local(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  return instruction_has_call_flow_local(&instruction);
}

static int platform_call_input_equal(const PlatformFactsV2CallInput *left,
    const PlatformFactsV2CallInput *right) {
  if (left == NULL || right == NULL) return 0;
  return left->reg_kind == right->reg_kind &&
    left->reg_index == right->reg_index &&
    left->has_struct_type == right->has_struct_type &&
    left->has_value_domain == right->has_value_domain &&
    left->is_string_pointer == right->is_string_pointer &&
    left->is_write_buffer == right->is_write_buffer &&
    left->is_write_length == right->is_write_length &&
    strcmp(left->input_name, right->input_name) == 0 &&
    strcmp(left->type_name, right->type_name) == 0 &&
    strcmp(left->semantic_kind_name, right->semantic_kind_name) == 0 &&
    strcmp(left->value_domain_name, right->value_domain_name) == 0;
}

static const char *amiga_output_type_or_struct_name(const AmigaOsCallOutputInfo *output) {
  const char *name;
  if (output == NULL) return NULL;
  if (output->struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, output->struct_id);
    if (name != NULL && name[0] != '\0') return name;
  }
  if (output->type_id != AMIGA_OS_TYPE_ID_NONE) {
    name = amiga_os_name(M68K_PLATFORM_NAME_TYPE, output->type_id);
    if (name != NULL && name[0] != '\0') return name;
  }
  return NULL;
}

static void typed_stored_value_platform_names(const M68kRenderTypedStoredValue *value, const char **out_symbol_name,
    const char **out_type_name, const char **out_semantic_kind, const char **out_value_domain_name) {
  const AmigaOsCallOutputInfo *output;
  if (out_symbol_name != NULL) *out_symbol_name = NULL;
  if (out_type_name != NULL) *out_type_name = NULL;
  if (out_semantic_kind != NULL) *out_semantic_kind = NULL;
  if (out_value_domain_name != NULL) *out_value_domain_name = NULL;
  if (value == NULL) return;
  output = value->output;
  if (output != NULL) {
    if (out_symbol_name != NULL) *out_symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id);
    if (out_type_name != NULL) *out_type_name = amiga_output_type_or_struct_name(output);
    if (out_semantic_kind != NULL)
      *out_semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id);
    if (out_value_domain_name != NULL)
      *out_value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id);
  } else if (value->struct_id != AMIGA_OS_STRUCT_ID_NONE && out_type_name != NULL) {
    *out_type_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, value->struct_id);
  }
}

static int operand_is_predec_a7_local(const M68kOperandIR *operand) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_PREDEC) return operand->value.reg == 7U;
  return operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 4U && operand->value.ea_reg == 7U;
}

static uint16_t reglist_long_stack_size_local(uint32_t mask) {
  uint16_t size = 0U;
  unsigned bit;
  for (bit = 0U; bit < 16U; ++bit) {
    if ((mask & (1UL << bit)) != 0U) size = (uint16_t)(size + 4U);
  }
  return size;
}

static int operand_is_stack_displacement_local(const M68kOperandIR *operand, int16_t *out_displacement);
static int typed_storage_keys_match(const M68kRenderTypedStorageSlot *slot, uint8_t kind, size_t section_index,
    int32_t displacement, uint32_t address);
static void typed_state_clear_reg(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index);
static void typed_memory_base_clear(M68kRenderTypedMemoryBaseValue *value);
static int typed_memory_base_offset_add(uint32_t base_offset, int32_t displacement, uint32_t *out_offset);
static void typed_memory_base_clear_pointer_table_if_offset_outside(M68kRenderTypedMemoryBaseValue *value);
static int policy_declared_app_extent_covers(const M68kAnalysisPolicy *policy, int16_t displacement,
    uint32_t access_size);
static int typed_app_memory_span(const M68kRenderLookup *lookup, const M68kRenderTypedState *state,
    const M68kInstructionIR *instruction, size_t operand_index, uint8_t *out_reg,
    int16_t *out_displacement, uint8_t *out_access, uint8_t *out_width,
    uint8_t *out_element_width, uint8_t *out_count);
static int render_lookup_record_layout_field_uses(M68kRenderLookup *lookup, size_t section_index,
    const M68kRenderPlatformState *state, const M68kInstructionIR *instruction, uint32_t offset);
static int render_lookup_record_base_app_accesses(M68kRenderLookup *lookup, size_t section_index,
    const M68kRenderPlatformState *state, const M68kInstructionIR *instruction, uint32_t offset,
    int legacy_fallbacks);
static int render_lookup_record_derived_app_operand(M68kRenderLookup *lookup, size_t section_index,
    const M68kRenderTypedState *state, const M68kInstructionIR *instruction, uint32_t offset, size_t operand_index);
static int render_lookup_record_derived_app_accesses(M68kRenderLookup *lookup, size_t section_index,
    const M68kRenderTypedState *state, const M68kInstructionIR *instruction, uint32_t offset);
static int render_lookup_record_affine_address_uses(M68kRenderLookup *lookup, size_t section_index,
    const M68kRenderTypedState *state, const M68kInstructionIR *instruction, uint32_t offset);
static int typed_memory_bases_equal(const M68kRenderTypedMemoryBaseValue *left,
    const M68kRenderTypedMemoryBaseValue *right);
static int candidate_loads_data_target_to_address_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg);
static int candidate_data_target_for_operand(const M68kDecodeCandidate *candidate, uint32_t operand_index,
    size_t *out_section_index, uint32_t *out_offset);
static int candidate_local_target_for_operand(const M68kDecodeCandidate *candidate, uint32_t operand_index,
    size_t *out_section_index, uint32_t *out_offset);
static int read_library_name_string_at(const M68kDecodeSectionIR *section, uint32_t offset,
    char *out_name, size_t out_size);
static int read_library_name_string_from_object(const M68kObject *object, size_t section_index,
    uint32_t offset, char *out_name, size_t out_size);
static int candidate_loads_runtime_address_ref_target_to_address_reg(const M68kRenderLookup *lookup,
    size_t section_index, const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg);
static int accepted_range_has_code_byte(const uint8_t *accepted_bytes, uint32_t section_size,
    uint32_t offset, uint32_t size);
static int render_lookup_mark_label(M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
static const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_primary_vector_at(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index, uint32_t helper_offset,
    unsigned depth);
static int instruction_move_operand_indices_from_metadata(const M68kInstructionIR *instruction,
    size_t *out_source_index, size_t *out_dest_index, const M68kSimFormMetadata **out_metadata);
int operand_address_register_index_local(const M68kOperandIR *operand, uint8_t *out_reg);
int operand_is_address_memory_local(const M68kOperandIR *operand, uint8_t *out_reg, int16_t *out_displacement);
static uint16_t lookup_typed_app_slot_struct_id(const M68kRenderLookup *lookup, int16_t displacement);
static const M68kAnalysisAbstractRegion *lookup_abstract_region_for_source_range(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset, uint32_t size) {
  const M68kAnalysisAbstractRegion *match = NULL;
  uint16_t index;
  if (lookup == NULL || lookup->policy == NULL || size == 0U || offset > UINT32_MAX - size) return NULL;
  for (index = 0U; index < lookup->policy->abstract_region_count &&
       index < M68K_ANALYSIS_ABSTRACT_REGION_LIMIT; ++index) {
    const M68kAnalysisAbstractRegion *region = &lookup->policy->abstract_regions[index];
    if (region->section_index != section_index || region->size == 0U ||
        region->start_offset > UINT32_MAX - region->size || offset < region->start_offset ||
        size > region->start_offset + region->size - offset) continue;
    /* Policy validation rejects overlap. Retain the explicit uniqueness guard
     * here so an in-memory malformed policy cannot turn ambiguous ownership
     * into an arbitrary effect subject. */
    if (match != NULL) return NULL;
    match = region;
  }
  return match;
}

static int typed_flow_local_callee_effect_summary(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index, uint32_t target_offset,
    M68kAnalysisFunctionSummary *out_summary, uint8_t *out_limit_hit);
static const M68kAnalysisAbstractRegion *lookup_abstract_region_for_source_range(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset, uint32_t size);
static const M68kAnalysisFunctionSummary *lookup_inferred_direct_function_summary(
  const M68kRenderLookup *lookup, size_t section_index, uint32_t entry_offset);
static size_t lookup_inferred_direct_function_summary_index(const M68kRenderLookup *lookup,
  size_t section_index, uint32_t entry_offset);
static const M68kAnalysisFunctionSummary *lookup_inferred_callback_table_function_summary(
  const M68kRenderLookup *lookup, size_t section_index, uint32_t table_offset);
static int instruction_may_update_stack_pointer_from_metadata(const M68kInstructionIR *);
static int typed_state_addr_alias_equal(const M68kRenderTypedState *, uint8_t, uint8_t);
static void typed_reg_forget_interpretation(M68kRenderTypedRegValue *);
static void typed_state_apply_function_summary_effects(M68kRenderTypedState *state,
    const M68kAnalysisFunctionSummary *summary);
static int generated_platform_call_summary(uint8_t platform_kind, const AmigaOsLibraryVectorInfo *vector,
    uint8_t output_reg_known, uint8_t output_reg_kind, uint8_t output_reg_index,
    M68kAnalysisFunctionSummary *out_summary);

/* A wrapper is usable only when its local effects and generated platform ABI
 * form one exact callable contract.  These are terminal composition states:
 * callers never truncate either side to obtain a plausible partial summary. */
typedef enum M68kPlatformContractCompositionState {
  M68K_PLATFORM_CONTRACT_COMPOSITION_COMPLETE = 0,
  M68K_PLATFORM_CONTRACT_COMPOSITION_CAPACITY = 1,
  M68K_PLATFORM_CONTRACT_COMPOSITION_IDENTITY_CONFLICT = 2
} M68kPlatformContractCompositionState;
static M68kPlatformContractCompositionState function_summary_compose_platform_contract(
    const M68kAnalysisFunctionSummary *local_summary,
    const M68kAnalysisFunctionSummary *platform_summary,
    M68kAnalysisFunctionSummary *out_summary);

#define M68K_RENDER_TYPED_FLOW_DEFAULT_NODE_VISIT_LIMIT 2000000U
#define M68K_RENDER_TYPED_FLOW_DEFAULT_ITERATION_LIMIT 64U

static int instruction_stack_delta_for_comment(const M68kInstructionIR *instruction, int32_t *out_delta) {
  size_t operand_index;
  uint8_t dest_reg = 0U;
  if (out_delta != NULL) *out_delta = 0;
  if (instruction == NULL || out_delta == NULL) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_PEA && instruction->operand_count == 1U) {
    *out_delta = 4;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U && operand_is_predec_a7_local(&instruction->operands[1])) {
    *out_delta = 4;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U && operand_is_postinc_a7_local(&instruction->operands[0])) {
    *out_delta = -4;
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U) {
    if (instruction->operands[0].kind == M68K_ASM_OPERAND_REGLIST &&
        operand_is_predec_a7_local(&instruction->operands[1])) {
      *out_delta = reglist_long_stack_size_local(instruction->operands[0].value.value);
      return 1;
    }
    if (operand_is_postinc_a7_local(&instruction->operands[0]) &&
        instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
      *out_delta = -(int32_t)reglist_long_stack_size_local(instruction->operands[1].value.value);
      return 1;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
      (operand_address_register_index_local(&instruction->operands[1], &dest_reg) && dest_reg == 7U)) {
    int16_t displacement = 0;
    if (!operand_is_stack_displacement_local(&instruction->operands[0], &displacement)) return 0;
    *out_delta = -(int32_t)displacement;
    return 1;
  }
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADD ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDA ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDI ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDQ ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUB ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBA ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBI ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBQ) &&
      instruction->operand_count == 2U && (operand_address_register_index_local(&instruction->operands[1], &dest_reg) && dest_reg == 7U)) {
    uint32_t value = 0U;
    if (!m68k_ir_operand_immediate_value(&instruction->operands[0], &value) || value > INT16_MAX) return 0;
    *out_delta = (instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUB ||
                  instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBA ||
                  instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBI ||
                  instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBQ)
      ? (int32_t)value
      : -(int32_t)value;
    return 1;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    if (operand_is_predec_a7_local(&instruction->operands[operand_index]) ||
        operand_is_postinc_a7_local(&instruction->operands[operand_index])) {
      return 0;
    }
  }
  if (instruction->operand_count > 0U &&
      (operand_address_register_index_local(&instruction->operands[instruction->operand_count - 1U], &dest_reg) && dest_reg == 7U)) {
    return 0;
  }
  return 1;
}

static int operand_is_stack_displacement_local(const M68kOperandIR *operand, int16_t *out_displacement) {
  uint8_t reg = 0U;
  int16_t displacement = 0;
  if (out_displacement != NULL) *out_displacement = 0;
  /* `(a7)` and `0(a7)` are one caller-stack location.  The former is EA mode
   * 2, while the latter is mode 5 with a zero extension; normalise both to
   * the same durable stack-slot identity before typed flow records it. */
  if (!operand_is_address_memory_local(operand, &reg, &displacement) || reg != 7U) return 0;
  if (out_displacement != NULL) *out_displacement = displacement;
  return 1;
}

static int recovered_function_arg_temp_add(M68kRenderRecoveredFunctionArg *args, size_t *arg_count,
    size_t arg_capacity, size_t section_index, uint32_t function_offset, uint16_t stack_offset,
    uint8_t reg_kind, uint8_t reg_index, const PlatformFactsV2CallInput *input) {
  size_t index;
  if (args == NULL || arg_count == NULL || input == NULL || stack_offset == 0U ||
      reg_kind == 0U || reg_index >= 8U) {
    return 0;
  }
  for (index = 0U; index < *arg_count; ++index) {
    M68kRenderRecoveredFunctionArg *arg = &args[index];
    if (arg->section_index == section_index && arg->function_offset == function_offset &&
        arg->stack_offset == stack_offset && arg->reg_kind == reg_kind && arg->reg_index == reg_index) {
      return arg->input_valid != 0U && platform_call_input_equal(&arg->input, input) ? 0 : -1;
    }
  }
  if (*arg_count >= arg_capacity) return -1;
  memset(&args[*arg_count], 0, sizeof(args[*arg_count]));
  args[*arg_count].section_index = section_index;
  args[*arg_count].function_offset = function_offset;
  args[*arg_count].stack_offset = stack_offset;
  args[*arg_count].reg_kind = reg_kind;
  args[*arg_count].reg_index = reg_index;
  args[*arg_count].input_valid = 1U;
  args[*arg_count].input = *input;
  *arg_count += 1U;
  return 0;
}

static int collect_recovered_function_args_from_stack_load_instruction(
    M68kRenderRecoveredFunctionArg *args, size_t *arg_count, size_t arg_capacity,
    size_t section_index, uint32_t function_offset, const M68kInstructionIR *instruction,
    const AmigaOsLibraryVectorInfo *vector, uint16_t stack_frame_depth) {
  int16_t displacement = 0;
  if (args == NULL || arg_count == NULL || instruction == NULL || vector == NULL) return 0;
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->size_suffix == 'l' && instruction->operand_count == 2U &&
      operand_is_stack_displacement_local(&instruction->operands[0], &displacement) &&
      displacement > (int16_t)stack_frame_depth) {
    uint8_t reg = 0U;
    uint8_t reg_kind = 0U;
    PlatformFactsV2CallInput input;
    if (operand_is_data_register_local(&instruction->operands[1], &reg)) reg_kind = 1U;
    else if (instruction->operands[1].kind == M68K_ASM_OPERAND_AN) {
      reg = (uint8_t)instruction->operands[1].value.reg;
      reg_kind = 2U;
    }
    if (amiga_vector_call_input_by_register(vector, reg_kind, reg, &input)) {
      return recovered_function_arg_temp_add(args, arg_count, arg_capacity, section_index, function_offset,
        (uint16_t)(displacement - (int16_t)stack_frame_depth), reg_kind, reg, &input);
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U &&
      operand_is_stack_displacement_local(&instruction->operands[0], &displacement) &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST &&
      displacement > (int16_t)stack_frame_depth) {
    uint32_t mask = instruction->operands[1].value.value;
    uint16_t stack_offset = (uint16_t)(displacement - (int16_t)stack_frame_depth);
    unsigned bit;
    for (bit = 0U; bit < 16U; ++bit) {
      uint8_t reg_kind;
      uint8_t reg_index;
      PlatformFactsV2CallInput input;
      if ((mask & (1UL << bit)) == 0U) continue;
      reg_kind = bit < 8U ? 1U : 2U;
      reg_index = (uint8_t)(bit < 8U ? bit : bit - 8U);
      if (amiga_vector_call_input_by_register(vector, reg_kind, reg_index, &input) &&
          recovered_function_arg_temp_add(args, arg_count, arg_capacity, section_index,
            function_offset, stack_offset, reg_kind, reg_index, &input) != 0) {
        return -1;
      }
      stack_offset = (uint16_t)(stack_offset + 4U);
    }
  }
  return 0;
}

static int render_lookup_collect_recovered_function_args_from_wrapper(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t wrapper_section_index, uint32_t wrapper_offset,
    const AmigaOsLibraryVectorInfo *expected_vector) {
  const M68kDecodeSectionIR *section;
  M68kRenderPlatformState state;
  M68kRenderRecoveredFunctionArg args[16];
  size_t arg_count = 0U;
  uint32_t cursor;
  uint16_t stack_frame_depth = 0U;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || expected_vector == NULL ||
      wrapper_section_index >= decode->section_count) {
    return 0;
  }
  section = &decode->sections[wrapper_section_index];
  if (!accepted_start_at(section, accepted_start[wrapper_section_index], wrapper_offset)) return 0;
  memset(&state, 0, sizeof(state));
  memset(args, 0, sizeof(args));
  cursor = wrapper_offset;
  while (cursor < section->size && cursor - wrapper_offset < 256U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const AmigaOsLibraryVectorInfo *vector;
    int32_t delta = 0;
    if (!accepted_start_at(section, accepted_start[wrapper_section_index], cursor)) break;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index, cursor);
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
    vector = attach_amiga_lvo_symbol_if_known(&state, &instruction);
    if (vector == NULL) {
      vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[wrapper_section_index],
        candidate, &instruction);
    }
    if (vector == NULL) {
      vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &state, section, candidate);
    }
    if (vector == expected_vector) {
      size_t index;
      for (index = 0U; index < arg_count; ++index) {
        if (args[index].input_valid == 0U) continue;
        if (render_lookup_add_recovered_function_arg(lookup, args[index].section_index, args[index].function_offset,
            args[index].stack_offset, args[index].reg_kind, args[index].reg_index, &args[index].input) != 0) {
          return -1;
        }
      }
      return 0;
    }
    if (vector != NULL || candidate_has_non_call_control_target(candidate)) break;
    if (collect_recovered_function_args_from_stack_load_instruction(args, &arg_count,
        sizeof(args) / sizeof(args[0]), section->section_index, wrapper_offset, &instruction, expected_vector,
        stack_frame_depth) != 0) {
      return -1;
    }
    if (!instruction_stack_delta_for_comment(&instruction, &delta)) break;
    if (delta < 0 && (uint32_t)(-delta) > (uint32_t)stack_frame_depth) break;
    if (delta > 0 && (uint32_t)delta > UINT16_MAX - (uint32_t)stack_frame_depth) break;
    stack_frame_depth = (uint16_t)((int32_t)stack_frame_depth + delta);
    platform_state_update_data_lvo_after_instruction(&state, &instruction);
    platform_state_update_after_instruction(&state, lookup, &instruction);
    if (!candidate_has_local_helper_summary_fallthrough(candidate)) break;
    cursor += candidate->byte_count;
  }
  return 0;
}

static int render_lookup_infer_amiga_platform_derived_summaries(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  M68kRenderPlatformState platform_state;
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  memset(&platform_state, 0, sizeof(platform_state));
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const AmigaOsLibraryVectorInfo *wrapper_call_vector;
      const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
      const AmigaOsLibraryVectorInfo *helper_call_vector;
      const AmigaOsLibraryVectorInfo *vector;
      size_t target_section_index = 0U;
      uint32_t target_offset = 0U;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      platform_state_apply_policy_register_seeds(&platform_state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
      wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &platform_state, section, candidate);
      direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
        section->section_index, candidate);
      helper_call_vector = (wrapper_call_vector == NULL && direct_wrapper_vector == NULL)
        ? resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start, section->section_index, candidate)
        : NULL;
      vector = direct_wrapper_vector != NULL ? direct_wrapper_vector :
        (wrapper_call_vector != NULL ? wrapper_call_vector : helper_call_vector);
      if (vector != NULL &&
          candidate_direct_control_target(lookup, section->section_index, candidate, &target_section_index,
            &target_offset) &&
          render_lookup_add_platform_derived_summary(lookup, target_section_index, target_offset, vector) != 0) {
        return -1;
      }
      platform_state_update_data_lvo_after_instruction(&platform_state, &instruction);
      platform_state_update_after_instruction(&platform_state, lookup, &instruction);
    }
  }
  return 0;
}

static int render_lookup_infer_amiga_recovered_function_args(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  M68kRenderPlatformState platform_state;
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  memset(&platform_state, 0, sizeof(platform_state));
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      const AmigaOsLibraryVectorInfo *wrapper_call_vector;
      const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
      const AmigaOsLibraryVectorInfo *vector;
      size_t target_section_index = 0U;
      uint32_t target_offset = 0U;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      platform_state_apply_policy_register_seeds(&platform_state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
      wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &platform_state, section, candidate);
      direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
        section->section_index, candidate);
      vector = direct_wrapper_vector != NULL ? direct_wrapper_vector : wrapper_call_vector;
      if (vector != NULL &&
          candidate_direct_control_target(lookup, section->section_index, candidate, &target_section_index,
            &target_offset) &&
          render_lookup_collect_recovered_function_args_from_wrapper(lookup, decode, accepted_start,
            target_section_index, target_offset, vector) != 0) {
        return -1;
      }
      platform_state_update_data_lvo_after_instruction(&platform_state, &instruction);
      platform_state_update_after_instruction(&platform_state, lookup, &instruction);
    }
  }
  return 0;
}

static int amiga_output_has_typed_info(const AmigaOsCallOutputInfo *output) {
  if (output == NULL || output->reg_kind == AMIGA_OS_REGISTER_NONE || output->reg_index >= 8U) return 0;
  return amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id) != NULL ||
    amiga_output_type_or_struct_name(output) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id) != NULL ||
    amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id) != NULL;
}

static void typed_state_clear_base_slots_for_base(M68kRenderTypedState *state, uint8_t base_reg) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return;
  index = 0U;
  while (index < state->base_slot_count) {
    if (state->base_slots[index].known == 0U || state->base_slots[index].base_reg != base_reg) {
      ++index;
      continue;
    }
    state->base_slots[index] = state->base_slots[state->base_slot_count - 1U];
    --state->base_slot_count;
  }
  index = 0U;
  while (index < state->field_slot_count) {
    if (state->field_slots[index].known == 0U || state->field_slots[index].base_reg != base_reg) {
      ++index;
      continue;
    }
    state->field_slots[index] = state->field_slots[state->field_slot_count - 1U];
    --state->field_slot_count;
  }
}

/* Memory writes can invalidate a pointee/cache contract, not rewrite a
 * preserved CPU register. Keep the independent whole-value components while
 * discarding memory-derived type/origin payload. Actual register writes use
 * typed_state_clear_reg directly and therefore cannot resurrect these IDs. */
static void typed_state_invalidate_memory_derived_reg(M68kRenderTypedState *state,
    uint8_t kind, uint8_t reg) {
  M68kRenderTypedRegValue *value = kind == M68K_ANALYSIS_REGISTER_DATA ?
    &state->data_regs[reg] : &state->addr_regs[reg];
  M68kRenderTypedRegValue before = *value;
  M68kRenderTypedProvenance provenance = before.provenance;
  M68kRenderTypedAppAddressValue app = kind == M68K_ANALYSIS_REGISTER_DATA ?
    state->data_app_addr_regs[reg] : state->app_addr_regs[reg];
  uint32_t aliases = state->addr_reg_alias_known;
  uint8_t alias_sources[8];
  memcpy(alias_sources, state->addr_reg_alias_source, sizeof(alias_sources));
  typed_reg_forget_interpretation(&before);
  typed_state_clear_reg(state, kind, reg);
  *value = before;
  /* A memory effect cannot change equality of already held CPU values. */
  state->addr_reg_alias_known = aliases;
  memcpy(state->addr_reg_alias_source, alias_sources, sizeof(alias_sources));
  if (app.known) value->provenance = provenance;
  if (kind == M68K_ANALYSIS_REGISTER_DATA) state->data_app_addr_regs[reg] = app;
  else state->app_addr_regs[reg] = app;
}

/* The typed-flow state already records the durable storage origin of values
 * reloaded from tracked static/app/base slots.  A static-storage effect can
 * therefore invalidate only the exact reloads and caches rooted at that
 * storage identity; it must not discard an unrelated preserved register. */
static void typed_state_invalidate_static_storage_subject(M68kRenderTypedState *state,
    const M68kFunctionSummaryEffectSubjectIR *subject) {
  uint8_t reg;
  if (state == NULL || subject == NULL ||
      subject->kind != M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STATIC_STORAGE) return;
  for (reg = 0U; reg < 8U; ++reg) {
    const M68kRenderTypedStorageOrigin *data_origin = &state->data_regs[reg].origin;
    const M68kRenderTypedStorageOrigin *address_origin = &state->addr_regs[reg].origin;
    if (data_origin->kind == M68K_RENDER_TYPED_ORIGIN_LOOKUP_STORAGE &&
        data_origin->section_index == subject->section_index && data_origin->address == subject->offset) {
      typed_state_invalidate_memory_derived_reg(state, M68K_ANALYSIS_REGISTER_DATA, reg);
    }
    if (address_origin->kind == M68K_RENDER_TYPED_ORIGIN_LOOKUP_STORAGE &&
        address_origin->section_index == subject->section_index && address_origin->address == subject->offset) {
      typed_state_invalidate_memory_derived_reg(state, M68K_ANALYSIS_REGISTER_ADDRESS, reg);
      continue;
    }
    if (state->memory_base_regs[reg].known != 0U &&
        state->memory_base_regs[reg].section_index == subject->section_index &&
        state->memory_base_regs[reg].offset == subject->offset) {
      typed_state_clear_base_slots_for_base(state, reg);
    }
  }
}

static void typed_state_invalidate_input_subject(M68kRenderTypedState *state,
    const M68kAnalysisFunctionSummary *summary, uint8_t input_index) {
  const M68kAnalysisFunctionSummaryInput *input;
  uint8_t member_index;
  if (state == NULL || summary == NULL || input_index >= summary->input_count) return;
  input = &summary->inputs[input_index];
  if (input->location.kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER &&
      input->location.kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER_TUPLE) return;
  for (member_index = 0U; member_index < input->location.register_count; ++member_index) {
    uint8_t base_reg = input->location.registers[member_index].register_index;
    uint8_t candidate;
    if (input->location.registers[member_index].register_kind != M68K_ANALYSIS_REGISTER_ADDRESS || base_reg >= 8U)
      continue;
    /* Field/base slots are indexed by the physical base register.  Include
     * directly tracked aliases of the ABI input; the underlying pointer can
     * be preserved while values cached through either spelling become stale. */
    for (candidate = 0U; candidate < 8U; ++candidate) {
      if (candidate == base_reg ||
          typed_state_addr_alias_equal(state, candidate, base_reg)) {
        uint8_t reg;
        /* A value loaded from a field/base cache is not a direct alias of the
         * input pointer.  It is nevertheless stale after a write through that
         * input, so retain the input itself but discard that derived register
         * value before removing its backing cache. */
        for (reg = 0U; reg < 8U; ++reg) {
          const M68kRenderTypedStorageOrigin *data_origin = &state->data_regs[reg].origin;
          const M68kRenderTypedStorageOrigin *address_origin = &state->addr_regs[reg].origin;
          if (data_origin->kind == M68K_RENDER_TYPED_ORIGIN_BASE_SLOT &&
              data_origin->base_reg == candidate) {
            typed_state_invalidate_memory_derived_reg(state, M68K_ANALYSIS_REGISTER_DATA, reg);
          }
          if (address_origin->kind == M68K_RENDER_TYPED_ORIGIN_BASE_SLOT &&
              address_origin->base_reg == candidate && reg != candidate &&
              !typed_state_addr_alias_equal(state, reg, candidate)) {
            typed_state_invalidate_memory_derived_reg(state, M68K_ANALYSIS_REGISTER_ADDRESS, reg);
          }
        }
        typed_state_clear_base_slots_for_base(state, candidate);
      }
    }
  }
}

/* Stack effects have the same exact-storage rule as static effects.  The ABI
 * convention is part of the identity: a caller result or cleanup slot at an
 * equal displacement cannot invalidate a caller argument. */
static void typed_state_invalidate_stack_subject(M68kRenderTypedState *state,
    const M68kFunctionSummaryEffectSubjectIR *subject) {
  size_t index;
  if (state == NULL || subject == NULL || subject->kind != M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STACK ||
      subject->offset > INT16_MAX) return;
  for (index = 0U; index < state->stack_slot_count; ++index) {
    const M68kRenderTypedStackSlot *slot = &state->stack_slots[index];
    if (slot->known == 0U || slot->displacement != (int16_t)subject->offset ||
        slot->abi_stack_convention != subject->stack_convention) continue;
    state->stack_slots[index] = state->stack_slots[state->stack_slot_count - 1U];
    --state->stack_slot_count;
    return;
  }
}

static void typed_origin_clear(M68kRenderTypedStorageOrigin *origin) {
  if (origin == NULL) return;
  memset(origin, 0, sizeof(*origin));
}

static void typed_provenance_clear(M68kRenderTypedProvenance *provenance) {
  if (provenance == NULL) return;
  memset(provenance, 0, sizeof(*provenance));
}

static void typed_reg_value_clear(M68kRenderTypedRegValue *value) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
  value->struct_id = AMIGA_OS_STRUCT_ID_NONE;
}

/* Type/cache interpretation can be forgotten without changing the held
 * value. CPU assignments still use the full register-write path. */
static void typed_reg_forget_interpretation(M68kRenderTypedRegValue *value) {
  M68kRenderTypedRegValue before = *value;
  typed_reg_value_clear(value);
  value->layout_base_id = before.layout_base_id;
  value->entry_value_id = before.entry_value_id;
  value->raw_long_value_known = before.raw_long_value_known;
  value->raw_long_candidate_count = before.raw_long_candidate_count;
  value->raw_long_value = before.raw_long_value;
  memcpy(value->raw_long_candidates, before.raw_long_candidates, sizeof(value->raw_long_candidates));
  value->address_value_candidate_overflow = before.address_value_candidate_overflow;
  value->known = value->layout_base_id || value->raw_long_value_known;
  if (value->known || value->entry_value_id) value->provenance = before.provenance;
}

static void typed_stored_value_clear(M68kRenderTypedStoredValue *value) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
  value->struct_id = AMIGA_OS_STRUCT_ID_NONE;
}

static int typed_table_origins_equal(const M68kAddressValueTableOriginIR *left,
    const M68kAddressValueTableOriginIR *right) {
  if (left == NULL || right == NULL) return 0;
  return left->has_origin == right->has_origin && left->selection_kind == right->selection_kind &&
    left->terminal_kind == right->terminal_kind && left->table_section_index == right->table_section_index &&
    left->table_start_offset == right->table_start_offset &&
    left->consumer_section_index == right->consumer_section_index &&
    left->consumer_offset == right->consumer_offset &&
    left->address_expression_id == right->address_expression_id &&
    left->entry_index == right->entry_index && left->index_min == right->index_min &&
    left->index_max == right->index_max;
}

static void typed_table_origin_clear(M68kAddressValueTableOriginIR *origin) {
  if (origin == NULL) return;
  memset(origin, 0, sizeof(*origin));
  origin->entry_index = UINT32_MAX;
}

/* A branch merge can retain a small, exact set of static pointer values. */
static void typed_pointer_candidates_normalize(uint8_t *known, uint8_t *count,
    uint32_t *value, uint32_t candidates[4]) {
  if (known == NULL || count == NULL || value == NULL || candidates == NULL) return;
  if (*known == 0U) { *count = 0U; return; }
  if (*count == 0U) { candidates[0] = *value; *count = 1U; }
  *value = candidates[0];
}

M68kRenderPointerCandidateMergeResult m68k_render_pointer_candidates_merge(uint8_t *dest_known, uint8_t *dest_count,
    uint32_t *dest_value, uint32_t dest_candidates[4], uint8_t source_known,
    uint8_t source_count, uint32_t source_value, const uint32_t source_candidates[4]) {
  uint32_t merged[4];
  size_t count = 0U, index, candidate_index;
  if (dest_known == NULL || dest_count == NULL || dest_value == NULL || dest_candidates == NULL ||
      source_candidates == NULL) return M68K_RENDER_POINTER_CANDIDATE_MERGE_NONE;
  memset(merged, 0, sizeof(merged));
  typed_pointer_candidates_normalize(dest_known, dest_count, dest_value, dest_candidates);
  if (source_known == 0U) return M68K_RENDER_POINTER_CANDIDATE_MERGE_NONE;
  if (source_count == 0U) source_count = 1U;
  for (index = 0U; index < *dest_count; ++index) merged[count++] = dest_candidates[index];
  for (index = 0U; index < source_count; ++index) {
    uint32_t candidate = source_count == 1U && index == 0U ? source_value : source_candidates[index];
    for (candidate_index = 0U; candidate_index < count; ++candidate_index)
      if (merged[candidate_index] == candidate) break;
    if (candidate_index == count) {
      if (count == sizeof(merged) / sizeof(merged[0])) return M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW;
      merged[count++] = candidate;
    }
  }
  memcpy(dest_candidates, merged, sizeof(merged));
  *dest_count = (uint8_t)count;
  *dest_value = merged[0];
  *dest_known = 1U;
  return M68K_RENDER_POINTER_CANDIDATE_MERGE_EXACT;
}

/* CFG predecessors are both real inputs. Unknown numeric bits are top,
 * unlike the empty accumulator accepted by the generic candidate union. */
static M68kRenderPointerCandidateMergeResult typed_must_candidates_merge(
    uint8_t *known, uint8_t *count, uint32_t *value, uint32_t candidates[4],
    uint8_t source_known, uint8_t source_count, uint32_t source_value, const uint32_t source_candidates[4]) {
  if (!*known || !source_known) {
    *known = *count = 0U; *value = 0U; memset(candidates, 0, 4U * sizeof(*candidates));
    return M68K_RENDER_POINTER_CANDIDATE_MERGE_NONE;
  }
  return m68k_render_pointer_candidates_merge(known, count, value, candidates,
    source_known, source_count, source_value, source_candidates);
}

static int typed_stored_value_has_payload(const M68kRenderTypedStoredValue *value) {
  return value != NULL && (value->struct_id != AMIGA_OS_STRUCT_ID_NONE || value->layout_base_id != 0U || value->app_address_known != 0U ||
    value->pointer_value_known != 0U || value->raw_long_value_known != 0U ||
    value->address_value_candidate_overflow != 0U || value->table_origin.has_origin != 0U);
}

static void typed_stored_value_update_known(M68kRenderTypedStoredValue *value) {
  if (value == NULL) return;
  value->known = typed_stored_value_has_payload(value) ? 1U : 0U;
}

static M68kRenderTypedProvenance typed_provenance_make(uint8_t kind, size_t section_index, uint32_t offset) {
  M68kRenderTypedProvenance provenance;
  memset(&provenance, 0, sizeof(provenance));
  provenance.kind = kind;
  provenance.section_index = section_index;
  provenance.offset = offset;
  return provenance;
}

static void typed_provenance_append_transfer(M68kRenderTypedProvenance *provenance,
    size_t section_index, uint32_t offset, uint8_t source_operand_index, uint8_t destination_operand_index) {
  M68kAddressValueTransferIR *transfer;
  if (provenance == NULL || provenance->kind == M68K_PLATFORM_TYPE_PROVENANCE_NONE) return;
  if (provenance->transfer_count >= sizeof(provenance->transfers) / sizeof(provenance->transfers[0])) {
    provenance->transfer_truncated = 1U;
    return;
  }
  transfer = &provenance->transfers[provenance->transfer_count++];
  transfer->section_index = (uint32_t)section_index;
  transfer->offset = offset;
  transfer->source_operand_index = source_operand_index;
  transfer->destination_operand_index = destination_operand_index;
}

static int typed_provenances_equal(const M68kRenderTypedProvenance *left,
    const M68kRenderTypedProvenance *right);

static uint8_t typed_provenance_rank(uint8_t kind) {
  switch (kind) {
  case M68K_PLATFORM_TYPE_PROVENANCE_API_OUTPUT:
  case M68K_PLATFORM_TYPE_PROVENANCE_API_INPUT:
  case M68K_PLATFORM_TYPE_PROVENANCE_POLICY_SEED:
  case M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA:
    return 70U;
  case M68K_PLATFORM_TYPE_PROVENANCE_FIELD_POINTER:
  case M68K_PLATFORM_TYPE_PROVENANCE_FIELD_ADDRESS:
    return 60U;
  case M68K_PLATFORM_TYPE_PROVENANCE_LOOKUP_STORAGE:
    return 50U;
  case M68K_PLATFORM_TYPE_PROVENANCE_APP_SLOT:
  case M68K_PLATFORM_TYPE_PROVENANCE_BASE_SLOT:
  case M68K_PLATFORM_TYPE_PROVENANCE_STACK_SLOT:
    return 40U;
  case M68K_PLATFORM_TYPE_PROVENANCE_PREFIX_REFINEMENT:
    return 30U;
  case M68K_PLATFORM_TYPE_PROVENANCE_REGISTER_COPY:
    return 10U;
  case M68K_PLATFORM_TYPE_PROVENANCE_NONE:
  default:
    return 0U;
  }
}

static void typed_provenance_merge(M68kRenderTypedProvenance *dest,
    const M68kRenderTypedProvenance *source) {
  uint8_t dest_rank;
  uint8_t source_rank;
  if (dest == NULL || source == NULL) return;
  if (typed_provenances_equal(dest, source)) return;
  if (dest->kind == M68K_PLATFORM_TYPE_PROVENANCE_NONE ||
      source->kind == M68K_PLATFORM_TYPE_PROVENANCE_NONE) {
    typed_provenance_clear(dest);
    dest->merge_conflicted = 1U;
    return;
  }
  dest_rank = typed_provenance_rank(dest->kind);
  source_rank = typed_provenance_rank(source->kind);
  if (source_rank > dest_rank) {
    *dest = *source;
  } else if (source_rank == dest_rank) {
    typed_provenance_clear(dest);
    dest->merge_conflicted = 1U;
  }
}

static int typed_origins_equal(const M68kRenderTypedStorageOrigin *left,
    const M68kRenderTypedStorageOrigin *right) {
  if (left == NULL || right == NULL) return 0;
  return left->kind == right->kind && left->storage_kind == right->storage_kind &&
    left->base_reg == right->base_reg && left->section_index == right->section_index &&
    left->displacement == right->displacement && left->address == right->address;
}

static int typed_provenances_equal(const M68kRenderTypedProvenance *left,
    const M68kRenderTypedProvenance *right) {
  if (left == NULL || right == NULL) return 0;
  return left->kind == right->kind && left->section_index == right->section_index &&
    left->offset == right->offset && left->producer_operand_index == right->producer_operand_index &&
    left->transfer_count == right->transfer_count && left->transfer_truncated == right->transfer_truncated &&
    left->merge_conflicted == right->merge_conflicted &&
    memcmp(left->transfers, right->transfers, sizeof(left->transfers)) == 0;
}

#include "m68k_address_register_alias.inc"

static void typed_state_clear_io_request_setup(M68kRenderTypedState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  memset(&state->io_request_setups[reg_index], 0, sizeof(state->io_request_setups[reg_index]));
}

static void typed_state_clear_reg(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == 1U) {
    typed_reg_value_clear(&state->data_regs[reg_index]);
    state->data_app_addr_regs[reg_index].known = 0U;
    state->data_app_addr_regs[reg_index].displacement = 0;
    state->data_app_addr_regs[reg_index].base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
    typed_memory_base_clear(&state->data_memory_base_regs[reg_index]);
  } else if (reg_kind == 2U) {
    typed_reg_value_clear(&state->addr_regs[reg_index]);
    state->app_addr_regs[reg_index].known = 0U;
    state->app_addr_regs[reg_index].displacement = 0;
    state->app_addr_regs[reg_index].base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
    typed_memory_base_clear(&state->memory_base_regs[reg_index]);
    typed_state_clear_io_request_setup(state, reg_index);
    typed_state_clear_addr_alias_for_reg(state, reg_index);
    typed_state_clear_base_slots_for_base(state, reg_index);
  }
}

static void typed_state_set_reg(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index,
    const AmigaOsCallOutputInfo *output, const M68kRenderTypedProvenance *provenance) {
  if (state == NULL || output == NULL || reg_index >= 8U || !amiga_output_has_typed_info(output)) return;
  if (reg_kind == 1U) {
    state->data_regs[reg_index].known = 1U;
    state->data_regs[reg_index].type_conflicted = 0U;
    state->data_regs[reg_index].output = output;
    state->data_regs[reg_index].struct_id = output->struct_id;
    state->data_regs[reg_index].conflict_struct_id = AMIGA_OS_STRUCT_ID_NONE;
    state->data_regs[reg_index].array_element_count = 0U;
    state->data_regs[reg_index].array_element_index = 0U;
    state->data_regs[reg_index].byte_cursor = 0;
    typed_origin_clear(&state->data_regs[reg_index].origin);
    state->data_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
    state->data_app_addr_regs[reg_index].known = 0U;
    state->data_app_addr_regs[reg_index].displacement = 0;
    state->data_app_addr_regs[reg_index].base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
    typed_memory_base_clear(&state->data_memory_base_regs[reg_index]);
  } else if (reg_kind == 2U) {
    state->addr_regs[reg_index].known = 1U;
    state->addr_regs[reg_index].type_conflicted = 0U;
    state->addr_regs[reg_index].output = output;
    state->addr_regs[reg_index].struct_id = output->struct_id;
    state->addr_regs[reg_index].conflict_struct_id = AMIGA_OS_STRUCT_ID_NONE;
    state->addr_regs[reg_index].array_element_count = 0U;
    state->addr_regs[reg_index].array_element_index = 0U;
    state->addr_regs[reg_index].byte_cursor = 0;
    typed_origin_clear(&state->addr_regs[reg_index].origin);
    state->addr_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
    state->app_addr_regs[reg_index].known = 0U;
    state->app_addr_regs[reg_index].displacement = 0;
    state->app_addr_regs[reg_index].base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
    typed_memory_base_clear(&state->memory_base_regs[reg_index]);
    typed_state_clear_addr_alias_for_reg(state, reg_index);
  }
}

static void typed_state_set_reg_struct_id(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index,
    uint16_t struct_id, const M68kRenderTypedProvenance *provenance) {
  if (state == NULL || reg_index >= 8U || struct_id == AMIGA_OS_STRUCT_ID_NONE) return;
  if (reg_kind == 1U) {
    state->data_regs[reg_index].known = 1U;
    state->data_regs[reg_index].type_conflicted = 0U;
    state->data_regs[reg_index].output = NULL;
    state->data_regs[reg_index].struct_id = struct_id;
    state->data_regs[reg_index].conflict_struct_id = AMIGA_OS_STRUCT_ID_NONE;
    state->data_regs[reg_index].array_element_count = 0U;
    state->data_regs[reg_index].array_element_index = 0U;
    state->data_regs[reg_index].byte_cursor = 0;
    typed_origin_clear(&state->data_regs[reg_index].origin);
    state->data_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
    state->data_app_addr_regs[reg_index].known = 0U;
    state->data_app_addr_regs[reg_index].displacement = 0;
    state->data_app_addr_regs[reg_index].base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
    typed_memory_base_clear(&state->data_memory_base_regs[reg_index]);
  } else if (reg_kind == 2U) {
    state->addr_regs[reg_index].known = 1U;
    state->addr_regs[reg_index].type_conflicted = 0U;
    state->addr_regs[reg_index].output = NULL;
    state->addr_regs[reg_index].struct_id = struct_id;
    state->addr_regs[reg_index].conflict_struct_id = AMIGA_OS_STRUCT_ID_NONE;
    state->addr_regs[reg_index].array_element_count = 0U;
    state->addr_regs[reg_index].array_element_index = 0U;
    state->addr_regs[reg_index].byte_cursor = 0;
    typed_origin_clear(&state->addr_regs[reg_index].origin);
    state->addr_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
    state->app_addr_regs[reg_index].known = 0U;
    state->app_addr_regs[reg_index].displacement = 0;
    state->app_addr_regs[reg_index].base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
    typed_memory_base_clear(&state->memory_base_regs[reg_index]);
    typed_state_clear_addr_alias_for_reg(state, reg_index);
  }
}

static const char *typed_policy_seed_struct_name(const M68kAnalysisRegisterSeed *seed) {
  if (seed == NULL) return NULL;
  if (seed->type_name[0] != '\0') return seed->type_name;
  if (seed->name[0] != '\0') return seed->name;
  return NULL;
}

typedef struct M68kRenderResolvedStructField {
  int16_t offset;
  uint16_t size;
  uint8_t inherited;
  uint8_t nested;
  char root_struct_name[64];
  char owner_struct_name[64];
  char field_name[64];
  char field_expr[M68K_IR_SYMBOL_NAME_SIZE];
} M68kRenderResolvedStructField;

static uint16_t amiga_struct_size_for_struct_id(uint16_t struct_id);
static uint16_t lookup_policy_struct_size_by_id(const M68kAnalysisPolicy *policy, uint16_t struct_id);
static int render_lookup_add_typed_access_by_names(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t operand_index, uint8_t base_reg, int16_t displacement, uint16_t struct_size,
  int16_t array_element_addend, int32_t base_cursor, uint16_t field_byte_offset,
  const M68kRenderResolvedStructField *field,
  const M68kRenderTypedProvenance *provenance, const M68kAddressValueTableOriginIR *table_origin);
static int render_lookup_add_unresolved_typed_access_by_names(M68kRenderLookup *lookup, size_t section_index,
  uint32_t offset, uint8_t operand_index, uint8_t base_reg, int32_t displacement, const char *root_struct_name,
  uint16_t struct_size, uint8_t access_size, uint8_t classification, uint16_t container_candidate_count,
  const char *container_struct_name, const char *container_field_expr, uint8_t refinement_applied,
  const char *refined_struct_name, const M68kRenderTypedProvenance *provenance);
static int render_lookup_pointer_value_to_object_source_location(const M68kRenderLookup *lookup, uint32_t value,
  size_t *out_section_index, uint32_t *out_source_offset);

static int policy_custom_struct_index_from_id(uint16_t struct_id, uint16_t *out_index) {
  uint32_t index;
  if (out_index != NULL) *out_index = 0U;
  if (struct_id < M68K_ANALYSIS_CUSTOM_STRUCT_ID_BASE) return 0;
  index = (uint32_t)struct_id - M68K_ANALYSIS_CUSTOM_STRUCT_ID_BASE;
  if (index >= M68K_ANALYSIS_CUSTOM_STRUCT_LIMIT) return 0;
  if (out_index != NULL) *out_index = (uint16_t)index;
  return 1;
}

static const M68kAnalysisCustomStruct *lookup_policy_custom_struct_by_id(const M68kAnalysisPolicy *policy,
    uint16_t struct_id) {
  uint16_t index;
  if (policy == NULL || policy->custom_structs == NULL || !policy_custom_struct_index_from_id(struct_id, &index) ||
      index >= policy->custom_struct_count) {
    return NULL;
  }
  return &policy->custom_structs[index];
}

static uint16_t lookup_policy_struct_id_by_name(const M68kAnalysisPolicy *policy, const char *struct_name) {
  uint16_t index;
  uint16_t platform_struct_id;
  if (struct_name == NULL || struct_name[0] == '\0') return AMIGA_OS_STRUCT_ID_NONE;
  if (policy != NULL && policy->custom_structs != NULL) {
    for (index = 0U; index < policy->custom_struct_count && index < M68K_ANALYSIS_CUSTOM_STRUCT_LIMIT; ++index) {
      if (strcmp(policy->custom_structs[index].name, struct_name) == 0)
        return (uint16_t)(M68K_ANALYSIS_CUSTOM_STRUCT_ID_BASE + index);
    }
  }
  platform_struct_id = amiga_os_name_id(M68K_PLATFORM_NAME_STRUCT, struct_name);
  if (amiga_os_name(M68K_PLATFORM_NAME_STRUCT, platform_struct_id) != NULL) return platform_struct_id;
  return AMIGA_OS_STRUCT_ID_NONE;
}

static void typed_state_set_reg_struct_id_array(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index,
    uint16_t struct_id, uint16_t element_count, uint16_t element_index,
  const M68kRenderTypedProvenance *provenance) {
  if (element_count == 0U || element_index >= element_count) {
    typed_state_set_reg_struct_id(state, reg_kind, reg_index, struct_id, provenance);
    return;
  }
  typed_state_set_reg_struct_id(state, reg_kind, reg_index, struct_id, provenance);
  if (reg_kind == M68K_ANALYSIS_REGISTER_DATA) {
    state->data_regs[reg_index].array_element_count = element_count;
    state->data_regs[reg_index].array_element_index = element_index;
  } else if (reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS) {
    state->addr_regs[reg_index].array_element_count = element_count;
    state->addr_regs[reg_index].array_element_index = element_index;
  }
}

static const char *lookup_policy_struct_name_by_id(const M68kAnalysisPolicy *policy, uint16_t struct_id) {
  const M68kAnalysisCustomStruct *custom_struct;
  const char *platform_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id);
  if (platform_name != NULL && platform_name[0] != '\0') return platform_name;
  custom_struct = lookup_policy_custom_struct_by_id(policy, struct_id);
  return custom_struct != NULL && custom_struct->name[0] != '\0' ? custom_struct->name : NULL;
}

/* Field seeds describe a cell in a root object, not an object starting at the
   cell's address. Require one declared field with the seed's complete width. */
static int lookup_policy_static_data_field_offset(const M68kAnalysisPolicy *policy, uint16_t struct_id,
    const M68kAnalysisStructuredDataItem *item, uint16_t struct_size, uint32_t *out_offset) {
  const M68kAnalysisCustomStruct *custom_struct = lookup_policy_custom_struct_by_id(policy, struct_id);
  uint32_t matched_offset = 0U, matched_size = 0U;
  unsigned matches = 0U;
  if (custom_struct != NULL) {
    uint16_t index;
    for (index = 0U; index < custom_struct->field_count && index < M68K_ANALYSIS_CUSTOM_STRUCT_FIELD_LIMIT; ++index) {
      const M68kAnalysisCustomStructField *field = &custom_struct->fields[index];
      if (strcmp(field->name, item->field_name) != 0) continue;
      if (item->field_type[0] != '\0' && strcmp(item->field_type, field->type_name) != 0) return 0;
      matched_offset = field->offset;
      matched_size = field->size;
      ++matches;
    }
  } else {
    uint32_t offset;
    for (offset = 0U; offset < struct_size && offset <= INT16_MAX; ++offset) {
      AmigaOsResolvedStructFieldInfo field;
      const char *name;
      const AmigaOsStructFieldInfo *declared;
      const char *type_name;
      if (!amiga_os_resolve_struct_field_by_struct_id(struct_id, (int16_t)offset, 0, &field) ||
          field.offset != (int16_t)offset) continue;
      name = amiga_os_name(M68K_PLATFORM_NAME_FIELD, field.field_id);
      if (name == NULL || strcmp(name, item->field_name) != 0) continue;
      declared = amiga_os_find_struct_field_by_field_id(field.field_id);
      type_name = declared != NULL ? amiga_os_name(M68K_PLATFORM_NAME_TYPE, declared->field_type_id) : NULL;
      if (item->field_type[0] != '\0' && (type_name == NULL || strcmp(item->field_type, type_name) != 0)) return 0;
      matched_offset = offset;
      matched_size = field.size;
      ++matches;
    }
  }
  if (matches != 1U || matched_size == 0U || item->size != matched_size ||
      matched_offset > INT32_MAX || (uint64_t)matched_offset + matched_size > struct_size) return 0;
  *out_offset = matched_offset;
  return 1;
}

static int typed_operand_is_runtime_only(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset, uint32_t operand_index) {
  const M68kAnalysisManualRepresentation *representation =
    lookup_manual_operand_representation(lookup, section_index, offset, operand_index);
  if (lookup == NULL || lookup->policy == NULL || representation == NULL ||
      representation->style_id != M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL ||
      representation->has_source_symbol || representation->target_equate_index == 0U ||
      representation->target_equate_index > lookup->policy->target_equate_count) return 0;
  /* A runtime-only workspace may numerically overlap a source image's load
   * view. The explicit domain does not establish that image's contents/type. */
  return lookup->policy->target_equates[representation->target_equate_index - 1U].address_domain != 0U;
}

/* A structured-data item can describe an object whose address is materialised
   at either its start or a proven interior byte. The cursor records that
   interior position relative to the root object for later field resolution. */
static uint16_t lookup_policy_struct_id_for_static_data_target(const M68kAnalysisPolicy *policy,
    size_t section_index, uint32_t offset, uint16_t *out_array_element_count,
    uint16_t *out_array_element_index, int32_t *out_byte_cursor, uint16_t *out_conflict_struct_id) {
  size_t index;
  uint16_t resolved_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  uint16_t resolved_array_element_count = 0U, resolved_array_element_index = 0U;
  int32_t resolved_byte_cursor = 0;
  if (out_array_element_count != NULL) *out_array_element_count = 0U;
  if (out_array_element_index != NULL) *out_array_element_index = 0U;
  if (out_byte_cursor != NULL) *out_byte_cursor = 0;
  if (out_conflict_struct_id != NULL) *out_conflict_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (policy == NULL || policy->structured_data_items == NULL) return AMIGA_OS_STRUCT_ID_NONE;
  for (index = 0U; index < policy->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &policy->structured_data_items[index];
    uint16_t struct_id;
    uint16_t struct_size, array_element_count = 0U, array_element_index = 0U;
    int32_t byte_cursor;
    uint64_t item_end;
    if (!item->has_section_index || item->section_index != section_index || item->size == 0U) continue;
    item_end = (uint64_t)item->offset + item->size;
    if (offset < item->offset || (uint64_t)offset >= item_end) continue;
    struct_id = item->struct_id != AMIGA_OS_STRUCT_ID_NONE ? item->struct_id :
      lookup_policy_struct_id_by_name(policy, item->struct_name);
    if (lookup_policy_struct_name_by_id(policy, struct_id) == NULL) continue;
    struct_size = lookup_policy_struct_size_by_id(policy, struct_id);
    byte_cursor = (int32_t)(offset - item->offset);
    if (item->field_name[0] != '\0') {
      uint32_t field_offset;
      if (!lookup_policy_static_data_field_offset(policy, struct_id, item, struct_size, &field_offset)) {
        /* An invalid field declaration must not fall back to a root at zero,
           including when another overlapping seed supplies a trusted type. */
        if (out_conflict_struct_id != NULL) *out_conflict_struct_id = struct_id;
        return resolved_struct_id != AMIGA_OS_STRUCT_ID_NONE ? resolved_struct_id : struct_id;
      }
      byte_cursor += (int32_t)field_offset;
    } else if (struct_size != 0U && item->size >= struct_size && item->size % struct_size == 0U &&
        item->size / struct_size <= UINT16_MAX) {
      array_element_count = (uint16_t)(item->size / struct_size);
      array_element_index = (uint16_t)((uint32_t)byte_cursor / struct_size);
      byte_cursor %= struct_size;
    }
    if (resolved_struct_id != AMIGA_OS_STRUCT_ID_NONE &&
        (resolved_struct_id != struct_id || resolved_array_element_count != array_element_count ||
         resolved_array_element_index != array_element_index || resolved_byte_cursor != byte_cursor)) {
      if (out_conflict_struct_id != NULL) *out_conflict_struct_id = struct_id;
      return resolved_struct_id;
    }
    resolved_struct_id = struct_id;
    resolved_array_element_count = array_element_count;
    resolved_array_element_index = array_element_index;
    resolved_byte_cursor = byte_cursor;
  }
  if (out_array_element_count != NULL) *out_array_element_count = resolved_array_element_count;
  if (out_array_element_index != NULL) *out_array_element_index = resolved_array_element_index;
  if (out_byte_cursor != NULL) *out_byte_cursor = resolved_byte_cursor;
  return resolved_struct_id;
}

static uint16_t lookup_policy_struct_size_by_id(const M68kAnalysisPolicy *policy, uint16_t struct_id) {
  const M68kAnalysisCustomStruct *custom_struct = lookup_policy_custom_struct_by_id(policy, struct_id);
  if (custom_struct != NULL)
    return custom_struct->size > UINT16_MAX ? UINT16_MAX : (uint16_t)custom_struct->size;
  return amiga_struct_size_for_struct_id(struct_id);
}

static int lookup_policy_resolve_struct_field(const M68kAnalysisPolicy *policy, uint16_t struct_id,
    int16_t displacement, uint8_t access_size, M68kRenderResolvedStructField *out_field) {
  const M68kAnalysisCustomStruct *custom_struct = lookup_policy_custom_struct_by_id(policy, struct_id);
  const char *struct_name;
  if (out_field != NULL) memset(out_field, 0, sizeof(*out_field));
  if (custom_struct != NULL) {
    uint16_t field_index;
    for (field_index = 0U; field_index < custom_struct->field_count &&
         field_index < M68K_ANALYSIS_CUSTOM_STRUCT_FIELD_LIMIT; ++field_index) {
      const M68kAnalysisCustomStructField *field = &custom_struct->fields[field_index];
      if (field->size == 0U || field->name[0] == '\0') continue;
      if (field->offset != (uint32_t)displacement &&
          (access_size == 0U || access_size >= field->size || (uint32_t)displacement < field->offset ||
           (uint64_t)(uint32_t)displacement + access_size > (uint64_t)field->offset + field->size)) continue;
      if (out_field != NULL) {
        out_field->offset = (int16_t)field->offset;
        out_field->size = field->size > UINT16_MAX ? UINT16_MAX : (uint16_t)field->size;
        snprintf(out_field->root_struct_name, sizeof(out_field->root_struct_name), "%s", custom_struct->name);
        snprintf(out_field->owner_struct_name, sizeof(out_field->owner_struct_name), "%s", custom_struct->name);
        snprintf(out_field->field_name, sizeof(out_field->field_name), "%s", field->name);
        if (snprintf(out_field->field_expr, sizeof(out_field->field_expr), "%s_%s",
            custom_struct->name, field->name) >= (int)sizeof(out_field->field_expr)) {
          return 0;
        }
      }
      return 1;
    }
    return 0;
  }
  struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id);
  if (struct_name != NULL && struct_name[0] != '\0') {
    AmigaOsResolvedStructFieldInfo field;
    const char *owner_struct_name;
    const char *field_name;
    if (!amiga_os_resolve_struct_field_by_struct_id(struct_id, displacement, 0, &field)) return 0;
    owner_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, field.owner_struct_id);
    field_name = amiga_os_name(M68K_PLATFORM_NAME_FIELD, field.field_id);
    if (owner_struct_name == NULL || field_name == NULL || out_field == NULL ||
        !amiga_os_resolve_struct_field_symbol_expr_by_struct_id(struct_id, displacement, 0,
          out_field->field_expr, sizeof(out_field->field_expr))) {
      return 0;
    }
    out_field->offset = field.offset;
    out_field->size = field.size;
    out_field->inherited = field.inherited;
    out_field->nested = field.nested;
    snprintf(out_field->root_struct_name, sizeof(out_field->root_struct_name), "%s", struct_name);
    snprintf(out_field->owner_struct_name, sizeof(out_field->owner_struct_name), "%s", owner_struct_name);
    snprintf(out_field->field_name, sizeof(out_field->field_name), "%s", field_name);
    return 1;
  }
  return 0;
}

static void typed_state_apply_policy_register_seeds(M68kRenderTypedState *state,
    const M68kAnalysisPolicy *policy, size_t section_index, uint32_t offset) {
  uint16_t index;
  if (state == NULL || policy == NULL) return;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    const char *struct_name;
    uint16_t struct_id;
    M68kRenderTypedProvenance provenance;
    if (seed->has_section_index && seed->section_index != (uint32_t)section_index) continue;
    if (seed->has_entry_offset) {
      if (seed->entry_offset != offset) continue;
    } else if (!policy->has_entry_offset || section_index != 0U || policy->entry_offset != offset) continue;
    if ((seed->kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR &&
         seed->kind != M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE) ||
        seed->reg_index >= 8U ||
        (seed->reg_kind != M68K_ANALYSIS_REGISTER_DATA &&
         seed->reg_kind != M68K_ANALYSIS_REGISTER_ADDRESS)) {
      continue;
    }
    struct_name = typed_policy_seed_struct_name(seed);
    if (struct_name == NULL || struct_name[0] == '\0') continue;
    struct_id = lookup_policy_struct_id_by_name(policy, struct_name);
    if (lookup_policy_struct_name_by_id(policy, struct_id) == NULL) continue;
    provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_POLICY_SEED, section_index, offset);
    typed_state_set_reg_struct_id_array(state, seed->reg_kind, seed->reg_index, struct_id,
      seed->array_element_count, 0U, &provenance);
    /* The seed establishes an independent typed root at this instruction.
     * Retaining the previous value's table origin lets canonical table
     * reconciliation discard fields supported by the seed itself. Ordinary
     * table-derived values still require their canonical binding. */
    if (seed->reg_kind == M68K_ANALYSIS_REGISTER_DATA)
      typed_table_origin_clear(&state->data_regs[seed->reg_index].table_origin);
    else
      typed_table_origin_clear(&state->addr_regs[seed->reg_index].table_origin);
  }
}

/* A long immediate is not an address merely because it fits the address
 * space.  Preserve its exact identity through ordinary data flow, then
 * promote it only when a typed destination proves address intent. */
static void typed_stored_value_set_raw_long(M68kRenderTypedStoredValue *value, uint32_t raw_value) {
  if (value == NULL) return;
  value->raw_long_value_known = 1U;
  value->raw_long_value = raw_value;
  value->raw_long_candidate_count = 1U;
  value->raw_long_candidates[0] = raw_value;
  typed_stored_value_update_known(value);
}

/* Partial transfers do not establish a complete longword constant/address. */
static void typed_stored_value_forget_concrete_long(M68kRenderTypedStoredValue *value) {
  value->raw_long_value_known = value->raw_long_candidate_count = 0U;
  value->raw_long_value = 0U; memset(value->raw_long_candidates, 0, sizeof(value->raw_long_candidates));
  value->pointer_value_known = value->pointer_candidate_count = value->pointer_target_known = 0U;
  value->pointer_value = value->pointer_target_offset = 0U; value->pointer_target_section_index = 0U;
  memset(value->pointer_candidates, 0, sizeof(value->pointer_candidates));
  value->address_value_candidate_overflow = 0U;
  typed_table_origin_clear(&value->table_origin);
  typed_stored_value_update_known(value);
}

static void typed_stored_value_activate_address(M68kRenderTypedStoredValue *value) {
  if (value == NULL || value->pointer_value_known != 0U || value->raw_long_value_known == 0U) return;
  value->pointer_value_known = 1U;
  value->pointer_value = value->raw_long_value;
  value->pointer_candidate_count = value->raw_long_candidate_count;
  memcpy(value->pointer_candidates, value->raw_long_candidates, sizeof(value->pointer_candidates));
  typed_stored_value_update_known(value);
}

static void typed_state_set_stack_slot(M68kRenderTypedState *state, int16_t displacement,
    uint8_t caller_save_temporary, uint8_t abi_stack_convention, const M68kRenderTypedStoredValue *value,
    const M68kRenderTypedMemoryBaseValue *memory_base);
static const M68kRenderTypedStoredValue *typed_state_stack_slot_value(const M68kRenderTypedState *state,
    int16_t displacement);
static const M68kRenderTypedMemoryBaseValue *typed_state_stack_slot_memory_base(
    const M68kRenderTypedState *state, int16_t displacement);
static const M68kRenderTypedStackSlot *typed_state_stack_slot_for_abi_location(
    const M68kRenderTypedState *state, int16_t displacement, uint8_t abi_stack_convention);

static void typed_state_apply_function_summary_inputs(M68kRenderTypedState *state,
    const M68kAnalysisPolicy *policy, const M68kAnalysisFunctionSummary *summary, size_t section_index,
    uint32_t offset) {
  uint8_t input_index;
  M68kRenderTypedProvenance provenance;
  if (state == NULL || policy == NULL || summary == NULL) return;
  provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_POLICY_SEED, section_index, offset);
  for (input_index = 0U; input_index < summary->input_count; ++input_index) {
    const M68kAnalysisFunctionSummaryInput *input = &summary->inputs[input_index];
    uint16_t struct_id;
    if (input->seed_kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR) continue;
    struct_id = lookup_policy_struct_id_by_name(policy, input->struct_name);
    if (lookup_policy_struct_name_by_id(policy, struct_id) == NULL) continue;
    if ((input->location.kind == M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER ||
         input->location.kind == M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER_TUPLE) &&
        input->location.register_count != 0U) {
      uint8_t member_index;
      for (member_index = 0U; member_index < input->location.register_count; ++member_index) {
        const M68kFunctionSummaryAbiRegisterMember *member = &input->location.registers[member_index];
        if (member->register_index >= 8U ||
            (member->register_kind != M68K_ANALYSIS_REGISTER_DATA &&
             member->register_kind != M68K_ANALYSIS_REGISTER_ADDRESS)) continue;
        typed_state_set_reg_struct_id(state, member->register_kind, member->register_index, struct_id, &provenance);
      }
    } else if (input->location.kind == M68K_FUNCTION_SUMMARY_ABI_LOCATION_STACK && input->location.width == 4U &&
        input->location.stack_offset >= INT16_MIN && input->location.stack_offset <= INT16_MAX) {
      M68kRenderTypedStoredValue value;
      typed_stored_value_clear(&value);
      value.struct_id = struct_id;
      value.provenance = provenance;
      typed_stored_value_update_known(&value);
      typed_state_set_stack_slot(state, (int16_t)input->location.stack_offset, 0U,
        input->location.stack_convention, &value, NULL);
    }
  }
}

static void typed_state_apply_function_summaries(M68kRenderTypedState *state,
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  const M68kAnalysisPolicy *policy;
  uint16_t summary_index;
  if (state == NULL || lookup == NULL || (policy = lookup->policy) == NULL || lookup->object == NULL) return;
  for (summary_index = 0U; summary_index < policy->function_summary_count &&
       summary_index < M68K_ANALYSIS_FUNCTION_SUMMARY_LIMIT; ++summary_index) {
    const M68kAnalysisFunctionSummary *summary = &policy->function_summaries[summary_index];
    const M68kSection *table_section;
    uint32_t cursor;
    if (!summary->has_section_index || summary->section_index >= lookup->object->section_count) continue;
    if (summary->callable_kind == M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT) {
      if (summary->section_index == section_index && summary->entry_offset == offset)
        typed_state_apply_function_summary_inputs(state, policy, summary, section_index, offset);
      continue;
    }
    if (summary->callable_kind != M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_CALLBACK_TABLE || summary->entry_count == 0U)
      continue;
    table_section = &lookup->object->sections[summary->section_index];
    if (table_section->data == NULL || summary->table_offset > table_section->size ||
        summary->entry_count > (table_section->size - summary->table_offset) / 4U) continue;
    for (cursor = 0U; cursor < summary->entry_count; ++cursor) {
      size_t target_section_index = 0U;
      uint32_t target_offset = 0U;
      uint32_t value = m68k_read_u32be(table_section->data + summary->table_offset + cursor * 4U);
      uint16_t range_index;
      uint8_t resolved = 0U;
      for (range_index = 0U; range_index < policy->runtime_range_count &&
           range_index < M68K_ANALYSIS_RUNTIME_RANGE_LIMIT; ++range_index) {
        const M68kAnalysisRuntimeRange *range = &policy->runtime_ranges[range_index];
        uint32_t delta;
        if (!range->has_section_index || range->section_index >= lookup->object->section_count ||
            value < range->runtime_address) continue;
        delta = value - range->runtime_address;
        if (delta >= range->size || range->offset > UINT32_MAX - delta) continue;
        target_section_index = range->section_index;
        target_offset = range->offset + delta;
        resolved = 1U;
        break;
      }
      if (!resolved && !render_lookup_pointer_value_to_object_source_location(lookup, value, &target_section_index,
            &target_offset)) {
        continue;
      }
      if (target_section_index != section_index || target_offset != offset) {
        continue;
      }
      typed_state_apply_function_summary_inputs(state, policy, summary, section_index, offset);
      break;
    }
  }
}

/* A target-declared result is deliberately narrower than an inferred callee
 * effect: it only applies at the exact direct-call boundary named by the
 * policy.  Keep the lookup separate from effect-summary selection so a
 * transient inferred effect can never manufacture a configured return. */
static const M68kAnalysisFunctionSummary *lookup_configured_direct_function_summary(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t entry_offset) {
  uint16_t summary_index;
  const M68kAnalysisPolicy *policy;
  if (lookup == NULL || (policy = lookup->policy) == NULL) return NULL;
  for (summary_index = 0U; summary_index < policy->function_summary_count &&
       summary_index < M68K_ANALYSIS_FUNCTION_SUMMARY_LIMIT; ++summary_index) {
    const M68kAnalysisFunctionSummary *summary = &policy->function_summaries[summary_index];
    if (summary->has_section_index &&
        summary->callable_kind == M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT &&
        summary->section_index == section_index && summary->entry_offset == entry_offset) {
      return summary;
    }
  }
  return NULL;
}

static const M68kRenderTypedRegValue *typed_state_register_value(const M68kRenderTypedState *state,
    uint8_t register_kind, uint8_t register_index) {
  if (state == NULL || register_index >= 8U) return NULL;
  if (register_kind == M68K_ANALYSIS_REGISTER_DATA) return &state->data_regs[register_index];
  if (register_kind == M68K_ANALYSIS_REGISTER_ADDRESS) return &state->addr_regs[register_index];
  return NULL;
}

static void typed_state_copy_register_identity_result(M68kRenderTypedState *state,
    const M68kRenderTypedState *before_call, uint8_t destination_kind, uint8_t destination_index,
    uint8_t source_kind, uint8_t source_index, uint16_t input_struct_id) {
  const M68kRenderTypedRegValue *source;
  if (state == NULL || before_call == NULL || destination_index >= 8U || source_index >= 8U ||
      (destination_kind != M68K_ANALYSIS_REGISTER_DATA && destination_kind != M68K_ANALYSIS_REGISTER_ADDRESS) ||
      (source_kind != M68K_ANALYSIS_REGISTER_DATA && source_kind != M68K_ANALYSIS_REGISTER_ADDRESS)) return;
  source = typed_state_register_value(before_call, source_kind, source_index);
  if (source == NULL) return;
  typed_state_clear_reg(state, destination_kind, destination_index);
  if (destination_kind == M68K_ANALYSIS_REGISTER_DATA) {
    state->data_regs[destination_index] = *source;
    state->data_app_addr_regs[destination_index] = source_kind == M68K_ANALYSIS_REGISTER_DATA ?
      before_call->data_app_addr_regs[source_index] : before_call->app_addr_regs[source_index];
    state->data_memory_base_regs[destination_index] = source_kind == M68K_ANALYSIS_REGISTER_DATA ?
      before_call->data_memory_base_regs[source_index] : before_call->memory_base_regs[source_index];
  } else {
    state->addr_regs[destination_index] = *source;
    state->app_addr_regs[destination_index] = source_kind == M68K_ANALYSIS_REGISTER_DATA ?
      before_call->data_app_addr_regs[source_index] : before_call->app_addr_regs[source_index];
    state->memory_base_regs[destination_index] = source_kind == M68K_ANALYSIS_REGISTER_DATA ?
      before_call->data_memory_base_regs[source_index] : before_call->memory_base_regs[source_index];
  }
  /* The result has the input value, but it is not an alias claim about a
   * register that the callee may have clobbered. */
  if (destination_kind == M68K_ANALYSIS_REGISTER_ADDRESS)
    typed_state_clear_addr_alias_for_reg(state, destination_index);
  if (input_struct_id != AMIGA_OS_STRUCT_ID_NONE)
    typed_state_set_reg_struct_id(state, destination_kind, destination_index, input_struct_id,
      &source->provenance);
}

static void typed_state_apply_function_summary_results(M68kRenderTypedState *state,
    const M68kRenderTypedState *before_call, const M68kRenderLookup *lookup,
    const M68kAnalysisFunctionSummary *summary, size_t section_index, uint32_t offset) {
  uint8_t result_index;
  if (state == NULL || before_call == NULL || lookup == NULL || lookup->policy == NULL) return;
  if (summary == NULL || summary->result_contract_invalid != 0U) return;
  for (result_index = 0U; result_index < summary->result_count &&
       result_index < M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_LIMIT; ++result_index) {
    const M68kAnalysisFunctionSummaryResult *result = &summary->results[result_index];
    const M68kAnalysisFunctionSummaryInput *input;
    uint8_t member_index;
    uint16_t input_struct_id;
    if (result->kind == M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_PLATFORM_OUTPUT) {
      const AmigaOsLibraryVectorInfo *vector;
      M68kRenderTypedProvenance api_provenance;
      if (result->location.kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER ||
          result->location.width != 4U || result->location.register_count != 1U) continue;
      vector = amiga_os_find_library_vector_by_ids(result->platform_library_id,
        result->platform_function_id, result->platform_output_id);
      if (vector == NULL || !amiga_output_has_typed_info(&vector->output)) continue;
      api_provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_API_OUTPUT, section_index, offset);
      typed_state_set_reg(state, result->location.registers[0].register_kind,
        result->location.registers[0].register_index, &vector->output, &api_provenance);
      continue;
    }
    if (result->kind != M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_IDENTITY_INPUT ||
        result->input_index >= summary->input_count) continue;
    input = &summary->inputs[result->input_index];
    if ((input->seed_kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR &&
         input->seed_kind != M68K_ANALYSIS_REGISTER_SEED_ABI_POINTER) ||
        input->location.kind != result->location.kind || input->location.width != result->location.width ||
        input->location.register_count != result->location.register_count) continue;
    input_struct_id = lookup_policy_struct_id_by_name(lookup->policy, input->struct_name);
    if (input->seed_kind == M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR && input_struct_id == AMIGA_OS_STRUCT_ID_NONE)
      continue;
    if (input->location.kind == M68K_FUNCTION_SUMMARY_ABI_LOCATION_STACK) {
      const M68kRenderTypedStackSlot *source_slot;
      if (input->location.width != 4U || input->location.stack_offset < INT16_MIN ||
          input->location.stack_offset > INT16_MAX || result->location.stack_offset < INT16_MIN ||
          result->location.stack_offset > INT16_MAX) continue;
      /* The caller's ordinary stack store has no ABI role until this
       * contract interprets it.  Snapshot that physical slot before callee
       * effects, then materialize a separate caller-result slot afterwards. */
      source_slot = typed_state_stack_slot_for_abi_location(before_call, (int16_t)input->location.stack_offset,
        input->location.stack_convention);
      if (source_slot == NULL || source_slot->value.struct_id != input_struct_id) continue;
      typed_state_set_stack_slot(state, (int16_t)result->location.stack_offset, 0U,
        result->location.stack_convention, &source_slot->value, &source_slot->memory_base);
      continue;
    }
    if (input->location.kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER &&
        input->location.kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER_TUPLE) continue;
    for (member_index = 0U; member_index < input->location.register_count; ++member_index) {
      const M68kRenderTypedRegValue *source_value = typed_state_register_value(before_call,
        input->location.registers[member_index].register_kind, input->location.registers[member_index].register_index);
      if (source_value == NULL || source_value->type_conflicted != 0U ||
          (input->seed_kind == M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR &&
           source_value->struct_id != AMIGA_OS_STRUCT_ID_NONE && source_value->struct_id != input_struct_id)) break;
    }
    if (member_index != input->location.register_count) continue;
    for (member_index = 0U; member_index < input->location.register_count; ++member_index) {
      typed_state_copy_register_identity_result(state, before_call,
        result->location.registers[member_index].register_kind, result->location.registers[member_index].register_index,
        input->location.registers[member_index].register_kind, input->location.registers[member_index].register_index,
        input_struct_id);
    }
  }
}

static void typed_state_clear_all(M68kRenderTypedState *state) {
  size_t index;
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
  for (index = 0U; index < 8U; ++index) {
    state->data_regs[index].struct_id = AMIGA_OS_STRUCT_ID_NONE;
    state->addr_regs[index].struct_id = AMIGA_OS_STRUCT_ID_NONE;
  }
}

static void typed_state_clear_non_caller_save_stack_slots(M68kRenderTypedState *state) {
  size_t index;
  if (state == NULL) return;
  for (index = 0U; index < state->stack_slot_count;) {
    if (state->stack_slots[index].known != 0U && state->stack_slots[index].caller_save_temporary != 0U) {
      ++index;
      continue;
    }
    state->stack_slots[index] = state->stack_slots[state->stack_slot_count - 1U];
    --state->stack_slot_count;
  }
}

/* An opaque memory/escape component invalidates cached values loaded from
 * caller-visible storage.  It does not, by itself, invalidate a register
 * identity whose independent register partition proves it was preserved. */
static void typed_state_invalidate_opaque_memory_effects(M68kRenderTypedState *state) {
  uint8_t reg;
  if (state == NULL) return;
  typed_state_clear_non_caller_save_stack_slots(state);
  state->base_slot_count = 0U;
  state->field_slot_count = 0U;
  for (reg = 0U; reg < 8U; ++reg) {
    if (state->data_regs[reg].origin.kind != M68K_RENDER_TYPED_ORIGIN_NONE)
      typed_state_invalidate_memory_derived_reg(state, M68K_ANALYSIS_REGISTER_DATA, reg);
    if (state->addr_regs[reg].origin.kind != M68K_RENDER_TYPED_ORIGIN_NONE)
      typed_state_invalidate_memory_derived_reg(state, M68K_ANALYSIS_REGISTER_ADDRESS, reg);
    typed_state_clear_io_request_setup(state, reg);
  }
}

static uint8_t function_summary_register_effect(const M68kAnalysisFunctionSummary *summary,
    uint8_t register_kind, uint8_t register_index) {
  uint8_t effect_index;
  if (summary == NULL || register_index >= 8U) return M68K_FUNCTION_SUMMARY_LOCATION_UNKNOWN;
  for (effect_index = 0U; effect_index < summary->location_effect_count; ++effect_index) {
    const M68kFunctionSummaryLocationEffectIR *effect = &summary->location_effects[effect_index];
    if (effect->location.kind == M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER &&
        effect->location.register_count == 1U && effect->location.registers[0].register_kind == register_kind &&
        effect->location.registers[0].register_index == register_index) return effect->effect;
  }
  return M68K_FUNCTION_SUMMARY_LOCATION_UNKNOWN;
}

/* The generated ABI, bounded local-body proof, and callback aggregate all
 * write the same exhaustive register partition. */
static void function_summary_set_register_partition(M68kAnalysisFunctionSummary *summary,
    uint8_t preserved_data, uint8_t preserved_address) {
  uint8_t bit;
  if (summary == NULL) return;
  summary->register_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT;
  summary->memory_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT;
  summary->escape_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT;
  summary->location_effect_count = 0U;
  for (bit = 0U; bit < 8U; ++bit) {
    M68kFunctionSummaryLocationEffectIR *data_effect = &summary->location_effects[summary->location_effect_count++];
    M68kFunctionSummaryLocationEffectIR *address_effect = &summary->location_effects[summary->location_effect_count++];
    memset(data_effect, 0, sizeof(*data_effect));
    data_effect->location.kind = M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
    data_effect->location.width = 4U;
    data_effect->location.register_count = 1U;
    data_effect->location.registers[0].register_kind = M68K_ANALYSIS_REGISTER_DATA;
    data_effect->location.registers[0].register_index = bit;
    data_effect->effect = (preserved_data & (uint8_t)(1U << bit)) != 0U
      ? M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED : M68K_FUNCTION_SUMMARY_LOCATION_CLOBBERED;
    memset(address_effect, 0, sizeof(*address_effect));
    address_effect->location.kind = M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
    address_effect->location.width = 4U;
    address_effect->location.register_count = 1U;
    address_effect->location.registers[0].register_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
    address_effect->location.registers[0].register_index = bit;
    address_effect->effect = (preserved_address & (uint8_t)(1U << bit)) != 0U
      ? M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED : M68K_FUNCTION_SUMMARY_LOCATION_CLOBBERED;
  }
}

static int generated_platform_call_summary(uint8_t platform_kind, const AmigaOsLibraryVectorInfo *vector,
    uint8_t output_reg_known, uint8_t output_reg_kind, uint8_t output_reg_index,
    M68kAnalysisFunctionSummary *out_summary) {
  uint8_t preserved_data = 0U;
  uint8_t preserved_address = 0U;
  if (out_summary == NULL) return 0;
  memset(out_summary, 0, sizeof(*out_summary));
  (void)platform_facts_v2_calling_convention_preserved_data_mask(platform_kind, &preserved_data);
  (void)platform_facts_v2_calling_convention_preserved_address_mask(platform_kind, &preserved_address);
  function_summary_set_register_partition(out_summary, preserved_data, preserved_address);
  if (vector != NULL) {
    const AmigaOsCallInputInfo *inputs;
    size_t input_count = 0U, input_index;
    inputs = amiga_os_library_vector_inputs(vector, &input_count);
    for (input_index = 0U; inputs != NULL && input_index < input_count &&
         out_summary->input_count < M68K_ANALYSIS_FUNCTION_SUMMARY_INPUT_LIMIT; ++input_index) {
      const AmigaOsCallInputInfo *platform_input = &inputs[input_index];
      const char *struct_name;
      M68kAnalysisFunctionSummaryInput *input;
      if (platform_input->reg_kind != AMIGA_OS_REGISTER_ADDRESS || platform_input->reg_index >= 8U ||
          platform_input->struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
      struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, platform_input->struct_id);
      if (struct_name == NULL || struct_name[0] == '\0') continue;
      input = &out_summary->inputs[out_summary->input_count++];
      input->seed_kind = M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR;
      input->location.kind = M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
      input->location.width = 4U;
      input->location.register_count = 1U;
      input->location.registers[0].register_kind = platform_input->reg_kind;
      input->location.registers[0].register_index = platform_input->reg_index;
      snprintf(input->struct_name, sizeof(input->struct_name), "%s", struct_name);
      input->has_platform_identity = 1U;
      input->platform_library_id = vector->library_id;
      input->platform_function_id = vector->function_id;
      input->platform_input_id = platform_input->input_id;
    }
  }
  if (vector != NULL && amiga_output_has_typed_info(&vector->output)) {
    M68kAnalysisFunctionSummaryResult *result = &out_summary->results[out_summary->result_count++];
    result->kind = M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_PLATFORM_OUTPUT;
    result->location.kind = M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
    result->location.width = 4U;
    result->location.register_count = 1U;
    result->location.registers[0].register_kind = output_reg_known != 0U ? output_reg_kind : vector->output.reg_kind;
    result->location.registers[0].register_index = output_reg_known != 0U ? output_reg_index : vector->output.reg_index;
    result->platform_library_id = vector->library_id;
    result->platform_function_id = vector->function_id;
    result->platform_output_id = vector->output.output_id;
  }
  return 1;
}

static int function_summary_platform_input_matches(const M68kAnalysisFunctionSummaryInput *existing,
    const M68kAnalysisFunctionSummaryInput *generated) {
  if (existing == NULL || generated == NULL || existing->seed_kind != generated->seed_kind ||
      strcmp(existing->struct_name, generated->struct_name) != 0) return 0;
  if (existing->has_platform_identity == 0U) return 1;
  return generated->has_platform_identity != 0U &&
    existing->platform_library_id == generated->platform_library_id &&
    existing->platform_function_id == generated->platform_function_id &&
    existing->platform_input_id == generated->platform_input_id;
}

static int function_summary_platform_result_matches(const M68kAnalysisFunctionSummaryResult *existing,
    const M68kAnalysisFunctionSummaryResult *generated) {
  return existing != NULL && generated != NULL && existing->kind == generated->kind &&
    existing->input_index == generated->input_index &&
    existing->platform_library_id == generated->platform_library_id &&
    existing->platform_function_id == generated->platform_function_id &&
    existing->platform_output_id == generated->platform_output_id;
}

static M68kPlatformContractCompositionState function_summary_compose_platform_contract(
    const M68kAnalysisFunctionSummary *local_summary,
    const M68kAnalysisFunctionSummary *platform_summary,
    M68kAnalysisFunctionSummary *out_summary) {
  uint8_t input_index, result_index;
  if (local_summary == NULL || platform_summary == NULL || out_summary == NULL)
    return M68K_PLATFORM_CONTRACT_COMPOSITION_IDENTITY_CONFLICT;
  *out_summary = *local_summary;
  for (input_index = 0U; input_index < platform_summary->input_count; ++input_index) {
    const M68kAnalysisFunctionSummaryInput *generated = &platform_summary->inputs[input_index];
    uint8_t existing_index;
    for (existing_index = 0U; existing_index < out_summary->input_count; ++existing_index) {
      if (m68k_function_summary_abi_location_equal(&out_summary->inputs[existing_index].location,
          &generated->location)) break;
    }
    if (existing_index < out_summary->input_count) {
      if (!function_summary_platform_input_matches(&out_summary->inputs[existing_index], generated))
        return M68K_PLATFORM_CONTRACT_COMPOSITION_IDENTITY_CONFLICT;
      /* Normalize an equivalent target-declared input to the generated ID. */
      out_summary->inputs[existing_index] = *generated;
    } else if (out_summary->input_count == M68K_ANALYSIS_FUNCTION_SUMMARY_INPUT_LIMIT) {
      return M68K_PLATFORM_CONTRACT_COMPOSITION_CAPACITY;
    } else {
      out_summary->inputs[out_summary->input_count++] = *generated;
    }
  }
  for (result_index = 0U; result_index < platform_summary->result_count; ++result_index) {
    const M68kAnalysisFunctionSummaryResult *generated = &platform_summary->results[result_index];
    uint8_t existing_index;
    for (existing_index = 0U; existing_index < out_summary->result_count; ++existing_index) {
      if (m68k_function_summary_abi_location_equal(&out_summary->results[existing_index].location,
          &generated->location)) break;
    }
    if (existing_index < out_summary->result_count) {
      if (!function_summary_platform_result_matches(&out_summary->results[existing_index], generated))
        return M68K_PLATFORM_CONTRACT_COMPOSITION_IDENTITY_CONFLICT;
    } else if (out_summary->result_count == M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_LIMIT) {
      return M68K_PLATFORM_CONTRACT_COMPOSITION_CAPACITY;
    } else {
      out_summary->results[out_summary->result_count++] = *generated;
    }
  }
  return M68K_PLATFORM_CONTRACT_COMPOSITION_COMPLETE;
}

static void typed_state_set_app_address(M68kRenderTypedState *state, uint8_t reg_index, int16_t displacement,
    uint16_t struct_id, const M68kRenderTypedProvenance *provenance, uint8_t base_evidence_kind) {
  if (state == NULL || reg_index >= 8U) return;
  state->addr_regs[reg_index].known = struct_id != AMIGA_OS_STRUCT_ID_NONE ? 1U : 0U;
  state->addr_regs[reg_index].output = NULL;
  state->addr_regs[reg_index].struct_id = struct_id;
  typed_origin_clear(&state->addr_regs[reg_index].origin);
  state->addr_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
  state->app_addr_regs[reg_index].known = 1U;
  state->app_addr_regs[reg_index].displacement = displacement;
  state->app_addr_regs[reg_index].base_evidence_kind = base_evidence_kind;
  typed_memory_base_clear(&state->memory_base_regs[reg_index]);
  typed_state_clear_addr_alias_for_reg(state, reg_index);
}

static void typed_state_set_data_app_address(M68kRenderTypedState *state, uint8_t reg_index, int16_t displacement,
    uint8_t base_evidence_kind) {
  if (state == NULL || reg_index >= 8U) return;
  state->data_app_addr_regs[reg_index].known = 1U;
  state->data_app_addr_regs[reg_index].displacement = displacement;
  state->data_app_addr_regs[reg_index].base_evidence_kind = base_evidence_kind;
  typed_memory_base_clear(&state->data_memory_base_regs[reg_index]);
}

static void typed_memory_base_clear(M68kRenderTypedMemoryBaseValue *value) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
}

static void typed_state_set_memory_base(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index,
    size_t section_index, uint32_t offset) {
  M68kRenderTypedMemoryBaseValue *value;
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == 1U) value = &state->data_memory_base_regs[reg_index];
  else if (reg_kind == 2U) value = &state->memory_base_regs[reg_index];
  else return;
  value->pointer_table_known = 0U;
  value->pointer_table_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  value->pointer_table_section_index = 0U;
  value->pointer_table_offset = 0U;
  value->pointer_table_size = 0U;
  value->known = 1U;
  value->section_index = section_index;
  value->offset = offset;
  value->affine_known = 1U;
  value->affine_origin_section_index = section_index;
  value->affine_origin_offset = offset;
  value->affine_signed_addend = 0;
}

static int typed_memory_base_apply_affine_delta(M68kRenderTypedMemoryBaseValue *value, int32_t delta) {
  uint32_t next_offset;
  int64_t next_addend;
  if (value == NULL) return 0;
  /* Cursor widening can lose a concrete offset without losing the table's
   * homogeneous pointee contract. This retains a type, never a target/bound. */
  if (!value->known) return value->pointer_table_known != 0U;
  if (!value->affine_known || !typed_memory_base_offset_add(value->offset, delta, &next_offset)) return 0;
  next_addend = (int64_t)value->affine_signed_addend + (int64_t)delta;
  if (next_addend < INT32_MIN || next_addend > INT32_MAX) return 0;
  value->offset = next_offset;
  value->affine_signed_addend = (int32_t)next_addend;
  typed_memory_base_clear_pointer_table_if_offset_outside(value);
  return 1;
}

static int typed_memory_base_with_displacement(const M68kRenderTypedMemoryBaseValue *source,
    int32_t displacement, M68kRenderTypedMemoryBaseValue *out_value) {
  if (source == NULL || out_value == NULL || !source->known || !source->affine_known) return 0;
  *out_value = *source;
  return typed_memory_base_apply_affine_delta(out_value, displacement);
}

static void typed_state_clear_address_reg_preserving_affine(M68kRenderTypedState *state, uint8_t reg_index,
    int32_t delta) {
  M68kRenderTypedMemoryBaseValue affine_base;
  if (state == NULL || reg_index >= 8U) return;
  affine_base = state->memory_base_regs[reg_index];
  typed_state_clear_reg(state, M68K_ANALYSIS_REGISTER_ADDRESS, reg_index);
  if (typed_memory_base_apply_affine_delta(&affine_base, delta)) {
    state->memory_base_regs[reg_index] = affine_base;
  }
}

static const M68kAnalysisStructuredDataItem *lookup_pointer_table_item_covering_address(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  uint16_t index;
  if (lookup == NULL || lookup->policy == NULL) return NULL;
  /* Prefer a declaration with a pointee contract: narrower legacy data
   * classifications are permitted to overlap the full table declaration. */
  for (index = 0U; index < lookup->policy->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &lookup->policy->structured_data_items[index];
    if (!item->has_section_index || item->section_index != section_index || item->size < 4U ||
        item->pointer_struct[0] == '\0' ||
        (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE) == 0U ||
        offset < item->offset || offset - item->offset > item->size - 4U || ((offset - item->offset) & 3U) != 0U)
      continue;
    return item;
  }
  for (index = 0U; index < lookup->auto_structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &lookup->auto_structured_data_items[index];
    if (!item->has_section_index || item->section_index != section_index || item->size < 4U ||
        item->pointer_struct[0] == '\0' ||
        (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE) == 0U ||
        offset < item->offset || offset - item->offset > item->size - 4U || ((offset - item->offset) & 3U) != 0U)
      continue;
    return item;
  }
  return NULL;
}

static const M68kAnalysisStructuredDataItem *lookup_pointer_table_item_for_contract(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t offset, uint32_t size) {
  uint16_t index;
  if (lookup == NULL || lookup->policy == NULL) return NULL;
  for (index = 0U; index < lookup->policy->structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &lookup->policy->structured_data_items[index];
    if (item->has_section_index && item->section_index == section_index && item->offset == offset &&
        item->size == size && item->size >= 4U && item->pointer_struct[0] != '\0' &&
        (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE) != 0U)
      return item;
  }
  for (index = 0U; index < lookup->auto_structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *item = &lookup->auto_structured_data_items[index];
    if (item->has_section_index && item->section_index == section_index && item->offset == offset &&
        item->size == size && item->size >= 4U && item->pointer_struct[0] != '\0' &&
        (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE) != 0U)
      return item;
  }
  return NULL;
}

static void typed_memory_base_bind_pointer_table(M68kRenderTypedMemoryBaseValue *value,
    const M68kRenderLookup *lookup) {
  const M68kAnalysisStructuredDataItem *item;
  if (value == NULL || lookup == NULL || lookup->policy == NULL || !value->known) return;
  item = lookup_pointer_table_item_covering_address(lookup, value->section_index, value->offset);
  if (item == NULL) return;
  value->pointer_table_known = 1U;
  value->pointer_table_struct_id = item->pointer_struct_id != AMIGA_OS_STRUCT_ID_NONE
    ? item->pointer_struct_id : lookup_policy_struct_id_by_name(lookup->policy, item->pointer_struct);
  value->pointer_table_section_index = item->section_index;
  value->pointer_table_offset = item->offset;
  value->pointer_table_size = item->size;
}

/* A runtime table has no source-section address to bind, but its app slot
 * still contracts the table's homogeneous longword entry type. */
static int typed_memory_base_bind_runtime_pointer_table_slot(M68kRenderTypedMemoryBaseValue *value,
    const M68kRenderLookup *lookup, const M68kRenderPlatformState *platform_state,
    const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint16_t index;
  if (value == NULL || lookup == NULL || lookup->policy == NULL || platform_state == NULL || operand == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U ||
      !render_state_operand_uses_app_base(platform_state, base_reg, displacement)) {
    return 0;
  }
  for (index = 0U; index < lookup->policy->rsset_layout_region_count &&
       index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++index) {
    const M68kAnalysisRssetLayoutRegion *region = &lookup->policy->rsset_layout_regions[index];
    const char *layout_name = region->layout_name[0] != '\0' ? region->layout_name : "app";
    const char *base_symbol = region->base_symbol[0] != '\0' ? region->base_symbol : M68K_APP_BASE_SYMBOL;
    uint16_t struct_id;
    if (!((region->flags & (uint8_t)M68K_ANALYSIS_RSSET_LAYOUT_REGION_FLAG_APP_LAYOUT) != 0U ||
          (strcmp(layout_name, "app") == 0 && strcmp(base_symbol, M68K_APP_BASE_SYMBOL) == 0)) ||
        strcmp(base_symbol, M68K_APP_BASE_SYMBOL) != 0 || region->offset != (uint32_t)displacement ||
        region->storage_kind_id != M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER_TABLE ||
        region->pointer_struct[0] == '\0') {
      continue;
    }
    struct_id = lookup_policy_struct_id_by_name(lookup->policy, region->pointer_struct);
    if (struct_id == AMIGA_OS_STRUCT_ID_NONE) return 0;
    typed_memory_base_clear(value);
    value->pointer_table_known = 1U;
    value->pointer_table_struct_id = struct_id;
    return 1;
  }
  return 0;
}

static int render_lookup_add_affine_address_use(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t operand_index, uint8_t base_register, const M68kRenderTypedMemoryBaseValue *base,
    int32_t displacement) {
  M68kRenderAffineAddressUse *grown;
  size_t index, next_capacity;
  uint32_t target_offset;
  int64_t signed_addend;
  if (lookup == NULL || base == NULL || !base->known || !base->affine_known || operand_index >= 4U ||
      base_register >= 8U || !typed_memory_base_offset_add(base->offset, displacement, &target_offset)) return 0;
  signed_addend = (int64_t)base->affine_signed_addend + (int64_t)displacement;
  if (signed_addend < INT32_MIN || signed_addend > INT32_MAX) return 0;
  for (index = 0U; index < lookup->affine_address_use_count; ++index) {
    const M68kRenderAffineAddressUse *existing = &lookup->affine_address_uses[index];
    if (existing->section_index == section_index && existing->offset == offset &&
        existing->operand_index == operand_index && existing->origin_section_index == base->affine_origin_section_index &&
        existing->origin_offset == base->affine_origin_offset && existing->target_section_index == base->section_index &&
        existing->target_offset == target_offset && existing->signed_addend == (int32_t)signed_addend) return 0;
  }
  if (lookup->affine_address_use_count == lookup->affine_address_use_capacity) {
    next_capacity = lookup->affine_address_use_capacity == 0U ? 32U : lookup->affine_address_use_capacity * 2U;
    grown = (M68kRenderAffineAddressUse *)render_lookup_grow_array(lookup, lookup->affine_address_uses,
      lookup->affine_address_use_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->affine_address_uses = grown;
    lookup->affine_address_use_capacity = next_capacity;
  }
  memset(&lookup->affine_address_uses[lookup->affine_address_use_count], 0,
    sizeof(lookup->affine_address_uses[lookup->affine_address_use_count]));
  lookup->affine_address_uses[lookup->affine_address_use_count].section_index = section_index;
  lookup->affine_address_uses[lookup->affine_address_use_count].offset = offset;
  lookup->affine_address_uses[lookup->affine_address_use_count].operand_index = operand_index;
  lookup->affine_address_uses[lookup->affine_address_use_count].base_register = base_register;
  lookup->affine_address_uses[lookup->affine_address_use_count].origin_section_index = base->affine_origin_section_index;
  lookup->affine_address_uses[lookup->affine_address_use_count].origin_offset = base->affine_origin_offset;
  lookup->affine_address_uses[lookup->affine_address_use_count].target_section_index = base->section_index;
  lookup->affine_address_uses[lookup->affine_address_use_count].target_offset = target_offset;
  lookup->affine_address_uses[lookup->affine_address_use_count].signed_addend = (int32_t)signed_addend;
  ++lookup->affine_address_use_count;
  return 0;
}

static int render_lookup_record_affine_address_uses(M68kRenderLookup *lookup, size_t section_index,
    const M68kRenderTypedState *state, const M68kInstructionIR *instruction, uint32_t offset) {
  size_t operand_index;
  if (lookup == NULL || state == NULL || instruction == NULL) return -1;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t base_register;
    int16_t displacement;
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (!operand_is_address_memory_local(operand, &base_register, &displacement) || base_register >= 8U) continue;
    if (render_lookup_add_affine_address_use(lookup, section_index, offset, (uint8_t)operand_index, base_register,
        &state->memory_base_regs[base_register], displacement) != 0) return -1;
  }
  return 0;
}

static void typed_memory_base_clear_pointer_table_if_offset_outside(M68kRenderTypedMemoryBaseValue *value) {
  /* Runtime table contracts have no finite source range. Their homogeneous
   * entry type remains valid as the cursor advances. */
  if (value == NULL || !value->pointer_table_known || !value->known) return;
  if (value->offset < value->pointer_table_offset || value->pointer_table_size < 4U ||
      value->offset - value->pointer_table_offset > value->pointer_table_size ||
      ((value->offset - value->pointer_table_offset) & 3U) != 0U) {
    value->pointer_table_known = 0U;
    value->pointer_table_struct_id = AMIGA_OS_STRUCT_ID_NONE;
    value->pointer_table_section_index = 0U;
    value->pointer_table_offset = 0U;
    value->pointer_table_size = 0U;
  }
}

static int typed_state_copy_memory_base(const M68kRenderTypedState *state, const M68kOperandIR *operand,
    M68kRenderTypedMemoryBaseValue *out_value) {
  uint8_t reg = 0U;
  if (out_value != NULL) typed_memory_base_clear(out_value);
  if (state == NULL || operand == NULL || out_value == NULL) return 0;
  if (operand_is_data_register_local(operand, &reg) && reg < 8U &&
      (state->data_memory_base_regs[reg].known || state->data_memory_base_regs[reg].pointer_table_known)) {
    *out_value = state->data_memory_base_regs[reg];
    return 1;
  }
  if (operand_address_register_index_local(operand, &reg) && reg < 8U &&
      (state->memory_base_regs[reg].known || state->memory_base_regs[reg].pointer_table_known)) {
    *out_value = state->memory_base_regs[reg];
    return 1;
  }
  if (operand != NULL && operand->kind == M68K_ASM_OPERAND_EA &&
      (operand->value.ea_mode == 2U || operand->value.ea_mode == 3U) && operand->value.ea_reg < 8U &&
      (state->memory_base_regs[operand->value.ea_reg].known ||
       state->memory_base_regs[operand->value.ea_reg].pointer_table_known)) {
    *out_value = state->memory_base_regs[operand->value.ea_reg];
    return 1;
  }
  return 0;
}

static int candidate_local_target_for_operand(const M68kDecodeCandidate *candidate, uint32_t operand_index,
    size_t *out_section_index, uint32_t *out_offset) {
  size_t target_index;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (candidate == NULL || out_section_index == NULL || out_offset == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->has_section == 0U || target->has_operand == 0U || target->operand_index != operand_index) continue;
    *out_section_index = target->section_index;
    *out_offset = target->offset;
    return 1;
  }
  return 0;
}

static int typed_memory_base_offset_add(uint32_t base_offset, int32_t displacement, uint32_t *out_offset) {
  int64_t value = (int64_t)base_offset + (int64_t)displacement;
  if (out_offset != NULL) *out_offset = 0U;
  if (value < 0 || value > UINT32_MAX) return 0;
  if (out_offset != NULL) *out_offset = (uint32_t)value;
  return 1;
}

static int typed_state_copy_app_address(const M68kRenderTypedState *state, const M68kOperandIR *operand,
    int16_t *out_displacement, uint8_t *out_base_evidence_kind) {
  uint8_t reg = 0U;
  if (out_base_evidence_kind != NULL) *out_base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
  if (out_displacement != NULL) *out_displacement = 0;
  if (state == NULL || operand == NULL || out_displacement == NULL) return 0;
  if (operand_address_register_index_local(operand, &reg) && reg < 8U && state->app_addr_regs[reg].known) {
    *out_displacement = state->app_addr_regs[reg].displacement;
    if (out_base_evidence_kind != NULL) *out_base_evidence_kind = state->app_addr_regs[reg].base_evidence_kind;
    return 1;
  }
  if (operand_is_data_register_local(operand, &reg) && reg < 8U && state->data_app_addr_regs[reg].known) {
    *out_displacement = state->data_app_addr_regs[reg].displacement;
    if (out_base_evidence_kind != NULL) *out_base_evidence_kind = state->data_app_addr_regs[reg].base_evidence_kind;
    return 1;
  }
  return 0;
}

static const AmigaOsCallOutputInfo *typed_state_output_for_operand(const M68kRenderTypedState *state,
    const M68kOperandIR *operand, uint8_t *out_reg_kind, uint8_t *out_reg_index) {
  uint8_t reg = 0U;
  if (out_reg_kind != NULL) *out_reg_kind = 0U;
  if (out_reg_index != NULL) *out_reg_index = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 1U;
    if (out_reg_index != NULL) *out_reg_index = reg;
    return state->data_regs[reg].known ? state->data_regs[reg].output : NULL;
  }
  if (operand_address_register_index_local(operand, &reg)) {
    if (out_reg_kind != NULL) *out_reg_kind = 2U;
    if (out_reg_index != NULL) *out_reg_index = reg;
    return state->addr_regs[reg].known ? state->addr_regs[reg].output : NULL;
  }
  return NULL;
}

static uint16_t typed_state_struct_id_for_operand(const M68kRenderTypedState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return AMIGA_OS_STRUCT_ID_NONE;
  if (operand_is_data_register_local(operand, &reg))
    return state->data_regs[reg].known ? state->data_regs[reg].struct_id : AMIGA_OS_STRUCT_ID_NONE;
  if (operand_address_register_index_local(operand, &reg))
    return state->addr_regs[reg].known ? state->addr_regs[reg].struct_id : AMIGA_OS_STRUCT_ID_NONE;
  return AMIGA_OS_STRUCT_ID_NONE;
}

static int typed_state_origin_for_operand(const M68kRenderTypedState *state, const M68kOperandIR *operand,
    M68kRenderTypedStorageOrigin *out_origin) {
  uint8_t reg = 0U;
  if (out_origin != NULL) typed_origin_clear(out_origin);
  if (state == NULL || operand == NULL || out_origin == NULL) return 0;
  if (operand_is_data_register_local(operand, &reg)) {
    if (state->data_regs[reg].known == 0U || state->data_regs[reg].origin.kind == M68K_RENDER_TYPED_ORIGIN_NONE)
      return 0;
    *out_origin = state->data_regs[reg].origin;
    return 1;
  }
  if (operand_address_register_index_local(operand, &reg)) {
    if (state->addr_regs[reg].known == 0U || state->addr_regs[reg].origin.kind == M68K_RENDER_TYPED_ORIGIN_NONE)
      return 0;
    *out_origin = state->addr_regs[reg].origin;
    return 1;
  }
  return 0;
}

static void typed_state_set_reg_origin(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index,
    const M68kRenderTypedStorageOrigin *origin) {
  if (state == NULL || origin == NULL || reg_index >= 8U || origin->kind == M68K_RENDER_TYPED_ORIGIN_NONE)
    return;
  if (reg_kind == 1U && state->data_regs[reg_index].known)
    state->data_regs[reg_index].origin = *origin;
  else if (reg_kind == 2U && state->addr_regs[reg_index].known)
    state->addr_regs[reg_index].origin = *origin;
}

static int typed_stored_value_has_useful_info(const M68kRenderTypedStoredValue *value) {
  return value != NULL && (value->entry_value_id != 0U ||
    (value->known != 0U && typed_stored_value_has_payload(value)));
}

static M68kRenderTypedStoredValue typed_stored_value_for_operand(const M68kRenderTypedState *state,
    const M68kOperandIR *operand) {
  M68kRenderTypedStoredValue value;
  int16_t app_displacement = 0;
  uint8_t reg = 0U;
  typed_stored_value_clear(&value);
  value.struct_id = typed_state_struct_id_for_operand(state, operand);
  value.output = typed_state_output_for_operand(state, operand, NULL, NULL);
  if (state != NULL && operand_is_data_register_local(operand, &reg)) {
    value.layout_base_id = state->data_regs[reg].layout_base_id;
    value.entry_value_id = state->data_regs[reg].entry_value_id;
    value.provenance = state->data_regs[reg].provenance;
    value.array_element_count = state->data_regs[reg].array_element_count;
    value.array_element_index = state->data_regs[reg].array_element_index;
    value.byte_cursor = state->data_regs[reg].byte_cursor;
    value.pointer_value_known = state->data_regs[reg].pointer_value_known;
    value.pointer_value = state->data_regs[reg].pointer_value;
    value.pointer_candidate_count = state->data_regs[reg].pointer_candidate_count;
    value.address_value_candidate_overflow = state->data_regs[reg].address_value_candidate_overflow;
    memcpy(value.pointer_candidates, state->data_regs[reg].pointer_candidates, sizeof(value.pointer_candidates));
    value.raw_long_value_known = state->data_regs[reg].raw_long_value_known;
    value.raw_long_value = state->data_regs[reg].raw_long_value;
    value.raw_long_candidate_count = state->data_regs[reg].raw_long_candidate_count;
    memcpy(value.raw_long_candidates, state->data_regs[reg].raw_long_candidates, sizeof(value.raw_long_candidates));
    value.table_origin = state->data_regs[reg].table_origin;
    value.pointer_target_known = state->data_regs[reg].pointer_target_known;
    value.pointer_target_section_index = state->data_regs[reg].pointer_target_section_index;
    value.pointer_target_offset = state->data_regs[reg].pointer_target_offset;
  } else if (state != NULL && operand_address_register_index_local(operand, &reg)) {
    value.layout_base_id = state->addr_regs[reg].layout_base_id;
    value.entry_value_id = state->addr_regs[reg].entry_value_id;
    value.provenance = state->addr_regs[reg].provenance;
    value.array_element_count = state->addr_regs[reg].array_element_count;
    value.array_element_index = state->addr_regs[reg].array_element_index;
    value.byte_cursor = state->addr_regs[reg].byte_cursor;
    value.pointer_value_known = state->addr_regs[reg].pointer_value_known;
    value.pointer_value = state->addr_regs[reg].pointer_value;
    value.pointer_candidate_count = state->addr_regs[reg].pointer_candidate_count;
    value.address_value_candidate_overflow = state->addr_regs[reg].address_value_candidate_overflow;
    memcpy(value.pointer_candidates, state->addr_regs[reg].pointer_candidates, sizeof(value.pointer_candidates));
    value.raw_long_value_known = state->addr_regs[reg].raw_long_value_known;
    value.raw_long_value = state->addr_regs[reg].raw_long_value;
    value.raw_long_candidate_count = state->addr_regs[reg].raw_long_candidate_count;
    memcpy(value.raw_long_candidates, state->addr_regs[reg].raw_long_candidates, sizeof(value.raw_long_candidates));
    value.table_origin = state->addr_regs[reg].table_origin;
    value.pointer_target_known = state->addr_regs[reg].pointer_target_known;
    value.pointer_target_section_index = state->addr_regs[reg].pointer_target_section_index;
    value.pointer_target_offset = state->addr_regs[reg].pointer_target_offset;
  }
  if (typed_state_copy_app_address(state, operand, &app_displacement, &value.app_base_evidence_kind)) {
    value.app_address_known = 1U;
    value.app_displacement = app_displacement;
  }
  typed_stored_value_update_known(&value);
  return value;
}

static void typed_state_restore_stored_register(M68kRenderTypedState *state, uint8_t kind, uint8_t reg,
    const M68kRenderTypedStoredValue *value, const M68kRenderTypedMemoryBaseValue *memory_base) {
  M68kRenderTypedRegValue *target;
  M68kRenderTypedAppAddressValue *app;
  if (reg >= 8U || (kind != M68K_ANALYSIS_REGISTER_DATA && kind != M68K_ANALYSIS_REGISTER_ADDRESS)) return;
  typed_state_clear_reg(state, kind, reg);
  target = kind == M68K_ANALYSIS_REGISTER_DATA ? &state->data_regs[reg] : &state->addr_regs[reg];
  app = kind == M68K_ANALYSIS_REGISTER_DATA ? &state->data_app_addr_regs[reg] : &state->app_addr_regs[reg];
  if (value != NULL && (value->known || value->entry_value_id)) {
    target->known = value->known;
    target->output = value->output;
    target->struct_id = value->struct_id;
    target->array_element_count = value->array_element_count;
    target->array_element_index = value->array_element_index;
    target->byte_cursor = value->byte_cursor;
    target->layout_base_id = value->layout_base_id;
    target->entry_value_id = value->entry_value_id;
    target->pointer_value_known = value->pointer_value_known;
    target->pointer_candidate_count = value->pointer_candidate_count;
    target->pointer_value = value->pointer_value;
    memcpy(target->pointer_candidates, value->pointer_candidates, sizeof(target->pointer_candidates));
    target->raw_long_value_known = value->raw_long_value_known;
    target->raw_long_candidate_count = value->raw_long_candidate_count;
    target->raw_long_value = value->raw_long_value;
    memcpy(target->raw_long_candidates, value->raw_long_candidates, sizeof(target->raw_long_candidates));
    target->address_value_candidate_overflow = value->address_value_candidate_overflow;
    target->pointer_target_known = value->pointer_target_known;
    target->pointer_target_section_index = value->pointer_target_section_index;
    target->pointer_target_offset = value->pointer_target_offset;
    target->table_origin = value->table_origin;
    target->provenance = value->provenance;
    if (value->app_address_known) {
      app->known = 1U;
      app->displacement = value->app_displacement;
      app->base_evidence_kind = value->app_base_evidence_kind;
    }
  }
  if (memory_base != NULL) {
    if (kind == M68K_ANALYSIS_REGISTER_DATA) state->data_memory_base_regs[reg] = *memory_base;
    else state->memory_base_regs[reg] = *memory_base;
  }
}

static void typed_state_clear_stack_slots(M68kRenderTypedState *state) {
  if (state == NULL) return;
  state->stack_slot_count = 0U;
}

static void typed_state_clear_stack_slot(M68kRenderTypedState *state, int16_t displacement) {
  size_t index;
  if (state == NULL) return;
  for (index = 0U; index < state->stack_slot_count; ++index) {
    if (state->stack_slots[index].known == 0U || state->stack_slots[index].displacement != displacement) continue;
    state->stack_slots[index] = state->stack_slots[state->stack_slot_count - 1U];
    --state->stack_slot_count;
    return;
  }
}

/* The stored packet denotes a whole LONG pointer/cursor value. Any byte
 * overlap destroys that identity; an unknown footprint cannot preserve it. */
static int typed_long_cell_overlaps_write(int64_t cell, int64_t start, uint8_t width) {
  return width == 0U || (cell < start + width && start < cell + 4);
}

/* Stack facts describe full LONG values.  A write into any byte of one
 * invalidates it, including an unaligned partial overwrite of a saved cursor. */
static void typed_state_clear_stack_write(M68kRenderTypedState *state, int16_t displacement,
    uint8_t width) {
  size_t index = 0U;
  if (state == NULL) return;
  if (width == 0U) { typed_state_clear_stack_slots(state); return; }
  while (index < state->stack_slot_count) {
    int32_t start = state->stack_slots[index].displacement;
    if (typed_long_cell_overlaps_write(start, displacement, width)) {
      state->stack_slots[index] = state->stack_slots[--state->stack_slot_count];
    } else ++index;
  }
}

static void typed_state_set_stack_slot(M68kRenderTypedState *state, int16_t displacement,
    uint8_t caller_save_temporary, uint8_t abi_stack_convention, const M68kRenderTypedStoredValue *value,
    const M68kRenderTypedMemoryBaseValue *memory_base) {
  size_t index;
  if (state == NULL || value == NULL ||
      (!typed_stored_value_has_useful_info(value) && (memory_base == NULL ||
       (memory_base->known == 0U && memory_base->pointer_table_known == 0U)))) return;
  for (index = 0U; index < state->stack_slot_count; ++index) {
    if (state->stack_slots[index].known == 0U || state->stack_slots[index].displacement != displacement) continue;
    state->stack_slots[index].value = *value;
    state->stack_slots[index].caller_save_temporary = caller_save_temporary;
    state->stack_slots[index].abi_stack_convention = abi_stack_convention;
    if (memory_base != NULL) state->stack_slots[index].memory_base = *memory_base;
    else typed_memory_base_clear(&state->stack_slots[index].memory_base);
    return;
  }
  if (state->stack_slot_count >= M68K_RENDER_TYPED_STACK_SLOT_LIMIT) return;
  state->stack_slots[state->stack_slot_count].known = 1U;
  state->stack_slots[state->stack_slot_count].caller_save_temporary = caller_save_temporary;
  state->stack_slots[state->stack_slot_count].abi_stack_convention = abi_stack_convention;
  state->stack_slots[state->stack_slot_count].displacement = displacement;
  state->stack_slots[state->stack_slot_count].value = *value;
  if (memory_base != NULL) state->stack_slots[state->stack_slot_count].memory_base = *memory_base;
  ++state->stack_slot_count;
}

static const M68kRenderTypedMemoryBaseValue *typed_state_stack_slot_memory_base(
    const M68kRenderTypedState *state, int16_t displacement) {
  size_t index;
  if (state == NULL) return NULL;
  for (index = 0U; index < state->stack_slot_count; ++index) {
    const M68kRenderTypedStackSlot *slot = &state->stack_slots[index];
    if (slot->known != 0U && slot->displacement == displacement &&
        (slot->memory_base.known != 0U || slot->memory_base.pointer_table_known != 0U)) {
      return &slot->memory_base;
    }
  }
  return NULL;
}

/* Stack slots are expressed relative to the current A7.  On a caller push,
 * existing slots move up by four; on a matching pop they move down by four. */
static void typed_state_rebase_stack_slots(M68kRenderTypedState *state, int16_t adjustment) {
  size_t index;
  if (state == NULL) return;
  for (index = 0U; index < state->stack_slot_count;) {
    M68kRenderTypedStackSlot *slot = &state->stack_slots[index];
    int32_t displacement = (int32_t)slot->displacement + adjustment;
    if (displacement < INT16_MIN || displacement > INT16_MAX || displacement < 0) {
      state->stack_slots[index] = state->stack_slots[state->stack_slot_count - 1U];
      --state->stack_slot_count;
      continue;
    }
    slot->displacement = (int16_t)displacement;
    ++index;
  }
}

static void typed_state_preserve_caller_save_stack_slots(M68kRenderTypedState *state) {
  M68kRenderTypedStackSlot preserved[M68K_RENDER_TYPED_STACK_SLOT_LIMIT];
  size_t preserved_count = 0U, index;
  if (state == NULL) return;
  for (index = 0U; index < state->stack_slot_count; ++index) {
    if (state->stack_slots[index].known != 0U && state->stack_slots[index].caller_save_temporary != 0U)
      preserved[preserved_count++] = state->stack_slots[index];
  }
  typed_state_clear_all(state);
  for (index = 0U; index < preserved_count; ++index) state->stack_slots[index] = preserved[index];
  state->stack_slot_count = preserved_count;
}

static const M68kRenderTypedStoredValue *typed_state_stack_slot_value(const M68kRenderTypedState *state,
    int16_t displacement) {
  size_t index;
  if (state == NULL) return NULL;
  for (index = 0U; index < state->stack_slot_count; ++index) {
    const M68kRenderTypedStackSlot *slot = &state->stack_slots[index];
    if (slot->known != 0U && slot->displacement == displacement &&
        typed_stored_value_has_useful_info(&slot->value)) {
      return &slot->value;
    }
  }
  return NULL;
}

/* Stack values retain their ABI role.  Result transfer may consume only the
 * declared caller-argument slot, never a cleanup or prior result at the same
 * displacement. */
static const M68kRenderTypedStackSlot *typed_state_stack_slot_for_abi_location(
    const M68kRenderTypedState *state, int16_t displacement, uint8_t abi_stack_convention) {
  size_t index;
  if (state == NULL) return NULL;
  for (index = 0U; index < state->stack_slot_count; ++index) {
    const M68kRenderTypedStackSlot *slot = &state->stack_slots[index];
    if (slot->known == 0U || slot->displacement != displacement ||
        !typed_stored_value_has_useful_info(&slot->value)) continue;
    if (slot->abi_stack_convention == abi_stack_convention) return slot;
  }
  return NULL;
}

static const M68kRenderTypedBaseSlot *typed_state_base_slot_entry(const M68kRenderTypedState *state,
    uint8_t base_reg, int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return NULL;
  for (index = 0U; index < state->base_slot_count; ++index) {
    const M68kRenderTypedBaseSlot *slot = &state->base_slots[index];
    if (slot->known != 0U && slot->base_reg == base_reg && slot->displacement == displacement)
      return slot;
  }
  return NULL;
}

static M68kRenderTypedBaseSlot *typed_state_mutable_base_slot_entry(M68kRenderTypedState *state,
    uint8_t base_reg, int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return NULL;
  for (index = 0U; index < state->base_slot_count; ++index) {
    M68kRenderTypedBaseSlot *slot = &state->base_slots[index];
    if (slot->known != 0U && slot->base_reg == base_reg && slot->displacement == displacement)
      return slot;
  }
  return NULL;
}

/* Local register-relative cells and typed fields share the instruction's
 * decoded full write footprint, including every MOVEM element. Base identity
 * and field byte-cursor semantics are unchanged. */
static void typed_state_clear_base_write(M68kRenderTypedState *state, uint8_t base_reg,
    int16_t displacement, uint8_t width) {
  size_t index = 0U;
  int64_t field_start;
  if (state == NULL || base_reg >= 8U) return;
  while (index < state->base_slot_count) {
    M68kRenderTypedBaseSlot *slot = &state->base_slots[index];
    if (slot->known && slot->base_reg == base_reg &&
        typed_long_cell_overlaps_write(slot->displacement, displacement, width)) {
      *slot = state->base_slots[--state->base_slot_count];
    } else ++index;
  }
  field_start = (int64_t)state->addr_regs[base_reg].byte_cursor + displacement;
  index = 0U;
  while (index < state->field_slot_count) {
    M68kRenderTypedFieldSlot *slot = &state->field_slots[index];
    if (slot->known && slot->base_reg == base_reg &&
        typed_long_cell_overlaps_write(slot->displacement, field_start, width)) {
      *slot = state->field_slots[--state->field_slot_count];
    } else ++index;
  }
}

static void typed_state_set_base_slot(M68kRenderTypedState *state, uint8_t base_reg, int16_t displacement,
    const M68kRenderTypedStoredValue *value) {
  size_t index;
  if (state == NULL || base_reg >= 8U || value == NULL || !typed_stored_value_has_useful_info(value)) return;
  for (index = 0U; index < state->base_slot_count; ++index) {
    if (state->base_slots[index].known == 0U || state->base_slots[index].base_reg != base_reg ||
        state->base_slots[index].displacement != displacement) {
      continue;
    }
    state->base_slots[index].value = *value;
    return;
  }
  if (state->base_slot_count >= M68K_RENDER_TYPED_BASE_SLOT_LIMIT) return;
  state->base_slots[state->base_slot_count].known = 1U;
  state->base_slots[state->base_slot_count].storage_id = 0U;
  state->base_slots[state->base_slot_count].base_reg = base_reg;
  state->base_slots[state->base_slot_count].displacement = displacement;
  state->base_slots[state->base_slot_count].value = *value;
  ++state->base_slot_count;
}

static const M68kRenderTypedStoredValue *typed_state_base_slot_value(const M68kRenderTypedState *state,
    uint8_t base_reg, int16_t displacement) {
  const M68kRenderTypedBaseSlot *slot = typed_state_base_slot_entry(state, base_reg, displacement);
  if (slot != NULL && typed_stored_value_has_useful_info(&slot->value)) return &slot->value;
  return NULL;
}

static const M68kRenderTypedFieldSlot *typed_state_field_slot_entry(const M68kRenderTypedState *state,
    uint8_t base_reg, uint16_t struct_id, int32_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U || struct_id == AMIGA_OS_STRUCT_ID_NONE) return NULL;
  for (index = 0U; index < state->field_slot_count; ++index) {
    const M68kRenderTypedFieldSlot *slot = &state->field_slots[index];
    if (slot->known != 0U && slot->base_reg == base_reg && slot->struct_id == struct_id &&
        slot->displacement == displacement) return slot;
  }
  return NULL;
}

static void typed_state_set_field_slot(M68kRenderTypedState *state, uint8_t base_reg, uint16_t struct_id,
    int32_t displacement, const M68kRenderTypedStoredValue *value) {
  const M68kRenderTypedFieldSlot *existing;
  size_t index;
  if (state == NULL || base_reg >= 8U || struct_id == AMIGA_OS_STRUCT_ID_NONE || value == NULL ||
      !typed_stored_value_has_useful_info(value)) return;
  existing = typed_state_field_slot_entry(state, base_reg, struct_id, displacement);
  if (existing != NULL) {
    state->field_slots[existing - state->field_slots].value = *value;
    return;
  }
  if (state->field_slot_count >= M68K_RENDER_TYPED_FIELD_SLOT_LIMIT) return;
  index = state->field_slot_count++;
  state->field_slots[index].known = 1U;
  state->field_slots[index].base_reg = base_reg;
  state->field_slots[index].struct_id = struct_id;
  state->field_slots[index].displacement = displacement;
  state->field_slots[index].value = *value;
}

static const M68kRenderTypedStoredValue *typed_state_field_slot_value(const M68kRenderTypedState *state,
    uint8_t base_reg, uint16_t struct_id, int32_t displacement) {
  const M68kRenderTypedFieldSlot *slot = typed_state_field_slot_entry(state, base_reg, struct_id, displacement);
  return slot != NULL && typed_stored_value_has_useful_info(&slot->value) ? &slot->value : NULL;
}

static uint16_t lookup_typed_output_slot_struct_id(const M68kRenderLookup *lookup, int16_t displacement) {
  size_t index;
  uint16_t struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (lookup == NULL) return AMIGA_OS_STRUCT_ID_NONE;
  for (index = 0U; index < lookup->typed_slot_effect_count; ++index) {
    const M68kRenderTypedSlotEffect *effect = &lookup->typed_slot_effects[index];
    uint16_t effect_struct_id;
    if (effect->displacement != displacement || effect->output == NULL) continue;
    effect_struct_id = effect->output->struct_id;
    if (effect_struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
    if (struct_id != AMIGA_OS_STRUCT_ID_NONE && struct_id != effect_struct_id) return AMIGA_OS_STRUCT_ID_NONE;
    struct_id = effect_struct_id;
  }
  return struct_id;
}

static uint16_t typed_struct_id_for_base_slot_operand(const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *platform_state, const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (lookup == NULL || operand == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U) {
    return AMIGA_OS_STRUCT_ID_NONE;
  }
  if (platform_state != NULL) {
    if (m68k_bitset_u32_has(platform_state->address_app_base_known, base_reg)) {
      uint16_t output_struct_id = lookup_typed_output_slot_struct_id(lookup, displacement);
      if (output_struct_id != AMIGA_OS_STRUCT_ID_NONE) return output_struct_id;
      output_struct_id = lookup_typed_app_slot_struct_id(lookup, displacement);
      if (output_struct_id != AMIGA_OS_STRUCT_ID_NONE) return output_struct_id;
      return lookup_app_base_field_slot_struct_id(lookup, displacement);
    }
    if (m68k_bitset_u32_has(platform_state->address_base_known, base_reg)) {
      return lookup_base_field_slot_struct_id(lookup, platform_state->address_base_library[base_reg], displacement);
    }
    if (base_reg == 6U) {
      uint16_t output_struct_id = lookup_typed_app_slot_struct_id(lookup, displacement);
      return output_struct_id != AMIGA_OS_STRUCT_ID_NONE ? output_struct_id :
        lookup_app_base_field_slot_struct_id(lookup, displacement);
    }
  } else if (base_reg == 6U) {
    return lookup_app_base_field_slot_struct_id(lookup, displacement);
  }
  return AMIGA_OS_STRUCT_ID_NONE;
}

static uint16_t lookup_typed_app_slot_struct_id(const M68kRenderLookup *lookup, int16_t displacement) {
  size_t index;
  if (lookup == NULL) return AMIGA_OS_STRUCT_ID_NONE;
  for (index = 0U; index < lookup->typed_app_slot_count; ++index) {
    const M68kRenderTypedAppSlot *slot = &lookup->typed_app_slots[index];
    if (slot->displacement == displacement)
      return slot->conflicted == 0U ? slot->struct_id : AMIGA_OS_STRUCT_ID_NONE;
  }
  return AMIGA_OS_STRUCT_ID_NONE;
}

static int typed_app_address_operand_info(const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *platform_state, const M68kOperandIR *operand, int16_t *out_displacement,
    uint16_t *out_struct_id, uint8_t *out_base_evidence_kind) {
  uint8_t base_reg = 0U, evidence;
  if (out_base_evidence_kind != NULL) *out_base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
  int16_t displacement = 0;
  if (out_displacement != NULL) *out_displacement = 0;
  if (out_struct_id != NULL) *out_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (lookup == NULL || operand == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U) {
    return 0;
  }
  evidence = render_app_base_evidence_kind(lookup, platform_state, base_reg, displacement, 1U);
  if (evidence == M68K_APP_SLOT_BASE_UNSPECIFIED) return 0;
  if (out_base_evidence_kind != NULL) *out_base_evidence_kind = evidence;
  if (out_displacement != NULL) *out_displacement = displacement;
  if (out_struct_id != NULL) *out_struct_id = lookup_typed_app_slot_struct_id(lookup, displacement);
  return 1;
}

static int typed_app_cursor_immediate_delta(const M68kInstructionIR *instruction, int64_t *out_delta) {
  uint32_t immediate;
  int subtract;
  if (instruction == NULL || instruction->operand_count != 2U ||
      !m68k_ir_operand_immediate_value(&instruction->operands[0], &immediate) || immediate > INT32_MAX ||
      (instruction->size_suffix == 'w' && immediate > INT16_MAX)) return 0;
  subtract = instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUB ||
    instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBA || instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBI ||
    instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBQ;
  if (!subtract && instruction->mnemonic_id != M68K_ASM_MNEMONIC_ADD &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_ADDA && instruction->mnemonic_id != M68K_ASM_MNEMONIC_ADDI &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_ADDQ) return 0;
  *out_delta = subtract ? -(int64_t)immediate : (int64_t)immediate;
  return 1;
}

/* Fold the existing raw-bit component, not a source-pointer origin/cursor.
 * Typed pointers retain their existing affine rules and drop the raw bit claim.
 * A computed constant has no renderable immediate producer expression. */
static void typed_address_raw_long_after_immediate(M68kRenderTypedRegValue *value,
    const M68kRenderTypedRegValue *before, const M68kInstructionIR *instruction,
    size_t section_index, uint32_t offset) {
  int64_t delta;
  int pure_raw = before->raw_long_value_known && !before->pointer_value_known &&
    !before->layout_base_id && !before->output && before->struct_id == AMIGA_OS_STRUCT_ID_NONE &&
    !before->type_conflicted && !before->table_origin.has_origin && !before->array_element_count;
  value->raw_long_value_known = value->raw_long_candidate_count = 0U;
  value->raw_long_value = 0U; memset(value->raw_long_candidates, 0, sizeof(value->raw_long_candidates));
  if (!pure_raw) return;
  value->byte_cursor = 0; value->known = 0U;
  if (instruction->size_suffix != 'l' || before->address_value_candidate_overflow ||
      before->raw_long_candidate_count > 4U || !typed_app_cursor_immediate_delta(instruction, &delta)) return;
  value->raw_long_candidate_count = before->raw_long_candidate_count ? before->raw_long_candidate_count : 1U;
  for (uint8_t i = 0U; i < value->raw_long_candidate_count; ++i) {
    uint32_t raw = value->raw_long_candidate_count == 1U ? before->raw_long_value : before->raw_long_candidates[i];
    value->raw_long_candidates[i] = (uint32_t)((int64_t)raw + delta);
  }
  value->raw_long_value = value->raw_long_candidates[0];
  value->raw_long_value_known = value->known = 1U;
  value->provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_CONSTANT_VALUE, section_index, offset);
  value->provenance.producer_operand_index = 1U;
}

/* Local cells reuse canonical storage identities, including conflicted global
 * writer summaries: a conflict there is not a conflict at every program point. */
static uint32_t typed_absolute_storage_id(const M68kRenderLookup *lookup, size_t section, uint32_t address) {
  size_t index;
  for (index = 0U; index < lookup->typed_storage_slot_count && index < UINT32_MAX; ++index) {
    const M68kRenderTypedStorageSlot *slot = &lookup->typed_storage_slots[index];
    if (slot->kind == M68K_RENDER_TYPED_STORAGE_ABSOLUTE && slot->section_index == section &&
        slot->address == address) return (uint32_t)index + 1U;
  }
  return 0U;
}

static const M68kRenderTypedBaseSlot *typed_state_absolute_cell(const M68kRenderTypedState *state, uint32_t id) {
  size_t index;
  if (id == 0U) return NULL;
  for (index = 0U; index < state->base_slot_count; ++index)
    if (state->base_slots[index].known && state->base_slots[index].storage_id == id)
      return &state->base_slots[index];
  return NULL;
}

static void typed_state_set_absolute_cell(M68kRenderTypedState *state, uint32_t id,
    const M68kRenderTypedStoredValue *value) {
  M68kRenderTypedBaseSlot *slot;
  size_t index;
  if (id == 0U || !typed_stored_value_has_useful_info(value)) return;
  for (index = 0U; index < state->base_slot_count; ++index)
    if (state->base_slots[index].storage_id == id) break;
  if (index == state->base_slot_count) {
    if (index == M68K_RENDER_TYPED_BASE_SLOT_LIMIT) return; /* Unknown, never global fallback. */
    ++state->base_slot_count;
  }
  slot = &state->base_slots[index];
  memset(slot, 0, sizeof(*slot));
  slot->known = 1U; slot->base_reg = UINT8_MAX; slot->storage_id = id; slot->value = *value;
}

static void typed_state_forget_absolute_cells(M68kRenderTypedState *state) {
  size_t index = 0U;
  state->absolute_memory_written = 1U;
  while (index < state->base_slot_count) {
    if (state->base_slots[index].storage_id != 0U)
      state->base_slots[index] = state->base_slots[--state->base_slot_count];
    else ++index;
  }
}

static int typed_storage_key_for_lookup_memory_operand(const M68kRenderLookup *lookup,
    const M68kRenderTypedState *state, const M68kRenderPlatformState *platform_state,
    size_t current_section_index, const M68kOperandIR *operand, uint8_t access_kind, uint8_t *out_kind,
    size_t *out_section_index, int32_t *out_displacement, uint32_t *out_address) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint32_t absolute_offset = 0U;
  uint8_t platform_kind = lookup != NULL && lookup->object != NULL
    ? (uint8_t)lookup->object->platform_backend_kind
    : 0U;
  if (out_kind != NULL) *out_kind = 0U;
  if (out_section_index != NULL) *out_section_index = (size_t)-1;
  if (out_displacement != NULL) *out_displacement = 0;
  if (out_address != NULL) *out_address = 0U;
  if (operand == NULL ||
      (access_kind != M68K_SIM_ACCESS_MEMORY_READ && access_kind != M68K_SIM_ACCESS_MEMORY_WRITE)) {
    return 0;
  }
  if (operand_is_address_memory_local(operand, &base_reg, &displacement) && base_reg < 8U &&
      render_state_operand_uses_app_base(platform_state, base_reg, displacement)) {
    if (out_kind != NULL) *out_kind = M68K_RENDER_TYPED_STORAGE_APP_SLOT;
    if (out_displacement != NULL) *out_displacement = displacement;
    return 1;
  }
  if (state != NULL && operand_is_address_memory_local(operand, &base_reg, &displacement) &&
      base_reg < 8U && base_reg != 7U && state->memory_base_regs[base_reg].known) {
    if (out_kind != NULL) *out_kind = M68K_RENDER_TYPED_STORAGE_BASE_SLOT;
    if (out_section_index != NULL) *out_section_index = state->memory_base_regs[base_reg].section_index;
    if (out_displacement != NULL) *out_displacement = displacement;
    if (out_address != NULL) *out_address = state->memory_base_regs[base_reg].offset;
    return 1;
  }
  if (operand_absolute_offset_local(operand, &absolute_offset)) {
    if (platform_facts_v2_address_has_hardware_owner(platform_kind, absolute_offset)) return 0;
    if (out_kind != NULL) *out_kind = M68K_RENDER_TYPED_STORAGE_ABSOLUTE;
    if (out_section_index != NULL)
      *out_section_index = operand->symbol_ref.has_section ? operand->symbol_ref.section_index : current_section_index;
    if (out_address != NULL) *out_address = absolute_offset;
    return 1;
  }
  return 0;
}

/* Unknown aliases clear local absolute values. A known literal write retains
 * only disjoint cells. This is a must-value cache, not a non-alias assumption. */
static void typed_state_note_absolute_write(M68kRenderTypedState *state, const M68kRenderLookup *lookup,
    size_t section, const M68kOperandIR *operand, uint8_t width) {
  uint32_t address;
  size_t index = 0U;
  uint8_t platform = lookup->object != NULL ? lookup->object->platform_backend_kind : 0U;
  int indirect_runtime_address = 0;
  if (!operand_absolute_offset_local(operand, &address)) {
    uint8_t base_reg;
    int16_t displacement;
    M68kRenderTypedMemoryBaseValue effective;
    int has_absolute_cell = 0;
    state->absolute_memory_written = 1U;
    for (size_t i = 0U; i < state->base_slot_count; ++i)
      if (state->base_slots[i].storage_id) { has_absolute_cell = 1; break; }
    /* Nothing to invalidate: retain the write barrier without resolving a
     * runtime view for every ordinary memory instruction. */
    if (!has_absolute_cell) return;
    /* Cells carry runtime addresses. Resolve the current shared source cursor
     * through a whole, unambiguous materialized view; neither a source offset,
     * pointer origin nor app-layout role alone is an effective address. */
    if (!operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U ||
        !typed_memory_base_with_displacement(&state->memory_base_regs[base_reg], displacement, &effective) ||
        !lookup_source_unique_runtime_span(lookup, effective.section_index, effective.offset, width, &address)) {
      typed_state_forget_absolute_cells(state); return;
    }
    indirect_runtime_address = 1;
  } else {
    if (platform_facts_v2_address_has_hardware_owner(platform, address)) return;
    section = operand->symbol_ref.has_section ? operand->symbol_ref.section_index : section;
  }
  state->absolute_memory_written = 1U;
  while (index < state->base_slot_count) {
    M68kRenderTypedBaseSlot *cell = &state->base_slots[index];
    if (cell->storage_id != 0U) {
      const M68kRenderTypedStorageSlot *owner = &lookup->typed_storage_slots[cell->storage_id - 1U];
      if ((indirect_runtime_address || owner->section_index == section) &&
          typed_long_cell_overlaps_write(owner->address, address, width)) {
        *cell = state->base_slots[--state->base_slot_count]; continue;
      }
    }
    ++index;
  }
}

static void typed_state_cache_absolute_store(M68kRenderTypedState *state, const M68kRenderLookup *lookup,
    size_t section, const M68kOperandIR *operand, const M68kRenderTypedStoredValue *value) {
  uint32_t address;
  if (!operand_absolute_offset_local(operand, &address)) return;
  section = operand->symbol_ref.has_section ? operand->symbol_ref.section_index : section;
  typed_state_set_absolute_cell(state, typed_absolute_storage_id(lookup, section, address), value);
}

static const M68kRenderTypedStorageSlot *lookup_typed_storage_slot(const M68kRenderLookup *lookup, uint8_t kind,
    size_t section_index, int32_t displacement, uint32_t address) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->typed_storage_slot_count; ++index) {
    const M68kRenderTypedStorageSlot *slot = &lookup->typed_storage_slots[index];
    if (slot->kind != kind || slot->conflicted != 0U) continue;
    if (kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT) {
      if (slot->displacement != displacement) continue;
    } else if (kind == M68K_RENDER_TYPED_STORAGE_ABSOLUTE) {
      if (slot->section_index != section_index || slot->address != address) continue;
    } else if (kind == M68K_RENDER_TYPED_STORAGE_BASE_SLOT) {
      if (slot->section_index != section_index || slot->address != address ||
          slot->displacement != displacement) {
        continue;
      }
    } else {
      continue;
    }
    return typed_stored_value_has_useful_info(&slot->value) ? slot : NULL;
  }
  return NULL;
}

static uint16_t lookup_policy_pointer_struct_id_for_field(const M68kAnalysisPolicy *policy, uint16_t struct_id,
    int16_t displacement) {
  const M68kAnalysisCustomStruct *custom_struct = lookup_policy_custom_struct_by_id(policy, struct_id);
  if (custom_struct != NULL) {
    uint16_t field_index;
    for (field_index = 0U; field_index < custom_struct->field_count &&
         field_index < M68K_ANALYSIS_CUSTOM_STRUCT_FIELD_LIMIT; ++field_index) {
      const M68kAnalysisCustomStructField *field = &custom_struct->fields[field_index];
      if (field->offset != (uint32_t)displacement ||
          field->value_kind != M68K_ANALYSIS_STRUCT_FIELD_VALUE_STRUCT_POINTER ||
          field->pointer_struct[0] == '\0') {
        continue;
      }
      return lookup_policy_struct_id_by_name(policy, field->pointer_struct);
    }
    return AMIGA_OS_STRUCT_ID_NONE;
  }
  {
    AmigaOsResolvedStructFieldInfo resolved;
    const AmigaOsStructFieldInfo *field;
    if (!amiga_os_resolve_struct_field_by_struct_id(struct_id, displacement, 0, &resolved) ||
        resolved.query_offset != resolved.offset) {
      return AMIGA_OS_STRUCT_ID_NONE;
    }
    field = amiga_os_find_struct_field_by_field_id(resolved.field_id);
    return field != NULL ? field->pointer_struct_id : AMIGA_OS_STRUCT_ID_NONE;
  }
}

static const M68kAnalysisCustomStructField *lookup_policy_pointer_value_field(const M68kAnalysisPolicy *policy,
    uint16_t struct_id, int32_t displacement, const M68kAnalysisCustomStruct **out_struct) {
  const M68kAnalysisCustomStruct *custom_struct = lookup_policy_custom_struct_by_id(policy, struct_id);
  uint16_t field_index;
  if (out_struct != NULL) *out_struct = NULL;
  if (custom_struct == NULL || displacement < 0) return NULL;
  for (field_index = 0U; field_index < custom_struct->field_count &&
       field_index < M68K_ANALYSIS_CUSTOM_STRUCT_FIELD_LIMIT; ++field_index) {
    const M68kAnalysisCustomStructField *field = &custom_struct->fields[field_index];
    if (field->offset != (uint32_t)displacement ||
        field->value_kind == M68K_ANALYSIS_STRUCT_FIELD_VALUE_SCALAR) {
      continue;
    }
    if (out_struct != NULL) *out_struct = custom_struct;
    return field;
  }
  return NULL;
}

static uint16_t lookup_policy_nested_struct_id_for_field(const M68kAnalysisPolicy *policy, uint16_t struct_id,
    int16_t displacement) {
  const M68kAnalysisCustomStruct *custom_struct = lookup_policy_custom_struct_by_id(policy, struct_id);
  if (custom_struct != NULL) {
    uint16_t field_index;
    for (field_index = 0U; field_index < custom_struct->field_count &&
         field_index < M68K_ANALYSIS_CUSTOM_STRUCT_FIELD_LIMIT; ++field_index) {
      const M68kAnalysisCustomStructField *field = &custom_struct->fields[field_index];
      if (field->offset != (uint32_t)displacement || field->struct_name[0] == '\0') continue;
      return lookup_policy_struct_id_by_name(policy, field->struct_name);
    }
    return AMIGA_OS_STRUCT_ID_NONE;
  }
  {
    AmigaOsResolvedStructFieldInfo resolved;
    const AmigaOsStructFieldInfo *field;
    if (!amiga_os_resolve_struct_field_by_struct_id(struct_id, displacement, 0, &resolved) ||
        resolved.query_offset != resolved.offset) {
      return AMIGA_OS_STRUCT_ID_NONE;
    }
    field = amiga_os_find_struct_field_by_field_id(resolved.field_id);
    if (field == NULL || field->pointer_struct_id != AMIGA_OS_STRUCT_ID_NONE || field->size == 0U)
      return AMIGA_OS_STRUCT_ID_NONE;
    return amiga_os_struct_id_from_type_id(field->nested_type_id);
  }
}

static uint16_t typed_pointer_struct_id_for_field_read(const M68kRenderLookup *lookup,
    const M68kRenderTypedState *state, const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  int64_t effective_displacement;
  uint16_t struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (lookup == NULL || state == NULL || operand == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U ||
      !state->addr_regs[base_reg].known) {
    return AMIGA_OS_STRUCT_ID_NONE;
  }
  struct_id = state->addr_regs[base_reg].struct_id;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE) return AMIGA_OS_STRUCT_ID_NONE;
  effective_displacement = (int64_t)state->addr_regs[base_reg].byte_cursor + displacement;
  if (effective_displacement < INT16_MIN || effective_displacement > INT16_MAX)
    return AMIGA_OS_STRUCT_ID_NONE;
  return lookup_policy_pointer_struct_id_for_field(lookup->policy, struct_id, (int16_t)effective_displacement);
}

static int typed_stored_value_from_field_pointer_read(M68kRenderTypedStoredValue *value,
    const M68kRenderLookup *lookup, const M68kRenderTypedState *state, const M68kOperandIR *operand,
    size_t section_index, uint32_t offset) {
  uint16_t struct_id;
  if (value == NULL) return 0;
  struct_id = typed_pointer_struct_id_for_field_read(lookup, state, operand);
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE) return 0;
  typed_stored_value_clear(value);
  value->struct_id = struct_id;
  value->provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_FIELD_POINTER, section_index, offset);
  typed_stored_value_update_known(value);
  return 1;
}

static uint16_t typed_nested_struct_id_for_field_address(const M68kRenderLookup *lookup,
    const M68kRenderTypedState *state, const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  int32_t effective_displacement;
  uint16_t struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (lookup == NULL || state == NULL || operand == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U ||
      !state->addr_regs[base_reg].known) {
    return AMIGA_OS_STRUCT_ID_NONE;
  }
  struct_id = state->addr_regs[base_reg].struct_id;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE) return AMIGA_OS_STRUCT_ID_NONE;
  effective_displacement = state->addr_regs[base_reg].byte_cursor + displacement;
  if (effective_displacement < INT16_MIN || effective_displacement > INT16_MAX)
    return AMIGA_OS_STRUCT_ID_NONE;
  return lookup_policy_nested_struct_id_for_field(lookup->policy, struct_id, (int16_t)effective_displacement);
}

static uint16_t amiga_struct_size_for_struct_id(uint16_t struct_id) {
  int32_t max_end = 0;
  size_t index;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE || amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id) == NULL)
    return 0U;
  for (index = 0U; index < AMIGA_OS_STRUCT_FIELD_COUNT; ++index) {
    const AmigaOsStructFieldInfo *field = amiga_os_struct_field_at(index);
    int32_t end;
    if (field == NULL || field->struct_id != struct_id) continue;
    end = (int32_t)field->offset + (int32_t)field->size;
    if (field->size == 0U) end = field->offset;
    if (end > max_end) max_end = end;
  }
  if (max_end <= 0) return 0U;
  return max_end > UINT16_MAX ? UINT16_MAX : (uint16_t)max_end;
}

static uint16_t amiga_struct_zero_offset_prefix_field_struct_id(uint16_t struct_id) {
  size_t index;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE) return AMIGA_OS_STRUCT_ID_NONE;
  for (index = 0U; index < AMIGA_OS_STRUCT_FIELD_COUNT; ++index) {
    const AmigaOsStructFieldInfo *field = amiga_os_struct_field_at(index);
    uint16_t nested_struct_id;
    if (field == NULL || field->struct_id != struct_id || field->offset != 0 || field->size == 0U)
      continue;
    nested_struct_id = amiga_os_struct_id_from_type_id(field->nested_type_id);
    if (nested_struct_id == AMIGA_OS_STRUCT_ID_NONE)
      nested_struct_id = amiga_os_struct_id_from_type_id(field->field_type_id);
    if (nested_struct_id != AMIGA_OS_STRUCT_ID_NONE && nested_struct_id != struct_id)
      return nested_struct_id;
  }
  return AMIGA_OS_STRUCT_ID_NONE;
}

static int amiga_struct_prefix_chain_contains(uint16_t struct_id, uint16_t prefix_struct_id) {
  uint16_t current_struct_id = struct_id;
  size_t guard;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE || prefix_struct_id == AMIGA_OS_STRUCT_ID_NONE) return 0;
  if (struct_id == prefix_struct_id) return 0;
  for (guard = 0U; guard < AMIGA_OS_STRUCT_BASE_COUNT + AMIGA_OS_STRUCT_FIELD_COUNT + 1U; ++guard) {
    const AmigaOsStructBaseInfo *base = amiga_os_find_struct_base_by_struct_id(current_struct_id);
    uint16_t next_struct_id = AMIGA_OS_STRUCT_ID_NONE;
    if (base != NULL && base->base_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
      next_struct_id = base->base_struct_id;
    } else {
      next_struct_id = amiga_struct_zero_offset_prefix_field_struct_id(current_struct_id);
    }
    if (next_struct_id == AMIGA_OS_STRUCT_ID_NONE) return 0;
    if (next_struct_id == prefix_struct_id) return 1;
    current_struct_id = next_struct_id;
  }
  return 0;
}

static uint16_t typed_struct_id_common_merge(uint16_t left_struct_id, uint16_t right_struct_id) {
  if (left_struct_id == right_struct_id) return left_struct_id;
  if (left_struct_id == AMIGA_OS_STRUCT_ID_NONE || right_struct_id == AMIGA_OS_STRUCT_ID_NONE)
    return AMIGA_OS_STRUCT_ID_NONE;
  if (amiga_struct_prefix_chain_contains(left_struct_id, right_struct_id)) return right_struct_id;
  if (amiga_struct_prefix_chain_contains(right_struct_id, left_struct_id)) return left_struct_id;
  return AMIGA_OS_STRUCT_ID_NONE;
}

static uint16_t typed_struct_id_refined_merge(uint16_t existing_struct_id, uint16_t candidate_struct_id,
    int *out_conflict) {
  if (out_conflict != NULL) *out_conflict = 0;
  if (existing_struct_id == AMIGA_OS_STRUCT_ID_NONE) return candidate_struct_id;
  if (candidate_struct_id == AMIGA_OS_STRUCT_ID_NONE || existing_struct_id == candidate_struct_id)
    return existing_struct_id;
  if (amiga_struct_prefix_chain_contains(candidate_struct_id, existing_struct_id)) return candidate_struct_id;
  if (amiga_struct_prefix_chain_contains(existing_struct_id, candidate_struct_id)) return existing_struct_id;
  if (out_conflict != NULL) *out_conflict = 1;
  return AMIGA_OS_STRUCT_ID_NONE;
}

static uint8_t instruction_size_suffix_bytes_local(char size_suffix) {
  if (size_suffix == 'b') return 1U;
  if (size_suffix == 'w') return 2U;
  if (size_suffix == 'l') return 4U;
  return 0U;
}

static uint16_t typed_struct_id_common_nonroot_merge(uint16_t current_struct_id, uint16_t candidate_struct_id,
    uint16_t root_struct_id, uint8_t *io_conflicted) {
  uint16_t merged;
  if (io_conflicted != NULL && *io_conflicted != 0U) return AMIGA_OS_STRUCT_ID_NONE;
  if (candidate_struct_id == AMIGA_OS_STRUCT_ID_NONE || candidate_struct_id == root_struct_id)
    return AMIGA_OS_STRUCT_ID_NONE;
  if (current_struct_id == AMIGA_OS_STRUCT_ID_NONE) return candidate_struct_id;
  merged = typed_struct_id_common_merge(current_struct_id, candidate_struct_id);
  if (merged == AMIGA_OS_STRUCT_ID_NONE || merged == root_struct_id) {
    if (io_conflicted != NULL) *io_conflicted = 1U;
    return AMIGA_OS_STRUCT_ID_NONE;
  }
  return merged;
}

static void classify_unresolved_typed_access_add_prefix_candidate(uint16_t root_struct_id,
    uint16_t candidate_struct_id, int16_t displacement, uint8_t access_size, uint16_t *candidate_ids,
    size_t *io_candidate_id_count, uint32_t *io_candidate_count, uint32_t *io_exact_size_candidate_count,
    uint16_t *io_unique_container_struct_id, uint16_t *io_exact_size_common_struct_id,
    uint8_t *io_exact_size_conflicted) {
  AmigaOsResolvedStructFieldInfo resolved;
  uint16_t candidate_size;
  size_t index;
  if (candidate_struct_id == AMIGA_OS_STRUCT_ID_NONE || candidate_struct_id == root_struct_id ||
      !amiga_struct_prefix_chain_contains(candidate_struct_id, root_struct_id)) {
    return;
  }
  candidate_size = amiga_struct_size_for_struct_id(candidate_struct_id);
  if (candidate_size == 0U || (int32_t)displacement >= (int32_t)candidate_size) return;
  for (index = 0U; index < *io_candidate_id_count; ++index) {
    if (candidate_ids[index] == candidate_struct_id) return;
  }
  if (*io_candidate_id_count < 64U) candidate_ids[(*io_candidate_id_count)++] = candidate_struct_id;
  ++*io_candidate_count;
  *io_unique_container_struct_id =
    *io_candidate_count == 1U ? candidate_struct_id : AMIGA_OS_STRUCT_ID_NONE;
  if (access_size != 0U &&
      amiga_os_resolve_struct_field_by_struct_id(candidate_struct_id, displacement, 0, &resolved) &&
      resolved.offset == displacement && resolved.size == access_size) {
    char exact_field_expr[96];
    if (!amiga_os_resolve_struct_field_symbol_expr_by_struct_id(candidate_struct_id, displacement, 0,
        exact_field_expr, sizeof(exact_field_expr))) {
      return;
    }
    ++*io_exact_size_candidate_count;
    *io_exact_size_common_struct_id = typed_struct_id_common_nonroot_merge(*io_exact_size_common_struct_id,
      candidate_struct_id, root_struct_id, io_exact_size_conflicted);
  }
}

static void classify_unresolved_typed_access(uint16_t root_struct_id, int16_t displacement, uint16_t struct_size,
    uint8_t access_size, uint8_t *out_classification, uint16_t *out_candidate_count, char *out_container_struct_name,
    size_t container_struct_name_size, char *out_container_field_expr, size_t container_field_expr_size,
    uint16_t *out_container_struct_id) {
  uint32_t candidate_count = 0U, exact_size_candidate_count = 0U;
  uint16_t unique_container_struct_id = AMIGA_OS_STRUCT_ID_NONE, exact_size_common_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  uint16_t candidate_ids[64];
  size_t candidate_id_count = 0U;
  uint8_t exact_size_conflicted = 0U;
  int32_t displacement32 = (int32_t)displacement;
  size_t index;
  if (out_classification != NULL)
    *out_classification = M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_FIELD_GAP;
  if (out_candidate_count != NULL) *out_candidate_count = 0U;
  if (out_container_struct_name != NULL && container_struct_name_size > 0U) out_container_struct_name[0] = '\0';
  if (out_container_field_expr != NULL && container_field_expr_size > 0U) out_container_field_expr[0] = '\0';
  if (out_container_struct_id != NULL) *out_container_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (root_struct_id == AMIGA_OS_STRUCT_ID_NONE) return;
  if (struct_size > 0U && (displacement32 < 0 || displacement32 >= (int32_t)struct_size)) {
    if (out_classification != NULL)
      *out_classification = M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_CUSTOM_TAIL_OR_MISTYPED_BASE;
  }
  if (struct_size == 0U || displacement32 < (int32_t)struct_size || displacement32 < 0) return;
  for (index = 0U; index < AMIGA_OS_STRUCT_BASE_COUNT; ++index) {
    const AmigaOsStructBaseInfo *base = amiga_os_struct_base_at(index);
    if (base == NULL || base->struct_id == root_struct_id) continue;
    classify_unresolved_typed_access_add_prefix_candidate(root_struct_id, base->struct_id, displacement,
      access_size, candidate_ids, &candidate_id_count, &candidate_count, &exact_size_candidate_count,
      &unique_container_struct_id, &exact_size_common_struct_id, &exact_size_conflicted);
  }
  if (candidate_count == 0U) {
    for (index = 0U; index < AMIGA_OS_STRUCT_FIELD_COUNT; ++index) {
      const AmigaOsStructFieldInfo *field = amiga_os_struct_field_at(index);
      uint16_t nested_struct_id;
      if (field == NULL || field->offset != 0 || field->size == 0U || field->struct_id == root_struct_id)
        continue;
      nested_struct_id = amiga_os_struct_id_from_type_id(field->nested_type_id);
      if (nested_struct_id == AMIGA_OS_STRUCT_ID_NONE)
        nested_struct_id = amiga_os_struct_id_from_type_id(field->field_type_id);
      if (nested_struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
      if (nested_struct_id != root_struct_id && !amiga_struct_prefix_chain_contains(nested_struct_id, root_struct_id))
        continue;
      classify_unresolved_typed_access_add_prefix_candidate(root_struct_id, field->struct_id, displacement,
        access_size, candidate_ids, &candidate_id_count, &candidate_count, &exact_size_candidate_count,
        &unique_container_struct_id, &exact_size_common_struct_id, &exact_size_conflicted);
    }
  }
  if (candidate_count == 0U) return;
  if (out_classification != NULL)
    *out_classification = M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION;
  if (out_candidate_count != NULL)
    *out_candidate_count = candidate_count > UINT16_MAX ? UINT16_MAX : (uint16_t)candidate_count;
  if (unique_container_struct_id == AMIGA_OS_STRUCT_ID_NONE && exact_size_candidate_count != 0U &&
      exact_size_conflicted == 0U)
    unique_container_struct_id = exact_size_common_struct_id;
  if (unique_container_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    const char *container_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, unique_container_struct_id);
    if (out_container_struct_id != NULL) *out_container_struct_id = unique_container_struct_id;
    if (container_name != NULL && container_name[0] != '\0' &&
        out_container_struct_name != NULL && container_struct_name_size > 0U) {
      snprintf(out_container_struct_name, container_struct_name_size, "%s", container_name);
    }
    if (out_container_field_expr != NULL && container_field_expr_size > 0U) {
      (void)amiga_os_resolve_struct_field_symbol_expr_by_struct_id(unique_container_struct_id, displacement, 0,
        out_container_field_expr, container_field_expr_size);
    }
  }
}

static int typed_value_for_memory_read_operand(const M68kRenderLookup *lookup, const M68kRenderTypedState *state,
    const M68kRenderPlatformState *platform_state, size_t current_section_index, const M68kOperandIR *operand,
    uint8_t access_kind, M68kRenderTypedStoredValue *out_value, M68kRenderTypedStorageOrigin *out_origin) {
  uint8_t base_reg = 0U, storage_kind = 0U;
  int16_t base_displacement = 0, stack_displacement = 0;
  size_t storage_section = (size_t)-1;
  int32_t storage_displacement = 0;
  uint32_t storage_address = 0U;
  const M68kRenderTypedStoredValue *value = NULL;
  const M68kRenderTypedStorageSlot *slot = NULL;
  M68kRenderTypedStoredValue inferred_type;
  if (out_value != NULL) typed_stored_value_clear(out_value);
  if (out_origin != NULL) typed_origin_clear(out_origin);
  if (lookup == NULL || state == NULL || operand == NULL || out_value == NULL ||
      access_kind != M68K_SIM_ACCESS_MEMORY_READ) {
    return 0;
  }
  if (operand_is_postinc_a7_local(operand)) {
    value = typed_state_stack_slot_value(state, 0);
    if (value != NULL) {
      *out_value = *value;
      if (out_value->provenance.kind == M68K_PLATFORM_TYPE_PROVENANCE_NONE &&
          !out_value->provenance.merge_conflicted)
        out_value->provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_STACK_SLOT,
          current_section_index, 0U);
      if (out_origin != NULL) {
        out_origin->kind = M68K_RENDER_TYPED_ORIGIN_STACK_SLOT;
        out_origin->displacement = 0;
      }
      return 1;
    }
  }
  if (operand_is_stack_displacement_local(operand, &stack_displacement)) {
    value = typed_state_stack_slot_value(state, stack_displacement);
    if (value != NULL) {
      *out_value = *value;
      if (out_value->provenance.kind == M68K_PLATFORM_TYPE_PROVENANCE_NONE &&
          !out_value->provenance.merge_conflicted)
        out_value->provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_STACK_SLOT, current_section_index, 0U);
      if (out_origin != NULL) {
        out_origin->kind = M68K_RENDER_TYPED_ORIGIN_STACK_SLOT;
        out_origin->displacement = stack_displacement;
      }
      return 1;
    }
  }
  if (operand_is_address_memory_local(operand, &base_reg, &base_displacement) && base_reg < 8U && base_reg != 7U &&
      !render_state_operand_uses_app_base(platform_state, base_reg, base_displacement)) {
    if (state->addr_regs[base_reg].known && state->addr_regs[base_reg].struct_id != AMIGA_OS_STRUCT_ID_NONE) {
      int32_t field_displacement = state->addr_regs[base_reg].byte_cursor + (int32_t)base_displacement;
      value = typed_state_field_slot_value(state, base_reg, state->addr_regs[base_reg].struct_id,
        field_displacement);
      if (value != NULL) {
        *out_value = *value;
        if (out_origin != NULL) {
          out_origin->kind = M68K_RENDER_TYPED_ORIGIN_BASE_SLOT;
          out_origin->base_reg = base_reg;
          out_origin->displacement = field_displacement;
        }
        return 1;
      }
    }
    value = typed_state_base_slot_value(state, base_reg, base_displacement);
    if (value != NULL) {
      *out_value = *value;
      if (out_value->provenance.kind == M68K_PLATFORM_TYPE_PROVENANCE_NONE &&
          !out_value->provenance.merge_conflicted)
        out_value->provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_BASE_SLOT, current_section_index, 0U);
      if (out_origin != NULL) {
        out_origin->kind = M68K_RENDER_TYPED_ORIGIN_BASE_SLOT;
        out_origin->base_reg = base_reg;
        out_origin->displacement = base_displacement;
      }
      return 1;
    }
  }
  {
    if (!typed_storage_key_for_lookup_memory_operand(lookup, state, platform_state, current_section_index, operand,
        access_kind, &storage_kind, &storage_section, &storage_displacement, &storage_address)) {
      return 0;
    }
    if (storage_kind == M68K_RENDER_TYPED_STORAGE_ABSOLUTE) {
      const M68kRenderTypedBaseSlot *cell = typed_state_absolute_cell(state,
        typed_absolute_storage_id(lookup, storage_section, storage_address));
      if (cell != NULL) value = &cell->value;
      else if (state->absolute_memory_written) return 0;
    }
    if (value == NULL) {
      slot = lookup_typed_storage_slot(lookup, storage_kind, storage_section, storage_displacement, storage_address);
      value = slot != NULL ? &slot->value : NULL;
      /* An inferred cursor writer elsewhere is not a reaching definition at
       * this entry, including a store later in the same function. */
      if (storage_kind == M68K_RENDER_TYPED_STORAGE_ABSOLUTE && value != NULL) {
        if (value->app_address_known) return 0;
        /* This is a cross-program writer/type summary, not a reaching
         * definition. Keep its pointee contract, never promote its numeric
         * bits or whole-base identity at an earlier/unrelated read. Declared
         * layout-base loads are handled independently by platform metadata. */
        inferred_type = *value;
        inferred_type.layout_base_id = 0U; inferred_type.entry_value_id = 0U;
        typed_stored_value_forget_concrete_long(&inferred_type);
        if (!typed_stored_value_has_useful_info(&inferred_type)) return 0;
        inferred_type.provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_LOOKUP_STORAGE,
          slot->source_section_index, slot->source_offset);
        value = &inferred_type;
      }
    }
  }
  if (value == NULL) return 0;
  *out_value = *value;
  if (out_value->provenance.kind == M68K_PLATFORM_TYPE_PROVENANCE_NONE &&
      !out_value->provenance.merge_conflicted)
    out_value->provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_LOOKUP_STORAGE,
      slot != NULL ? slot->source_section_index : current_section_index,
      slot != NULL ? slot->source_offset : 0U);
  if (out_origin != NULL) {
    out_origin->kind = M68K_RENDER_TYPED_ORIGIN_LOOKUP_STORAGE;
    out_origin->storage_kind = storage_kind;
    out_origin->section_index = storage_section;
    out_origin->displacement = storage_displacement;
    out_origin->address = storage_address;
  }
  return 1;
}

static int typed_stored_value_promote_struct(M68kRenderTypedStoredValue *value, uint16_t root_struct_id,
    uint16_t refined_struct_id) {
  if (value == NULL || root_struct_id == AMIGA_OS_STRUCT_ID_NONE ||
      refined_struct_id == AMIGA_OS_STRUCT_ID_NONE || value->struct_id != root_struct_id ||
      !amiga_struct_prefix_chain_contains(refined_struct_id, root_struct_id)) {
    return 0;
  }
  value->struct_id = refined_struct_id;
  value->output = NULL;
  typed_stored_value_update_known(value);
  return 1;
}

static int render_lookup_promote_typed_storage_slot(M68kRenderLookup *lookup, const M68kRenderTypedStorageOrigin *origin,
    uint16_t root_struct_id, uint16_t refined_struct_id, size_t source_section_index, uint32_t source_offset,
    int *out_changed) {
  size_t index;
  if (out_changed != NULL) *out_changed = 0;
  if (lookup == NULL || origin == NULL || origin->kind != M68K_RENDER_TYPED_ORIGIN_LOOKUP_STORAGE)
    return 0;
  if (origin->storage_kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT) {
    return render_lookup_add_typed_app_slot(lookup, (int16_t)origin->displacement, refined_struct_id,
      source_section_index, source_offset, out_changed);
  }
  for (index = 0U; index < lookup->typed_storage_slot_count; ++index) {
    M68kRenderTypedStorageSlot *slot = &lookup->typed_storage_slots[index];
    if (slot->conflicted != 0U || !typed_storage_keys_match(slot, origin->storage_kind, origin->section_index,
        origin->displacement, origin->address)) {
      continue;
    }
    if (typed_stored_value_promote_struct(&slot->value, root_struct_id, refined_struct_id)) {
      slot->source_section_index = source_section_index;
      slot->source_offset = source_offset;
      slot->value.provenance =
        typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
      if (out_changed != NULL) *out_changed = 1;
    }
    return 0;
  }
  return 0;
}

static int typed_state_promote_origin_struct(M68kRenderLookup *lookup, M68kRenderTypedState *state,
    const M68kRenderTypedStorageOrigin *origin, uint16_t root_struct_id, uint16_t refined_struct_id,
    size_t source_section_index, uint32_t source_offset, int *out_changed) {
  size_t index;
  int changed = 0;
  if (out_changed != NULL) *out_changed = 0;
  if (state == NULL || origin == NULL || origin->kind == M68K_RENDER_TYPED_ORIGIN_NONE) return 0;
  if (origin->kind == M68K_RENDER_TYPED_ORIGIN_STACK_SLOT) {
    for (index = 0U; index < state->stack_slot_count; ++index) {
      M68kRenderTypedStackSlot *slot = &state->stack_slots[index];
      if (slot->known != 0U && slot->displacement == origin->displacement &&
          typed_stored_value_promote_struct(&slot->value, root_struct_id, refined_struct_id)) {
        slot->value.provenance =
          typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
        changed = 1;
        break;
      }
    }
  } else if (origin->kind == M68K_RENDER_TYPED_ORIGIN_BASE_SLOT) {
    M68kRenderTypedBaseSlot *slot = typed_state_mutable_base_slot_entry(state, origin->base_reg,
      (int16_t)origin->displacement);
    if (slot != NULL && typed_stored_value_promote_struct(&slot->value, root_struct_id, refined_struct_id)) {
      slot->value.provenance =
        typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
      changed = 1;
    }
  } else if (origin->kind == M68K_RENDER_TYPED_ORIGIN_LOOKUP_STORAGE) {
    if (render_lookup_promote_typed_storage_slot(lookup, origin, root_struct_id, refined_struct_id,
        source_section_index, source_offset, &changed) != 0) {
      return -1;
    }
  }
  if (out_changed != NULL) *out_changed = changed;
  return 0;
}

static int typed_state_refine_address_reg_from_prefix(M68kRenderLookup *lookup, M68kRenderTypedState *state,
    uint8_t reg_index, uint16_t root_struct_id, uint16_t refined_struct_id, size_t source_section_index,
    uint32_t source_offset, int *out_changed) {
  int origin_changed = 0;
  if (out_changed != NULL) *out_changed = 0;
  if (state == NULL || reg_index >= 8U || root_struct_id == AMIGA_OS_STRUCT_ID_NONE ||
      refined_struct_id == AMIGA_OS_STRUCT_ID_NONE || !state->addr_regs[reg_index].known ||
      state->addr_regs[reg_index].struct_id != root_struct_id ||
      !amiga_struct_prefix_chain_contains(refined_struct_id, root_struct_id)) {
    return 0;
  }
  if (typed_state_promote_origin_struct(lookup, state, &state->addr_regs[reg_index].origin, root_struct_id,
      refined_struct_id, source_section_index, source_offset, &origin_changed) != 0) {
    return -1;
  }
  state->addr_regs[reg_index].struct_id = refined_struct_id;
  state->addr_regs[reg_index].output = NULL;
  state->addr_regs[reg_index].provenance =
    typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
  if (out_changed != NULL) *out_changed = 1;
  (void)origin_changed;
  return 0;
}

static int typed_reg_value_same_type_source(const M68kRenderTypedRegValue *left,
    const M68kRenderTypedStoredValue *right) {
  if (left == NULL || right == NULL || left->known == 0U || !typed_stored_value_has_useful_info(right))
    return 0;
  if (left->output != NULL && left->output == right->output) return 1;
  return left->struct_id != AMIGA_OS_STRUCT_ID_NONE && left->struct_id == right->struct_id &&
    typed_provenances_equal(&left->provenance, &right->provenance);
}

static int typed_state_promote_matching_stored_values(M68kRenderTypedState *state,
    const M68kRenderTypedRegValue *source, uint16_t root_struct_id, uint16_t refined_struct_id,
    size_t source_section_index, uint32_t source_offset) {
  size_t index;
  int changed = 0;
  if (state == NULL || source == NULL || root_struct_id == AMIGA_OS_STRUCT_ID_NONE ||
      refined_struct_id == AMIGA_OS_STRUCT_ID_NONE) {
    return 0;
  }
  for (index = 0U; index < state->stack_slot_count; ++index) {
    M68kRenderTypedStackSlot *slot = &state->stack_slots[index];
    if (slot->known != 0U && typed_reg_value_same_type_source(source, &slot->value) &&
        typed_stored_value_promote_struct(&slot->value, root_struct_id, refined_struct_id)) {
      slot->value.provenance =
        typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
      changed = 1;
    }
  }
  for (index = 0U; index < state->base_slot_count; ++index) {
    M68kRenderTypedBaseSlot *slot = &state->base_slots[index];
    if (slot->known != 0U && typed_reg_value_same_type_source(source, &slot->value) &&
        typed_stored_value_promote_struct(&slot->value, root_struct_id, refined_struct_id)) {
      slot->value.provenance =
        typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
      changed = 1;
    }
  }
  return changed;
}

static int instruction_stores_typed_reg_to_a6_slot(const M68kRenderTypedState *state,
    const M68kInstructionIR *instruction, int a6_is_known_library_base, int16_t *out_displacement,
    const AmigaOsCallOutputInfo **out_output) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const AmigaOsCallOutputInfo *output;
  if (out_displacement != NULL) *out_displacement = 0;
  if (out_output != NULL) *out_output = NULL;
  if (state == NULL || instruction == NULL || out_displacement == NULL || out_output == NULL) return 0;
  if (a6_is_known_library_base) return 0;
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || instruction->size_suffix != 'l' ||
      instruction->operand_count != 2U) {
    return 0;
  }
  output = typed_state_output_for_operand(state, &instruction->operands[0], NULL, NULL);
  if (output == NULL) return 0;
  if (!operand_is_address_displacement_local(&instruction->operands[1], &base_reg, &displacement) ||
      base_reg != 6U) {
    return 0;
  }
  *out_displacement = displacement;
  *out_output = output;
  return 1;
}

/* A single ordinary memory access has an unambiguous auto-update cursor.
 * Require a bounded field access and exclude stack, multi-transfer and shared
 * base/update forms. Generated metadata owns access kind and transfer width. */
static int typed_single_auto_update_cursor(const M68kRenderLookup *lookup,
    const M68kRenderTypedState *state, const M68kInstructionIR *instruction, size_t operand_index,
    uint8_t *out_reg, uint8_t *out_width) {
  const M68kSimFormMetadata *metadata;
  const M68kOperandIR *operand;
  const M68kRenderTypedRegValue *value;
  uint16_t struct_size;
  uint8_t width, reg, shape;
  size_t other_index;
  if (lookup == NULL || state == NULL || instruction == NULL || operand_index >= instruction->operand_count ||
      operand_index >= 4U) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  operand = &instruction->operands[operand_index];
  if (metadata == NULL || metadata->operation_class == M68K_SIM_CLASS_MULTI_REGISTER_TRANSFER ||
      metadata->multi_transfer_direction != M68K_SIM_MULTI_NONE || metadata->sp_effect_count != 0U ||
      instruction_has_call_flow_local(instruction) ||
      !((metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_READ &&
         metadata->source_operand_index == operand_index) ||
        (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_WRITE &&
         metadata->dest_operand_index == operand_index)) ||
      (metadata->operand_width_modes[operand_index] != M68K_SIM_WIDTH_FIXED &&
       metadata->operand_width_modes[operand_index] != M68K_SIM_WIDTH_INSTRUCTION_SIZE) ||
      (metadata->operand_width_modes[operand_index] == M68K_SIM_WIDTH_INSTRUCTION_SIZE &&
       instruction_size_suffix_bytes_local(instruction->size_suffix) == 0U) ||
      operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_reg >= 7U ||
      (m68k_instruction_operand_decoded_ea_shape(operand) != M68K_SIM_EA_SHAPE_POSTINCREMENT &&
       m68k_instruction_operand_decoded_ea_shape(operand) != M68K_SIM_EA_SHAPE_PREDECREMENT)) return 0;
  shape = m68k_instruction_operand_decoded_ea_shape(operand);
  if (metadata->operand_ea_register_updates[operand_index] != M68K_SIM_EA_UPDATE_NONE &&
      metadata->operand_ea_register_updates[operand_index] != (shape == M68K_SIM_EA_SHAPE_POSTINCREMENT
        ? M68K_SIM_EA_UPDATE_POSTINCREMENT : M68K_SIM_EA_UPDATE_PREDECREMENT)) return 0;
  reg = operand->value.ea_reg;
  value = &state->addr_regs[reg];
  width = m68k_sim_operand_width_bytes(instruction, (uint8_t)operand_index);
  struct_size = lookup_policy_struct_size_by_id(lookup->policy, value->struct_id);
  /* A table entry contains a pointee pointer; the table cursor is not a
   * cursor within that pointee's fields. Keep their existing transfer lane. */
  if (state->memory_base_regs[reg].pointer_table_known) return 0;
  if (!value->known || value->type_conflicted || (width != 1U && width != 2U && width != 4U) ||
      struct_size == 0U || value->byte_cursor < 0 || value->byte_cursor > struct_size ||
      (shape == M68K_SIM_EA_SHAPE_POSTINCREMENT
        ? width > (uint32_t)struct_size - (uint32_t)value->byte_cursor
        : width > (uint32_t)value->byte_cursor) ||
      (value->array_element_count != 0U && value->array_element_index >= value->array_element_count)) return 0;
  for (other_index = 0U; other_index < instruction->operand_count; ++other_index) {
    const M68kOperandIR *other = &instruction->operands[other_index];
    uint8_t other_reg = 0U;
    uint8_t shape;
    if (other_index == operand_index) continue;
    if (operand_address_register_index_local(other, &other_reg) && other_reg == reg) return 0;
    shape = m68k_instruction_operand_decoded_ea_shape(other);
    if (shape == M68K_SIM_EA_SHAPE_POSTINCREMENT || shape == M68K_SIM_EA_SHAPE_PREDECREMENT) return 0;
    if (other->kind != M68K_ASM_OPERAND_EA && other->kind != M68K_ASM_OPERAND_BF_EA) continue;
    if ((shape == M68K_SIM_EA_SHAPE_INDIRECT || shape == M68K_SIM_EA_SHAPE_POSTINCREMENT ||
         shape == M68K_SIM_EA_SHAPE_PREDECREMENT || shape == M68K_SIM_EA_SHAPE_DISPLACEMENT ||
         shape == M68K_SIM_EA_SHAPE_INDEX) && other->value.ea_reg == reg) return 0;
    if (shape == M68K_SIM_EA_SHAPE_INDEX && other->value.index_is_address && other->value.index_reg == reg)
      return 0;
  }
  if (out_reg != NULL) *out_reg = reg;
  if (out_width != NULL) *out_width = width;
  return 1;
}

static int typed_access_has_unmodelled_base_update(const M68kRenderLookup *lookup,
    const M68kRenderTypedState *state, const M68kInstructionIR *instruction, size_t access_index,
    uint8_t base_reg, uint8_t *io_access_size) {
  size_t update_index;
  for (update_index = 0U; update_index < instruction->operand_count; ++update_index) {
    const M68kOperandIR *update = &instruction->operands[update_index];
    uint8_t shape;
    if (update->kind != M68K_ASM_OPERAND_EA || update->value.ea_reg != base_reg) continue;
    shape = m68k_instruction_operand_decoded_ea_shape(update);
    if (shape != M68K_SIM_EA_SHAPE_POSTINCREMENT && shape != M68K_SIM_EA_SHAPE_PREDECREMENT) continue;
    if (update_index != access_index ||
        !typed_single_auto_update_cursor(lookup, state, instruction, update_index, NULL, io_access_size)) return 1;
  }
  return 0;
}

static int render_lookup_record_typed_struct_accesses(M68kRenderLookup *lookup, size_t section_index,
    M68kRenderTypedState *state, const M68kInstructionIR *instruction, uint32_t offset, int record_accesses,
    int *io_changed) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (lookup == NULL || state == NULL || instruction == NULL) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    uint8_t base_reg = 0U, classification = M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_FIELD_GAP;
    uint8_t auto_update = M68K_SIM_EA_UPDATE_NONE;
    int32_t displacement = 0, effective_displacement = 0, base_cursor = 0;
    uint16_t struct_id, struct_size, container_struct_id = AMIGA_OS_STRUCT_ID_NONE, container_candidate_count = 0U;
    uint16_t conflict_struct_id = AMIGA_OS_STRUCT_ID_NONE;
    int16_t array_element_addend = 0;
    int16_t field_displacement;
    uint8_t access_size;
    char container_struct_name[64], container_field_expr[96];
    int refinement_applied = 0;
    int type_conflicted = 0;
    M68kRenderResolvedStructField field;
    M68kRenderTypedProvenance app_slot_provenance;
    const M68kRenderTypedProvenance *provenance = NULL;
    const M68kAddressValueTableOriginIR *table_origin = NULL;
    container_struct_name[0] = '\0';
    container_field_expr[0] = '\0';
    struct_id = AMIGA_OS_STRUCT_ID_NONE;
    if (metadata != NULL && metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_BRANCH_TARGET)
      continue;
    if (operand->kind == M68K_ASM_OPERAND_EA &&
        (operand->value.ea_mode == 3U || operand->value.ea_mode == 4U) && operand->value.ea_reg < 8U) {
      base_reg = operand->value.ea_reg;
      auto_update = operand->value.ea_mode == 3U ? M68K_SIM_EA_UPDATE_POSTINCREMENT :
        M68K_SIM_EA_UPDATE_PREDECREMENT;
    } else if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 6U && operand->value.ea_reg < 8U) {
      base_reg = operand->value.ea_reg;
      displacement = operand->value.full_ext_base_disp_size != 0U
        ? (int32_t)operand->value.full_ext_base_disp_value
        : (int32_t)operand->value.value;
    } else {
      int16_t fixed_displacement;
      if (!operand_is_address_memory_local(operand, &base_reg, &fixed_displacement) || base_reg >= 8U) continue;
      displacement = fixed_displacement;
    }
    if (struct_id == AMIGA_OS_STRUCT_ID_NONE && state->addr_regs[base_reg].known) {
      struct_id = state->addr_regs[base_reg].struct_id;
      provenance = &state->addr_regs[base_reg].provenance;
      table_origin = &state->addr_regs[base_reg].table_origin;
    } else if (struct_id == AMIGA_OS_STRUCT_ID_NONE && state->addr_regs[base_reg].type_conflicted != 0U) {
      struct_id = state->addr_regs[base_reg].struct_id;
      conflict_struct_id = state->addr_regs[base_reg].conflict_struct_id;
      provenance = &state->addr_regs[base_reg].provenance;
      table_origin = &state->addr_regs[base_reg].table_origin;
      type_conflicted = 1;
    } else if (struct_id == AMIGA_OS_STRUCT_ID_NONE && state->app_addr_regs[base_reg].known) {
      struct_id = lookup_typed_app_slot_struct_id(lookup, state->app_addr_regs[base_reg].displacement);
      if (struct_id == AMIGA_OS_STRUCT_ID_NONE)
        struct_id = lookup_app_base_field_slot_struct_id(lookup, state->app_addr_regs[base_reg].displacement);
      app_slot_provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_APP_SLOT, section_index, offset);
      provenance = &app_slot_provenance;
    } else {
      continue;
    }
    if (struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
    if (state->addr_regs[base_reg].known) base_cursor = state->addr_regs[base_reg].byte_cursor;
    struct_size = lookup_policy_struct_size_by_id(lookup->policy, struct_id);
    access_size = instruction_size_suffix_bytes_local(instruction->size_suffix);
    if (auto_update != M68K_SIM_EA_UPDATE_NONE)
      access_size = m68k_sim_operand_width_bytes(instruction, (uint8_t)operand_index);
    if (auto_update == M68K_SIM_EA_UPDATE_PREDECREMENT) displacement = -(int32_t)access_size;
    if ((base_cursor > 0 && displacement > INT32_MAX - base_cursor) ||
        (base_cursor < 0 && displacement < INT32_MIN - base_cursor)) {
      base_cursor = 0;
    }
    effective_displacement = displacement + base_cursor;
    if (operand->value.ea_mode == 6U) {
      if (record_accesses) {
        const char *root_struct_name = lookup_policy_struct_name_by_id(lookup->policy, struct_id);
        if (root_struct_name != NULL &&
            render_lookup_add_unresolved_typed_access_by_names(lookup, section_index, offset,
              (uint8_t)operand_index, base_reg, effective_displacement, root_struct_name, struct_size, access_size,
              M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_INDEXED_DYNAMIC, 0U, NULL, NULL, 0U, NULL,
              provenance) != 0) {
          return -1;
        }
      }
      continue;
    }
    if (type_conflicted) {
      if (record_accesses) {
        const char *root_struct_name = lookup_policy_struct_name_by_id(lookup->policy, struct_id);
        const char *conflict_struct_name = lookup_policy_struct_name_by_id(lookup->policy, conflict_struct_id);
        if (root_struct_name != NULL &&
            render_lookup_add_unresolved_typed_access_by_names(lookup, section_index, offset,
              (uint8_t)operand_index, base_reg, effective_displacement, root_struct_name, struct_size, access_size,
              M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_TYPE_CONFLICT,
              conflict_struct_name != NULL ? 2U : 1U, conflict_struct_name, NULL, 0U, NULL, provenance) != 0) {
          return -1;
        }
      }
      continue;
    }
    if (typed_access_has_unmodelled_base_update(lookup, state, instruction, operand_index, base_reg, &access_size)) {
      if (record_accesses) {
        const char *root_struct_name = lookup_policy_struct_name_by_id(lookup->policy, struct_id);
        if (root_struct_name != NULL &&
            render_lookup_add_unresolved_typed_access_by_names(lookup, section_index, offset,
              (uint8_t)operand_index, base_reg, effective_displacement, root_struct_name, struct_size, access_size,
              M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_AUTO_UPDATE_CURSOR, 0U, NULL, NULL, 0U, NULL,
              provenance) != 0) {
          return -1;
        }
      }
      continue;
    }
    if (effective_displacement < INT16_MIN || effective_displacement > INT16_MAX) {
      if (record_accesses) {
        const char *root_struct_name = lookup_policy_struct_name_by_id(lookup->policy, struct_id);
        if (root_struct_name != NULL && render_lookup_add_unresolved_typed_access_by_names(lookup,
            section_index, offset, (uint8_t)operand_index, base_reg, effective_displacement, root_struct_name,
            struct_size, access_size, M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_FIELD_GAP, 0U, NULL, NULL,
            0U, NULL, provenance) != 0) return -1;
      }
      continue;
    }
    field_displacement = (int16_t)effective_displacement;
    if (state->addr_regs[base_reg].known && state->addr_regs[base_reg].array_element_count != 0U &&
        struct_size != 0U) {
      int64_t array_offset = (int64_t)state->addr_regs[base_reg].array_element_index * (int64_t)struct_size +
        effective_displacement;
      if (array_offset >= 0 && (uint64_t)array_offset <
          (uint64_t)state->addr_regs[base_reg].array_element_count * struct_size) {
        array_element_addend = (int16_t)((int32_t)((uint64_t)array_offset / struct_size) -
          (int32_t)state->addr_regs[base_reg].array_element_index);
        field_displacement = (int16_t)((uint64_t)array_offset % struct_size);
      }
    }
    if (!lookup_policy_resolve_struct_field(lookup->policy, struct_id, field_displacement, access_size, &field)) {
      int refined_exact_field_access_recorded = 0;
      if (amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id) != NULL) {
        classify_unresolved_typed_access(struct_id, field_displacement, struct_size, access_size,
          &classification, &container_candidate_count,
          container_struct_name, sizeof(container_struct_name), container_field_expr, sizeof(container_field_expr),
          &container_struct_id);
      }
      if (classification == M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION &&
          container_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
        if (typed_state_refine_address_reg_from_prefix(lookup, state, base_reg, struct_id, container_struct_id,
            section_index, offset, &refinement_applied) != 0) {
          return -1;
        }
        if (refinement_applied && io_changed != NULL) *io_changed = 1;
      }
      if (record_accesses) {
        if (refinement_applied && container_struct_id != AMIGA_OS_STRUCT_ID_NONE && access_size != 0U &&
            lookup_policy_resolve_struct_field(lookup->policy, container_struct_id, field_displacement, access_size, &field) &&
            field.offset == field_displacement && field.size == access_size &&
            field.field_expr[0] != '\0') {
          M68kRenderTypedProvenance prefix_provenance =
            typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_PREFIX_REFINEMENT, section_index, offset);
          if (render_lookup_add_typed_access_by_names(lookup, section_index, offset, (uint8_t)operand_index,
              base_reg, (int16_t)displacement, lookup_policy_struct_size_by_id(lookup->policy, container_struct_id),
              array_element_addend, base_cursor, 0U, &field,
              &prefix_provenance, NULL) != 0) {
            return -1;
          }
          refined_exact_field_access_recorded = 1;
        }
        if (!refined_exact_field_access_recorded) {
          const char *root_struct_name = lookup_policy_struct_name_by_id(lookup->policy, struct_id);
          if (root_struct_name != NULL &&
              render_lookup_add_unresolved_typed_access_by_names(lookup, section_index, offset,
                (uint8_t)operand_index, base_reg, effective_displacement, root_struct_name, struct_size, access_size, classification,
                container_candidate_count, container_struct_name, container_field_expr,
                (uint8_t)(refinement_applied ? 1U : 0U),
                refinement_applied ? lookup_policy_struct_name_by_id(lookup->policy, container_struct_id) : NULL,
                provenance) != 0) {
            return -1;
          }
        }
      }
      continue;
    }
    if (field.field_expr[0] == '\0') {
      if (record_accesses) {
        const char *root_struct_name = lookup_policy_struct_name_by_id(lookup->policy, struct_id);
        if (root_struct_name != NULL &&
            render_lookup_add_unresolved_typed_access_by_names(lookup, section_index, offset,
              (uint8_t)operand_index, base_reg, effective_displacement, root_struct_name, struct_size, access_size,
              M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_FIELD_GAP, 0U, NULL, NULL, 0U, NULL, provenance) != 0) {
          return -1;
        }
      }
      continue;
    }
    if (record_accesses) {
      if (render_lookup_add_typed_access_by_names(lookup, section_index, offset, (uint8_t)operand_index,
          base_reg, (int16_t)displacement, struct_size, array_element_addend, base_cursor,
          (uint16_t)(field_displacement - field.offset), &field, provenance, table_origin) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static void typed_io_request_setup_value_set(M68kRenderIoRequestSetupValue *target,
    uint32_t value, uint32_t source_offset) {
  if (target == NULL) return;
  target->known = 1U;
  target->value = value;
  target->source_offset = source_offset;
}

static void typed_state_record_io_request_immediate_store(M68kRenderTypedState *state,
    const M68kInstructionIR *instruction, uint32_t offset) {
  const M68kSimFormMetadata *metadata;
  size_t source_index = 0U, dest_index = 0U;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint32_t value = 0U;
  AmigaOsResolvedStructFieldInfo field;
  M68kRenderIoRequestSetup *setup;
  if (state == NULL || instruction == NULL) return;
  if (!instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index, &metadata))
    return;
  (void)metadata;
  if (!m68k_ir_operand_immediate_value(&instruction->operands[source_index], &value) ||
      !operand_is_address_displacement_local(&instruction->operands[dest_index], &base_reg, &displacement) ||
      base_reg >= 8U || state->addr_regs[base_reg].known == 0U ||
      state->addr_regs[base_reg].struct_id == AMIGA_OS_STRUCT_ID_NONE ||
      !amiga_os_resolve_struct_field_by_struct_id(state->addr_regs[base_reg].struct_id, displacement, 0, &field)) {
    return;
  }
  setup = &state->io_request_setups[base_reg];
  if (field.field_id == AMIGA_OS_FIELD_ID_IO_COMMAND) {
    typed_io_request_setup_value_set(&setup->command, value, offset);
  } else if (field.field_id == AMIGA_OS_FIELD_ID_IO_OFFSET) {
    typed_io_request_setup_value_set(&setup->disk_offset, value, offset);
  } else if (field.field_id == AMIGA_OS_FIELD_ID_IO_LENGTH) {
    typed_io_request_setup_value_set(&setup->byte_length, value, offset);
  } else if (field.field_id == AMIGA_OS_FIELD_ID_IO_DATA) {
    typed_io_request_setup_value_set(&setup->destination, value, offset);
  }
}

static int policy_seed_context_matches(const M68kAnalysisPolicy *policy, size_t section_index,
    uint32_t offset, uint8_t reg_kind, uint8_t reg_index, const char *context_name) {
  uint16_t index;
  if (policy == NULL || context_name == NULL) return 0;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if (seed->kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR ||
        seed->reg_kind != reg_kind || seed->reg_index != reg_index ||
        strcmp(seed->context_name, context_name) != 0) {
      continue;
    }
    if (seed->has_section_index && seed->section_index != (uint32_t)section_index) continue;
    if (seed->has_entry_offset) {
      if (seed->entry_offset != offset) continue;
    } else if (!policy->has_entry_offset || section_index != 0U || policy->entry_offset != offset) continue;
    return 1;
  }
  return 0;
}

static int render_lookup_add_bootblock_disk_read(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint32_t command_value, uint32_t disk_offset, uint32_t byte_length,
    uint32_t destination_addr) {
  M68kRenderBootblockDiskRead *grown;
  size_t index;
  size_t next_capacity;
  if (lookup == NULL || byte_length == 0U) return 0;
  for (index = 0U; index < lookup->bootblock_disk_read_count; ++index) {
    const M68kRenderBootblockDiskRead *read = &lookup->bootblock_disk_reads[index];
    if (read->section_index == section_index && read->offset == offset &&
        read->command_value == command_value && read->disk_offset == disk_offset &&
        read->byte_length == byte_length && read->destination_addr == destination_addr) {
      return 0;
    }
  }
  if (lookup->bootblock_disk_read_count == lookup->bootblock_disk_read_capacity) {
    next_capacity = lookup->bootblock_disk_read_capacity == 0U ? 4U : lookup->bootblock_disk_read_capacity * 2U;
    grown = (M68kRenderBootblockDiskRead *)render_lookup_grow_array(lookup, lookup->bootblock_disk_reads,
      lookup->bootblock_disk_read_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->bootblock_disk_reads = grown;
    lookup->bootblock_disk_read_capacity = next_capacity;
  }
  memset(&lookup->bootblock_disk_reads[lookup->bootblock_disk_read_count], 0,
    sizeof(lookup->bootblock_disk_reads[lookup->bootblock_disk_read_count]));
  lookup->bootblock_disk_reads[lookup->bootblock_disk_read_count].section_index = section_index;
  lookup->bootblock_disk_reads[lookup->bootblock_disk_read_count].offset = offset;
  lookup->bootblock_disk_reads[lookup->bootblock_disk_read_count].command_value = command_value;
  lookup->bootblock_disk_reads[lookup->bootblock_disk_read_count].disk_offset = disk_offset;
  lookup->bootblock_disk_reads[lookup->bootblock_disk_read_count].byte_length = byte_length;
  lookup->bootblock_disk_reads[lookup->bootblock_disk_read_count].destination_addr = destination_addr;
  snprintf(lookup->bootblock_disk_reads[lookup->bootblock_disk_read_count].command_name,
    sizeof(lookup->bootblock_disk_reads[lookup->bootblock_disk_read_count].command_name), "CMD_READ");
  lookup->bootblock_disk_reads[lookup->bootblock_disk_read_count].source_kind =
    M68K_RECOVERED_PLATFORM_TRANSFER_SOURCE_LOGICAL_DISK_OFFSET;
  ++lookup->bootblock_disk_read_count;
  return 0;
}

static int render_lookup_record_bootblock_disk_read_call(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, const M68kRenderTypedState *state, const AmigaOsLibraryVectorInfo *vector) {
  int32_t cmd_read_value = 0;
  const M68kRenderIoRequestSetup *setup;
  const M68kRenderTypedRegValue *ioreq;
  if (lookup == NULL || state == NULL || vector == NULL || vector->lvo_symbol_id != AMIGA_OS_SYMBOL_ID_LVODOIO)
    return 0;
  if (!render_amiga_constant_value_by_symbol_id(AMIGA_OS_SYMBOL_ID_CMD_READ, &cmd_read_value))
    return 0;
  ioreq = &state->addr_regs[1U];
  if (ioreq->known == 0U || ioreq->struct_id != AMIGA_OS_STRUCT_ID_IO ||
      ioreq->provenance.kind != M68K_PLATFORM_TYPE_PROVENANCE_POLICY_SEED ||
      !policy_seed_context_matches(lookup->policy, ioreq->provenance.section_index, ioreq->provenance.offset,
        M68K_ANALYSIS_REGISTER_ADDRESS, 1U, "trackdisk.device")) {
    return 0;
  }
  setup = &state->io_request_setups[1U];
  if (setup->command.known == 0U || setup->disk_offset.known == 0U ||
      setup->byte_length.known == 0U || setup->destination.known == 0U ||
      setup->command.value != (uint32_t)cmd_read_value) {
    return 0;
  }
  return render_lookup_add_bootblock_disk_read(lookup, section_index, offset, setup->command.value,
    setup->disk_offset.value, setup->byte_length.value, setup->destination.value);
}

static int render_lookup_add_bootblock_runtime_copy(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint32_t source_addr, uint32_t destination_addr, uint32_t byte_length,
    uint32_t handoff_addr) {
  M68kRenderBootblockRuntimeCopy *grown;
  size_t index;
  size_t next_capacity;
  if (lookup == NULL || byte_length == 0U) return 0;
  for (index = 0U; index < lookup->bootblock_runtime_copy_count; ++index) {
    const M68kRenderBootblockRuntimeCopy *copy = &lookup->bootblock_runtime_copies[index];
    if (copy->section_index == section_index && copy->offset == offset &&
        copy->source_addr == source_addr && copy->destination_addr == destination_addr &&
        copy->byte_length == byte_length && copy->handoff_addr == handoff_addr) {
      return 0;
    }
  }
  if (lookup->bootblock_runtime_copy_count == lookup->bootblock_runtime_copy_capacity) {
    next_capacity = lookup->bootblock_runtime_copy_capacity == 0U ? 4U : lookup->bootblock_runtime_copy_capacity * 2U;
    grown = (M68kRenderBootblockRuntimeCopy *)render_lookup_grow_array(lookup, lookup->bootblock_runtime_copies,
      lookup->bootblock_runtime_copy_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->bootblock_runtime_copies = grown;
    lookup->bootblock_runtime_copy_capacity = next_capacity;
  }
  memset(&lookup->bootblock_runtime_copies[lookup->bootblock_runtime_copy_count], 0,
    sizeof(lookup->bootblock_runtime_copies[lookup->bootblock_runtime_copy_count]));
  lookup->bootblock_runtime_copies[lookup->bootblock_runtime_copy_count].section_index = section_index;
  lookup->bootblock_runtime_copies[lookup->bootblock_runtime_copy_count].offset = offset;
  lookup->bootblock_runtime_copies[lookup->bootblock_runtime_copy_count].source_addr = source_addr;
  lookup->bootblock_runtime_copies[lookup->bootblock_runtime_copy_count].destination_addr = destination_addr;
  lookup->bootblock_runtime_copies[lookup->bootblock_runtime_copy_count].byte_length = byte_length;
  lookup->bootblock_runtime_copies[lookup->bootblock_runtime_copy_count].handoff_addr = handoff_addr;
  lookup->bootblock_runtime_copies[lookup->bootblock_runtime_copy_count].source_kind =
    M68K_RECOVERED_PLATFORM_TRANSFER_SOURCE_POST_READ_RUNTIME_COPY;
  ++lookup->bootblock_runtime_copy_count;
  return 0;
}

static void typed_flow_apply_call_input_alias_type(const M68kAnalysisFunctionSummary *summary,
    size_t section_index, uint32_t offset, M68kRenderTypedState *state,
    const M68kAnalysisFunctionSummaryInput *input, uint16_t input_struct_id, int *io_changed) {
  if (!summary || !state || !input || input_struct_id == AMIGA_OS_STRUCT_ID_NONE ||
      input->location.kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER ||
      input->location.register_count != 1U ||
      input->location.registers[0].register_kind != AMIGA_OS_REGISTER_ADDRESS ||
      input->location.registers[0].register_index >= 8U) return;
  uint8_t argument = input->location.registers[0].register_index;
  for (uint8_t reg = 0U; reg < 8U; ++reg) {
    if (reg == argument || !typed_state_addr_alias_equal(state, reg, argument) ||
        function_summary_register_effect(summary, M68K_ANALYSIS_REGISTER_ADDRESS, reg) !=
          M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED) continue;
    M68kRenderTypedProvenance provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_API_INPUT,
      section_index, offset);
    M68kRenderTypedRegValue *value = &state->addr_regs[reg];
    if (!value->known) {
      /* This is a precondition interpretation, never a CPU write. */
      typed_reg_forget_interpretation(value);
      value->known = 1U; value->struct_id = input_struct_id; value->provenance = provenance;
      if (io_changed) *io_changed = 1;
    } else if (value->struct_id != input_struct_id) {
      int conflict = 0;
      uint16_t merged = typed_struct_id_refined_merge(value->struct_id, input_struct_id, &conflict);
      if (!conflict && merged != AMIGA_OS_STRUCT_ID_NONE && merged != value->struct_id) {
        value->struct_id = merged; value->output = NULL; value->provenance = provenance;
        if (io_changed) *io_changed = 1;
      }
    }
  }
}

static int render_lookup_record_typed_call_consumer(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint8_t kind, uint8_t reg_kind, uint8_t reg_index, const char *pointee_struct_name,
    const char *contract_name, const char *function_summary_id, uint32_t contract_section_index, uint32_t contract_offset,
    const M68kAnalysisFunctionSummaryInput *platform_input, const M68kRenderTypedState *state,
    const M68kRenderTypedStoredValue *direct_value);
static int typed_flow_callback_table_identity(const M68kRenderTypedState *state,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, const M68kRenderTypedStoredValue *direct_value,
    size_t *out_table_section_index, uint32_t *out_table_offset);
static M68kRenderTypedStoredValue typed_stored_value_for_address_register(
    const M68kRenderTypedState *state, uint8_t reg_index);

static int typed_flow_apply_call_input_type_refs(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, M68kRenderTypedState *state, const M68kAnalysisFunctionSummary *summary,
    int allow_lookup_storage, int *io_changed) {
  uint8_t index;
  if (lookup == NULL || state == NULL || summary == NULL) return 0;
  for (index = 0U; index < summary->input_count; ++index) {
    const M68kAnalysisFunctionSummaryInput *input = &summary->inputs[index];
    uint16_t input_struct_id;
    int added = 0;
    uint8_t reg_index;
    if (input->seed_kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR ||
        input->location.kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER ||
        input->location.register_count != 1U ||
        input->location.registers[0].register_kind != AMIGA_OS_REGISTER_ADDRESS ||
        input->location.registers[0].register_index >= 8U) {
      continue;
    }
    reg_index = input->location.registers[0].register_index;
    input_struct_id = lookup_policy_struct_id_by_name(lookup->policy, input->struct_name);
    if (input_struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
    if (render_lookup_record_typed_call_consumer(lookup, section_index, offset,
          M68K_ADDRESS_VALUE_CONSUMER_PLATFORM_API_INPUT, AMIGA_OS_REGISTER_ADDRESS, reg_index,
          input->struct_name, NULL, NULL, UINT32_MAX, 0U, input, state, NULL) != 0) {
      return -1;
    }
    if (allow_lookup_storage && state->app_addr_regs[reg_index].known) {
      if (render_lookup_add_typed_app_slot_region(lookup, state->app_addr_regs[reg_index].displacement,
          input_struct_id, section_index, offset, &added) != 0) {
        return -1;
      }
      if (added && io_changed != NULL) *io_changed = 1;
    }
    if (state->addr_regs[reg_index].known && state->addr_regs[reg_index].struct_id != input_struct_id &&
        amiga_struct_prefix_chain_contains(input_struct_id, state->addr_regs[reg_index].struct_id)) {
      int refined = 0;
      uint16_t root_struct_id = state->addr_regs[reg_index].struct_id;
      M68kRenderTypedRegValue input_value = state->addr_regs[reg_index];
      if (typed_state_refine_address_reg_from_prefix(lookup, state, reg_index,
          root_struct_id, input_struct_id, section_index, offset, &refined) != 0) {
        return -1;
      }
      if (typed_state_promote_matching_stored_values(state, &input_value, root_struct_id, input_struct_id,
          section_index, offset)) {
        refined = 1;
      }
      if (refined && io_changed != NULL) *io_changed = 1;
    }
    typed_flow_apply_call_input_alias_type(summary, section_index, offset, state, input, input_struct_id,
      io_changed);
  }
  return 0;
}

static int typed_flow_record_local_call_input_consumers(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, size_t target_section_index, uint32_t target_offset, const M68kRenderTypedState *state) {
  uint16_t index;
  if (lookup == NULL || lookup->policy == NULL || state == NULL) return 0;
  for (index = 0U; index < lookup->policy->function_summary_count &&
       index < M68K_ANALYSIS_FUNCTION_SUMMARY_LIMIT; ++index) {
    const M68kAnalysisFunctionSummary *summary = &lookup->policy->function_summaries[index];
    uint8_t input_index;
    if (!summary->has_section_index || summary->callable_kind != M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT ||
        summary->section_index != (uint32_t)target_section_index || summary->entry_offset != target_offset) continue;
    {
      M68kFunctionSummaryUseIR use;
      memset(&use, 0, sizeof(use));
      snprintf(use.function_summary_id, sizeof(use.function_summary_id), "%s", summary->function_summary_id);
      use.caller_section_index = (uint32_t)section_index;
      use.caller_offset = offset;
      use.kind = M68K_FUNCTION_SUMMARY_USE_CALL;
      if (render_lookup_add_function_summary_use(lookup, &use) != 0) return -1;
    }
    for (input_index = 0U; input_index < summary->input_count; ++input_index) {
      const M68kAnalysisFunctionSummaryInput *input = &summary->inputs[input_index];
      if (input->seed_kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR ||
          (input->location.kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER &&
           input->location.kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER_TUPLE) ||
          lookup_policy_struct_id_by_name(lookup->policy, input->struct_name) == AMIGA_OS_STRUCT_ID_NONE) continue;
      for (uint8_t member_index = 0U; member_index < input->location.register_count; ++member_index) {
        const M68kFunctionSummaryAbiRegisterMember *member = &input->location.registers[member_index];
        if (member->register_kind != AMIGA_OS_REGISTER_ADDRESS || member->register_index >= 8U) continue;
        if (render_lookup_record_typed_call_consumer(lookup, section_index, offset,
              M68K_ADDRESS_VALUE_CONSUMER_LOCAL_FUNCTION_INPUT, member->register_kind, member->register_index,
              input->struct_name, NULL, summary->function_summary_id,
              (uint32_t)target_section_index, target_offset, NULL, state, NULL) != 0)
          return -1;
      }
    }
  }
  return 0;
}

static int typed_flow_record_callback_input_consumers(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, const M68kRenderTypedState *state,
    const M68kRenderTypedStoredValue *direct_value) {
  const M68kAnalysisPolicy *policy;
  uint16_t summary_index;
  size_t table_section_index;
  uint32_t table_offset;
  M68kRenderTypedStoredValue common_value;
  uint8_t dispatch_reg = 0U;
  int has_dispatch_reg;
  if (lookup == NULL || lookup->object == NULL || instruction == NULL || state == NULL ||
      (policy = lookup->policy) == NULL || !typed_flow_callback_table_identity(state, section, candidate,
        instruction, direct_value, &table_section_index, &table_offset)) {
    return 0;
  }
  /* The first flow pass discovers identities.  Do not write source-analysis
   * uses against a pre-materialization policy projection: the second pass will
   * write one edge to the durable table-owned summary instead. */
  if (lookup->inferred_function_summaries_ready == 0U && direct_value == NULL) return 0;
  typed_stored_value_clear(&common_value);
  if (direct_value != NULL) common_value = *direct_value;
  has_dispatch_reg = operand_is_address_memory_local(&instruction->operands[0], &dispatch_reg, NULL);
  if (direct_value == NULL && has_dispatch_reg)
    common_value = typed_stored_value_for_address_register(state, dispatch_reg);
  if (common_value.table_origin.has_origin == 0U) {
    common_value.table_origin.has_origin = 1U;
    common_value.table_origin.table_section_index = (uint32_t)table_section_index;
    common_value.table_origin.table_start_offset = table_offset;
    common_value.table_origin.consumer_section_index = (uint32_t)section_index;
    common_value.table_origin.consumer_offset = offset;
    common_value.table_origin.entry_index = UINT32_MAX;
    common_value.table_origin.selection_kind = M68K_ADDRESS_VALUE_TABLE_SELECTION_NONE;
  }
  for (summary_index = 0U; summary_index < policy->function_summary_count &&
       summary_index < M68K_ANALYSIS_FUNCTION_SUMMARY_LIMIT; ++summary_index) {
    const M68kAnalysisFunctionSummary *summary = &policy->function_summaries[summary_index];
    const M68kAnalysisFunctionSummary *effect_summary;
    const M68kSection *table_section;
    uint8_t input_index;
    if (!summary->has_section_index || summary->callable_kind != M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_CALLBACK_TABLE ||
        summary->section_index >= lookup->object->section_count || summary->entry_count == 0U ||
        summary->section_index != table_section_index || summary->table_offset != table_offset) continue;
    effect_summary = lookup_inferred_callback_table_function_summary(lookup, table_section_index, table_offset);
    if (effect_summary == NULL) effect_summary = summary;
    table_section = &lookup->object->sections[summary->section_index];
    if (table_section->data == NULL || summary->table_offset > table_section->size ||
        summary->entry_count > (table_section->size - summary->table_offset) / 4U) continue;
    {
      M68kFunctionSummaryUseIR use;
      memset(&use, 0, sizeof(use));
      snprintf(use.function_summary_id, sizeof(use.function_summary_id), "%s", effect_summary->function_summary_id);
      use.caller_section_index = (uint32_t)section_index;
      use.caller_offset = offset;
      use.kind = M68K_FUNCTION_SUMMARY_USE_CALL;
      if (render_lookup_add_function_summary_use(lookup, &use) != 0) return -1;
    }
    for (input_index = 0U; input_index < summary->input_count; ++input_index) {
      const M68kAnalysisFunctionSummaryInput *input = &summary->inputs[input_index];
      if (input->seed_kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR ||
          input->location.kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER ||
          input->location.register_count != 1U ||
          input->location.registers[0].register_kind != AMIGA_OS_REGISTER_ADDRESS ||
          input->location.registers[0].register_index >= 8U ||
          lookup_policy_struct_id_by_name(policy, input->struct_name) == AMIGA_OS_STRUCT_ID_NONE) continue;
      if (render_lookup_record_typed_call_consumer(lookup, section_index, offset,
            M68K_ADDRESS_VALUE_CONSUMER_CALLBACK_INPUT, input->location.registers[0].register_kind,
            input->location.registers[0].register_index,
            input->struct_name, NULL, effect_summary->function_summary_id,
            summary->section_index, summary->table_offset, NULL, state, &common_value) != 0)
        return -1;
    }
  }
  return 0;
}

int instruction_operand_writes_register_from_metadata(const M68kInstructionIR *instruction,
    size_t operand_index) {
  return platform_operand_register_write_mask(instruction, operand_index) != 0U;
}

static int instruction_move_operand_indices_from_metadata(const M68kInstructionIR *instruction,
    size_t *out_source_index, size_t *out_dest_index, const M68kSimFormMetadata **out_metadata) {
  const M68kSimFormMetadata *metadata;
  if (out_source_index != NULL) *out_source_index = 0U;
  if (out_dest_index != NULL) *out_dest_index = 0U;
  if (out_metadata != NULL) *out_metadata = NULL;
  if (instruction == NULL || instruction->operand_count == 0U) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL || metadata->operation_type != M68K_SIM_OP_MOVE ||
      metadata->source_operand_index >= instruction->operand_count ||
      metadata->dest_operand_index >= instruction->operand_count) {
    return 0;
  }
  if (out_source_index != NULL) *out_source_index = metadata->source_operand_index;
  if (out_dest_index != NULL) *out_dest_index = metadata->dest_operand_index;
  if (out_metadata != NULL) *out_metadata = metadata;
  return 1;
}

static int instruction_may_update_stack_pointer_from_metadata(const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (instruction == NULL) return 1;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 1;
  if (metadata->sp_effect_count != 0U) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    if (platform_operand_register_write_mask(instruction, operand_index) & UINT16_C(0x8000)) return 1;
    if (metadata->operand_ea_register_updates[operand_index] != M68K_SIM_EA_UPDATE_NONE &&
        (operand_is_predec_a7_local(&instruction->operands[operand_index]) ||
         operand_is_postinc_a7_local(&instruction->operands[operand_index]))) {
      return 1;
    }
  }
  return 0;
}

static M68kRenderTypedStoredValue typed_stored_value_for_address_register(
    const M68kRenderTypedState *state, uint8_t reg_index) {
  M68kOperandIR operand = {0};
  operand.kind = M68K_ASM_OPERAND_AN;
  operand.value.reg = reg_index;
  return typed_stored_value_for_operand(state, &operand);
}

static void typed_address_consumer_clear_source_targets(M68kRenderTypedAddressConsumer *consumer) {
  consumer->has_target = 0U; consumer->target_section_index = consumer->target_offset = 0U;
  for (size_t i = 0U; i < 4U; ++i) {
    consumer->candidate_target_section_indices[i] = SIZE_MAX;
    consumer->candidate_target_offsets[i] = 0U;
  }
}

void m68k_render_typed_address_consumer_mark_candidate_overflow(
    M68kRenderTypedAddressConsumer *consumer) {
  if (consumer == NULL) return;
  consumer->value.pointer_value_known = 0U;
  consumer->value.pointer_value = 0U;
  consumer->value.pointer_candidate_count = 0U;
  memset(consumer->value.pointer_candidates, 0, sizeof(consumer->value.pointer_candidates));
  consumer->value.raw_long_value_known = 0U;
  consumer->value.raw_long_value = 0U;
  consumer->value.raw_long_candidate_count = 0U;
  memset(consumer->value.raw_long_candidates, 0, sizeof(consumer->value.raw_long_candidates));
  consumer->value.address_value_candidate_overflow = 1U;
  consumer->provenance = consumer->value.provenance;
  consumer->source_value = 0U;
  typed_address_consumer_clear_source_targets(consumer);
  consumer->candidate_target_count = 0U;
  memset(consumer->candidate_source_values, 0, sizeof(consumer->candidate_source_values));
  consumer->resolution = M68K_ADDRESS_VALUE_RESOLUTION_CANDIDATE_OVERFLOW;
}

static int render_lookup_add_typed_address_consumer(M68kRenderLookup *lookup, size_t section_index,
    const M68kAddressValueConsumerIR *fact, const M68kRenderTypedStoredValue *value,
    const M68kPointerStoreIR *storage) {
  M68kRenderTypedAddressConsumer *grown;
  size_t index, next_capacity;
  if (lookup == NULL || fact == NULL || value == NULL) return -1;
  if (lookup->suppress_address_value_observations || lookup->typed_flow_incomplete_count) return 0;
  for (index = 0U; index < lookup->address_value_consumer_count; ++index) {
    M68kRenderTypedAddressConsumer *existing = &lookup->address_value_consumers[index];
    if (existing->section_index != section_index || existing->fact.offset != fact->offset ||
        existing->fact.operand_index != fact->operand_index || existing->fact.kind != fact->kind ||
        existing->fact.register_kind != fact->register_kind || existing->fact.register_index != fact->register_index)
      continue;
    /* The fixed-point state may become more precise or merge distinct static
     * values. Preserve the complete bounded candidate set on the one shared
     * consumer observation; a storage write has no private value copy. */
    if (existing->value.address_value_candidate_overflow != 0U ||
        value->address_value_candidate_overflow != 0U) {
      m68k_render_typed_address_consumer_mark_candidate_overflow(existing);
    } else if (existing->value.pointer_value_known == 0U && value->pointer_value_known != 0U) {
      existing->value = *value;
    } else if (existing->value.pointer_value_known != 0U && value->pointer_value_known != 0U) {
      if (m68k_render_pointer_candidates_merge(&existing->value.pointer_value_known,
        &existing->value.pointer_candidate_count, &existing->value.pointer_value,
        existing->value.pointer_candidates, value->pointer_value_known, value->pointer_candidate_count,
        value->pointer_value, value->pointer_candidates) == M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW) {
        m68k_render_typed_address_consumer_mark_candidate_overflow(existing);
      }
    }
    if (existing->value.table_origin.has_origin == 0U && value->table_origin.has_origin != 0U)
      existing->value.table_origin = value->table_origin;
    else if (existing->value.table_origin.has_origin != 0U && value->table_origin.has_origin != 0U &&
        !typed_table_origins_equal(&existing->value.table_origin, &value->table_origin))
      typed_table_origin_clear(&existing->value.table_origin);
    existing->provenance = existing->value.provenance;
    existing->source_value = existing->value.pointer_value;
    existing->candidate_target_count = existing->value.pointer_candidate_count;
    typed_address_consumer_clear_source_targets(existing);
    memcpy(existing->candidate_source_values, existing->value.pointer_candidates,
      sizeof(existing->candidate_source_values));
    existing->resolution = existing->value.address_value_candidate_overflow != 0U
      ? M68K_ADDRESS_VALUE_RESOLUTION_CANDIDATE_OVERFLOW
      : existing->value.pointer_value_known != 0U &&
        existing->value.pointer_candidate_count > 1U
      ? M68K_ADDRESS_VALUE_RESOLUTION_AMBIGUOUS_TARGET
      : M68K_ADDRESS_VALUE_RESOLUTION_UNKNOWN_TARGET;
    if (storage != NULL) {
      existing->storage = *storage;
      existing->has_storage = 1U;
    }
    return 0;
  }
  if (lookup->address_value_consumer_count == lookup->address_value_consumer_capacity) {
    next_capacity = lookup->address_value_consumer_capacity == 0U ? 16U :
      lookup->address_value_consumer_capacity * 2U;
    grown = (M68kRenderTypedAddressConsumer *)render_lookup_grow_array(lookup,
      lookup->address_value_consumers, lookup->address_value_consumer_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->address_value_consumers = grown;
    lookup->address_value_consumer_capacity = next_capacity;
  }
  memset(&lookup->address_value_consumers[lookup->address_value_consumer_count], 0,
    sizeof(lookup->address_value_consumers[lookup->address_value_consumer_count]));
  typed_address_consumer_clear_source_targets(&lookup->address_value_consumers[lookup->address_value_consumer_count]);
  lookup->address_value_consumers[lookup->address_value_consumer_count].section_index = section_index;
  lookup->address_value_consumers[lookup->address_value_consumer_count].fact = *fact;
  if (storage != NULL) {
    lookup->address_value_consumers[lookup->address_value_consumer_count].storage = *storage;
    lookup->address_value_consumers[lookup->address_value_consumer_count].has_storage = 1U;
  }
  lookup->address_value_consumers[lookup->address_value_consumer_count].value = *value;
  lookup->address_value_consumers[lookup->address_value_consumer_count].provenance = value->provenance;
  lookup->address_value_consumers[lookup->address_value_consumer_count].source_value = value->pointer_value;
  lookup->address_value_consumers[lookup->address_value_consumer_count].resolution =
    value->address_value_candidate_overflow != 0U ? M68K_ADDRESS_VALUE_RESOLUTION_CANDIDATE_OVERFLOW :
    value->pointer_value_known != 0U && value->pointer_candidate_count > 1U ?
      M68K_ADDRESS_VALUE_RESOLUTION_AMBIGUOUS_TARGET : M68K_ADDRESS_VALUE_RESOLUTION_UNKNOWN_TARGET;
  lookup->address_value_consumers[lookup->address_value_consumer_count].candidate_target_count =
    value->pointer_candidate_count;
  memcpy(lookup->address_value_consumers[lookup->address_value_consumer_count].candidate_source_values,
    value->pointer_candidates, sizeof(value->pointer_candidates));
  if (value->address_value_candidate_overflow != 0U) {
    m68k_render_typed_address_consumer_mark_candidate_overflow(
      &lookup->address_value_consumers[lookup->address_value_consumer_count]);
  }
  ++lookup->address_value_consumer_count;
  return 0;
}

int render_lookup_add_function_summary_use(M68kRenderLookup *lookup, const M68kFunctionSummaryUseIR *use) {
  M68kFunctionSummaryUseIR *grown;
  size_t index, next_capacity;
  if (lookup != NULL && lookup->affine_entry_context != NULL) return 0;
  if (lookup == NULL || use == NULL || use->function_summary_id[0] == '\0' ||
      (use->kind != M68K_FUNCTION_SUMMARY_USE_CALL && use->kind != M68K_FUNCTION_SUMMARY_USE_INPUT)) return -1;
  for (index = 0U; index < lookup->function_summary_use_count; ++index) {
    M68kFunctionSummaryUseIR *existing = &lookup->function_summary_uses[index];
    if (existing->caller_section_index == use->caller_section_index &&
        existing->caller_offset == use->caller_offset && existing->kind == use->kind &&
        existing->consumer_kind == use->consumer_kind && existing->operand_index == use->operand_index &&
        existing->register_kind == use->register_kind && existing->register_index == use->register_index &&
        strcmp(existing->function_summary_id, use->function_summary_id) == 0) {
      if (existing->terminal_reason == M68K_FUNCTION_SUMMARY_TERMINAL_NONE &&
          use->terminal_reason != M68K_FUNCTION_SUMMARY_TERMINAL_NONE)
        existing->terminal_reason = use->terminal_reason;
      return 0;
    }
  }
  if (lookup->function_summary_use_count == lookup->function_summary_use_capacity) {
    next_capacity = lookup->function_summary_use_capacity == 0U ? 16U :
      lookup->function_summary_use_capacity * 2U;
    grown = (M68kFunctionSummaryUseIR *)render_lookup_grow_array(lookup, lookup->function_summary_uses,
      lookup->function_summary_use_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->function_summary_uses = grown;
    lookup->function_summary_use_capacity = next_capacity;
  }
  lookup->function_summary_uses[lookup->function_summary_use_count++] = *use;
  return 0;
}

static int render_lookup_add_platform_call_thunk(M68kRenderLookup *lookup,
    const M68kPlatformCallThunkIR *thunk) {
  M68kPlatformCallThunkIR *grown;
  size_t index, next_capacity;
  if (lookup != NULL && lookup->affine_entry_context != NULL) return 0;
  if (lookup == NULL || thunk == NULL ||
      thunk->relation_kind != M68K_PLATFORM_CALL_THUNK_RELATION_PLATFORM_CALL_THUNK) return -1;
  for (index = 0U; index < lookup->platform_call_thunk_count; ++index) {
    const M68kPlatformCallThunkIR *existing = &lookup->platform_call_thunks[index];
    if (existing->wrapper_section_index == thunk->wrapper_section_index &&
        existing->wrapper_entry_offset == thunk->wrapper_entry_offset &&
        existing->platform_library_id == thunk->platform_library_id &&
        existing->platform_function_id == thunk->platform_function_id &&
        existing->wrapper_call_offset == thunk->wrapper_call_offset) return 0;
  }
  if (lookup->platform_call_thunk_count == lookup->platform_call_thunk_capacity) {
    next_capacity = lookup->platform_call_thunk_capacity == 0U ? 16U :
      lookup->platform_call_thunk_capacity * 2U;
    grown = (M68kPlatformCallThunkIR *)render_lookup_grow_array(lookup, lookup->platform_call_thunks,
      lookup->platform_call_thunk_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->platform_call_thunks = grown;
    lookup->platform_call_thunk_capacity = next_capacity;
  }
  lookup->platform_call_thunks[lookup->platform_call_thunk_count++] = *thunk;
  return 0;
}

static int render_lookup_record_typed_call_consumer(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint8_t kind, uint8_t reg_kind, uint8_t reg_index, const char *pointee_struct_name,
    const char *contract_name, const char *function_summary_id, uint32_t contract_section_index, uint32_t contract_offset,
    const M68kAnalysisFunctionSummaryInput *platform_input, const M68kRenderTypedState *state,
    const M68kRenderTypedStoredValue *direct_value) {
  M68kAddressValueConsumerIR fact;
  M68kRenderTypedStoredValue value;
  if (lookup == NULL || (state == NULL && direct_value == NULL) || pointee_struct_name == NULL || pointee_struct_name[0] == '\0' ||
      reg_kind != AMIGA_OS_REGISTER_ADDRESS || reg_index >= 8U) return 0;
  value = direct_value != NULL ? *direct_value : typed_stored_value_for_address_register(state, reg_index);
  if (value.raw_long_value_known == 0U && value.pointer_value_known == 0U &&
      value.address_value_candidate_overflow == 0U && value.table_origin.has_origin == 0U) return 0;
  typed_stored_value_activate_address(&value);
  memset(&fact, 0, sizeof(fact));
  fact.offset = offset;
  fact.operand_index = reg_index;
  fact.kind = kind;
  fact.register_kind = reg_kind;
  fact.register_index = reg_index;
  fact.contract_section_index = contract_section_index;
  fact.contract_offset = contract_offset;
  snprintf(fact.pointee_struct_name, sizeof(fact.pointee_struct_name), "%s", pointee_struct_name);
  snprintf(fact.contract_name, sizeof(fact.contract_name), "%s", contract_name != NULL ? contract_name : "");
  if (platform_input != NULL && platform_input->has_platform_identity != 0U) {
    fact.has_platform_input_identity = 1U;
    fact.platform_library_id = platform_input->platform_library_id;
    fact.platform_function_id = platform_input->platform_function_id;
    fact.platform_input_id = platform_input->platform_input_id;
  }
  snprintf(fact.function_summary_id, sizeof(fact.function_summary_id), "%s",
    function_summary_id != NULL ? function_summary_id : "");
  if (fact.function_summary_id[0] != '\0') {
    M68kFunctionSummaryUseIR use;
    memset(&use, 0, sizeof(use));
    snprintf(use.function_summary_id, sizeof(use.function_summary_id), "%s", fact.function_summary_id);
    use.caller_section_index = (uint32_t)section_index;
    use.caller_offset = offset;
    use.kind = M68K_FUNCTION_SUMMARY_USE_INPUT;
    use.consumer_kind = kind;
    use.operand_index = reg_index;
    use.register_kind = reg_kind;
    use.register_index = reg_index;
    if (render_lookup_add_function_summary_use(lookup, &use) != 0) return -1;
  }
  return render_lookup_add_typed_address_consumer(lookup, section_index, &fact, &value, NULL);
}

/* A typed pointer-table load is itself a durable value consumer.  Recording
 * it here keeps the table expression attached to the instruction even when
 * the loaded pointer is only dereferenced later.  Source analysis fills the
 * candidate values and targets from canonical table entries after rendering;
 * this path deliberately contributes identity and contract context only. */
static int render_lookup_record_typed_table_load(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, size_t source_operand_index, uint8_t destination_register,
    const char *pointee_struct_name, const M68kRenderTypedStoredValue *value) {
  M68kAddressValueConsumerIR fact;
  if (lookup == NULL || value == NULL || value->table_origin.has_origin == 0U) return 0;
  memset(&fact, 0, sizeof(fact));
  fact.offset = offset;
  fact.operand_index = (uint8_t)source_operand_index;
  fact.kind = M68K_ADDRESS_VALUE_CONSUMER_STORAGE;
  fact.register_kind = AMIGA_OS_REGISTER_ADDRESS;
  fact.register_index = destination_register;
  snprintf(fact.pointee_struct_name, sizeof(fact.pointee_struct_name), "%s",
    pointee_struct_name != NULL ? pointee_struct_name : "");
  snprintf(fact.contract_name, sizeof(fact.contract_name), "table_load");
  return render_lookup_add_typed_address_consumer(lookup, section_index, &fact, value, NULL);
}

static int typed_memory_destination_requires_address_value(const M68kRenderLookup *lookup,
    const M68kRenderTypedState *state, const M68kRenderPlatformState *platform_state,
    const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint16_t index;
  uint32_t absolute_address = 0U;
  if (lookup == NULL || state == NULL || operand == NULL) return 0;
  if (operand_is_address_memory_local(operand, &base_reg, &displacement) && base_reg < 8U &&
      state->addr_regs[base_reg].known && state->addr_regs[base_reg].struct_id != AMIGA_OS_STRUCT_ID_NONE &&
      lookup_policy_pointer_value_field(lookup->policy, state->addr_regs[base_reg].struct_id,
        state->addr_regs[base_reg].byte_cursor + displacement, NULL) != NULL) {
    return 1;
  }
  if (operand_absolute_offset_local(operand, &absolute_address) && lookup->policy != NULL) {
    for (index = 0U; index < lookup->policy->absolute_storage_slot_count &&
         index < M68K_ANALYSIS_ABSOLUTE_STORAGE_SLOT_LIMIT; ++index) {
      const M68kAnalysisAbsoluteStorageSlot *slot = &lookup->policy->absolute_storage_slots[index];
      if (slot->address != absolute_address) continue;
      if (slot->storage_kind_id == M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER ||
          slot->storage_kind_id == M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_POINTER ||
          slot->storage_kind_id == M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER_TABLE) {
        return 1;
      }
    }
  }
  if (!operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U ||
      platform_state == NULL || !render_state_operand_uses_app_base(platform_state, base_reg, displacement) ||
      lookup->policy == NULL) {
    return 0;
  }
  for (index = 0U; index < lookup->policy->rsset_layout_region_count &&
       index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++index) {
    const M68kAnalysisRssetLayoutRegion *region = &lookup->policy->rsset_layout_regions[index];
    if (region->offset != (uint32_t)displacement) continue;
    if (region->storage_kind_id == M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER ||
        region->storage_kind_id == M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_POINTER ||
        region->storage_kind_id == M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER_TABLE) {
      return 1;
    }
  }
  return 0;
}

/* Construct the complete destination-bearing fact in one place.  Additional
 * typed storage classes use the same public representation once their
 * renderer/source-quality obligations are installed. */
static int render_lookup_record_typed_address_store(M68kRenderLookup *lookup,
    const M68kRenderTypedState *state, const M68kRenderPlatformState *platform_state, size_t section_index,
    const M68kInstructionIR *instruction, size_t source_index, size_t dest_index, uint32_t offset,
    const M68kRenderTypedStoredValue *value) {
  const M68kOperandIR *source_operand;
  const M68kOperandIR *dest_operand;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint32_t absolute_address = 0U;
  uint16_t policy_index;
  M68kPointerStoreIR fact;
  M68kAddressValueConsumerIR consumer;
  if (lookup != NULL && lookup->affine_entry_context != NULL) return 0;
  if (lookup == NULL || state == NULL || instruction == NULL || value == NULL ||
      source_index >= instruction->operand_count || dest_index >= instruction->operand_count ||
      instruction->size_suffix != 'l') {
    return 0;
  }
  source_operand = &instruction->operands[source_index];
  dest_operand = &instruction->operands[dest_index];
  memset(&fact, 0, sizeof(fact));
  memset(&consumer, 0, sizeof(consumer));
  fact.offset = offset;
  fact.source_operand_index = (uint8_t)source_index;
  fact.destination_operand_index = (uint8_t)dest_index;
  consumer.offset = offset;
  consumer.kind = M68K_ADDRESS_VALUE_CONSUMER_STORAGE;
  consumer.operand_index = (uint8_t)source_index;
  if (operand_is_address_memory_local(dest_operand, &base_reg, &displacement) && base_reg < 8U &&
      state->addr_regs[base_reg].known && state->addr_regs[base_reg].struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    const M68kAnalysisCustomStruct *destination_struct = NULL;
    const M68kAnalysisCustomStructField *destination_field = lookup_policy_pointer_value_field(lookup->policy,
      state->addr_regs[base_reg].struct_id, state->addr_regs[base_reg].byte_cursor + displacement,
      &destination_struct);
    if (destination_field != NULL && destination_struct != NULL) {
      fact.destination_kind = M68K_POINTER_STORE_DESTINATION_STRUCT_FIELD;
      fact.destination_field_offset = (uint16_t)destination_field->offset;
      fact.destination_value_kind = destination_field->value_kind;
      snprintf(fact.destination_struct_name, sizeof(fact.destination_struct_name), "%s", destination_struct->name);
      snprintf(fact.destination_field_name, sizeof(fact.destination_field_name), "%s", destination_field->name);
      snprintf(fact.destination_symbol, sizeof(fact.destination_symbol), "%s", destination_field->name);
      snprintf(fact.pointee_struct_name, sizeof(fact.pointee_struct_name), "%s", destination_field->pointer_struct);
      snprintf(consumer.pointee_struct_name, sizeof(consumer.pointee_struct_name), "%s", fact.pointee_struct_name);
      snprintf(consumer.contract_name, sizeof(consumer.contract_name), "%s", fact.destination_symbol);
      return render_lookup_add_typed_address_consumer(lookup, section_index, &consumer, value, &fact);
    }
  }
  if (operand_absolute_offset_local(dest_operand, &absolute_address) && lookup->policy != NULL) {
    for (policy_index = 0U; policy_index < lookup->policy->absolute_storage_slot_count &&
         policy_index < M68K_ANALYSIS_ABSOLUTE_STORAGE_SLOT_LIMIT; ++policy_index) {
      const M68kAnalysisAbsoluteStorageSlot *slot = &lookup->policy->absolute_storage_slots[policy_index];
      if (slot->address != absolute_address ||
          (slot->storage_kind_id != M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER &&
           slot->storage_kind_id != M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_POINTER &&
           slot->storage_kind_id != M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER_TABLE)) continue;
      fact.destination_kind = M68K_POINTER_STORE_DESTINATION_ABSOLUTE_SLOT;
      fact.destination_value_kind = slot->storage_kind_id;
      snprintf(fact.destination_symbol, sizeof(fact.destination_symbol), "%s", slot->symbol);
      snprintf(fact.pointee_struct_name, sizeof(fact.pointee_struct_name), "%s", slot->pointer_struct);
      snprintf(consumer.pointee_struct_name, sizeof(consumer.pointee_struct_name), "%s", fact.pointee_struct_name);
      snprintf(consumer.contract_name, sizeof(consumer.contract_name), "%s", fact.destination_symbol);
      return render_lookup_add_typed_address_consumer(lookup, section_index, &consumer, value, &fact);
    }
  }
  if (operand_is_address_memory_local(dest_operand, &base_reg, &displacement) && base_reg < 8U &&
      platform_state != NULL && render_state_operand_uses_app_base(platform_state, base_reg, displacement) &&
      lookup->policy != NULL) {
    for (policy_index = 0U; policy_index < lookup->policy->rsset_layout_region_count &&
         policy_index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++policy_index) {
      const M68kAnalysisRssetLayoutRegion *region = &lookup->policy->rsset_layout_regions[policy_index];
      if (region->offset != (uint32_t)displacement ||
          (region->storage_kind_id != M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER &&
           region->storage_kind_id != M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_POINTER &&
           region->storage_kind_id != M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_POINTER_TABLE)) continue;
      fact.destination_kind = M68K_POINTER_STORE_DESTINATION_APP_SLOT;
      fact.destination_value_kind = region->storage_kind_id;
      snprintf(fact.destination_symbol, sizeof(fact.destination_symbol), "%s", region->symbol);
      snprintf(fact.pointee_struct_name, sizeof(fact.pointee_struct_name), "%s", region->pointer_struct);
      snprintf(consumer.pointee_struct_name, sizeof(consumer.pointee_struct_name), "%s", fact.pointee_struct_name);
      snprintf(consumer.contract_name, sizeof(consumer.contract_name), "%s", fact.destination_symbol);
      return render_lookup_add_typed_address_consumer(lookup, section_index, &consumer, value, &fact);
    }
  }
  return 0;
}

static int render_lookup_record_typed_storage_store(M68kRenderLookup *lookup, M68kRenderTypedState *state,
    const M68kRenderPlatformState *platform_state, size_t section_index, const M68kInstructionIR *instruction,
    const M68kDecodeCandidate *candidate, uint32_t offset, int allow_lookup_storage, int *io_changed) {
  const M68kSimFormMetadata *metadata = NULL;
  size_t source_index = 0U, dest_index = 0U;
  uint8_t base_reg = 0U;
  int16_t base_displacement = 0, stack_displacement = 0;
  int destination_requires_address = 0;
  if (lookup == NULL || state == NULL || instruction == NULL) return 0;
  if (!instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index, &metadata))
    return 0;
  if (metadata == NULL || platform_operand_memory_access(instruction, dest_index) != M68K_SIM_ACCESS_MEMORY_WRITE)
    return 0;
    const M68kOperandIR *source_operand = &instruction->operands[source_index];
    const M68kOperandIR *dest_operand = &instruction->operands[dest_index];
    M68kRenderTypedStoredValue value = typed_stored_value_for_operand(state, source_operand);
  {
    uint32_t immediate_value = 0U;
    if (instruction->size_suffix == 'l' && m68k_ir_operand_immediate_value(source_operand, &immediate_value)) {
      typed_stored_value_set_raw_long(&value, immediate_value);
      value.provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_IMMEDIATE,
        section_index, offset);
      value.provenance.producer_operand_index = (uint8_t)source_index;
    }
    destination_requires_address = typed_memory_destination_requires_address_value(lookup, state, platform_state,
      dest_operand);
    if (destination_requires_address && instruction->size_suffix == 'l') {
      typed_stored_value_activate_address(&value);
      if (instruction->size_suffix == 'l' && m68k_ir_operand_immediate_value(source_operand, &immediate_value)) {
        if (candidate != NULL) {
          const M68kFact *relocation = analysis_operand_relocation_ref(lookup, section_index, candidate, source_index);
          uint32_t target_runtime_address = 0U;
          if (relocation != NULL && relocation->target_section_index < lookup->section_count &&
              lookup_source_runtime_address(lookup, relocation->target_section_index, relocation->target_offset,
                &target_runtime_address)) {
            value.pointer_value = target_runtime_address;
            value.pointer_candidates[0] = target_runtime_address;
          }
        }
      }
    }
  }
  if (!typed_stored_value_has_useful_info(&value) &&
      metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ) {
    (void)typed_value_for_memory_read_operand(lookup, state, platform_state, section_index, source_operand,
      metadata->operand_access_kinds[source_index], &value, NULL);
    if (!typed_stored_value_has_useful_info(&value) && instruction->size_suffix == 'l')
      (void)typed_stored_value_from_field_pointer_read(&value, lookup, state, source_operand, section_index, offset);
  }
  if (instruction->size_suffix != 'l') {
    value.layout_base_id = 0U;
    value.entry_value_id = 0U;
    value.app_address_known = 0U;
    value.app_displacement = 0;
    value.app_base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
    typed_stored_value_forget_concrete_long(&value);
  }
  typed_provenance_append_transfer(&value.provenance, section_index, offset,
    (uint8_t)source_index, (uint8_t)dest_index);
  if (render_lookup_record_typed_address_store(lookup, state, platform_state, section_index, instruction,
      source_index, dest_index, offset, &value) != 0) {
    return -1;
  }
  {
    uint8_t span = 0U;
    (void)platform_operand_memory_span(instruction, dest_index, NULL, NULL, &span);
    typed_state_note_absolute_write(state, lookup, section_index, dest_operand, span);
  }
  if (operand_is_stack_displacement_local(dest_operand, &stack_displacement)) {
    typed_state_clear_stack_write(state, stack_displacement,
      m68k_sim_operand_width_bytes(instruction, (uint8_t)dest_index));
    if (instruction->size_suffix == 'l' && typed_stored_value_has_useful_info(&value))
      typed_state_set_stack_slot(state, stack_displacement, 0U,
        M68K_FUNCTION_SUMMARY_ABI_STACK_CALLER_ARGUMENT, &value, NULL);
    return 0;
  }
  /* Raw scalar identity may cross registers and stack temporaries, where a
   * later typed parameter or field can establish its meaning.  It must not
   * turn arbitrary persistent RAM into an inferred pointer slot. */
  if (!destination_requires_address && value.raw_long_value_known != 0U &&
      value.pointer_value_known == 0U && value.output == NULL &&
      value.struct_id == AMIGA_OS_STRUCT_ID_NONE && value.app_address_known == 0U) {
    uint32_t entry_value_id = value.entry_value_id;
    typed_stored_value_clear(&value);
    value.entry_value_id = entry_value_id;
  }
  if (operand_is_address_memory_local(dest_operand, &base_reg, &base_displacement) && base_reg < 8U &&
      base_reg != 7U && !render_state_operand_uses_app_base(platform_state, base_reg, base_displacement)) {
    uint8_t span = 0U;
    (void)platform_operand_memory_span(instruction, dest_index, NULL, NULL, &span);
    typed_state_clear_base_write(state, base_reg, base_displacement, span);
    if (destination_requires_address && state->addr_regs[base_reg].known &&
        state->addr_regs[base_reg].struct_id != AMIGA_OS_STRUCT_ID_NONE &&
        typed_stored_value_has_useful_info(&value)) {
      typed_state_set_field_slot(state, base_reg, state->addr_regs[base_reg].struct_id,
        state->addr_regs[base_reg].byte_cursor + (int32_t)base_displacement, &value);
    }
    if (typed_stored_value_has_useful_info(&value)) typed_state_set_base_slot(state, base_reg, base_displacement,
      &value);
    if (!allow_lookup_storage || !state->memory_base_regs[base_reg].known) return 0;
  }
  if (!allow_lookup_storage) {
    if (instruction->size_suffix == 'l')
      typed_state_cache_absolute_store(state, lookup, section_index, dest_operand, &value);
    return 0;
  }
  {
    uint8_t storage_kind = 0U;
    size_t storage_section = (size_t)-1;
    int32_t storage_displacement = 0;
    uint32_t storage_address = 0U;
    int added = 0;
    if (!typed_storage_key_for_lookup_memory_operand(lookup, state, platform_state, section_index, dest_operand,
        metadata->operand_access_kinds[dest_index], &storage_kind, &storage_section, &storage_displacement,
        &storage_address)) {
      return 0;
    }
    if (!typed_stored_value_has_useful_info(&value)) {
      if (render_lookup_conflict_typed_storage_slot(lookup, storage_kind, storage_section, storage_displacement,
          storage_address, section_index, offset, &added) != 0) {
        return -1;
      }
      if (added && io_changed != NULL) *io_changed = 1;
      if (storage_kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT) {
        size_t app_index;
        for (app_index = 0U; app_index < lookup->typed_app_slot_count; ++app_index) {
          M68kRenderTypedAppSlot *slot = &lookup->typed_app_slots[app_index];
          if (slot->displacement != (int16_t)storage_displacement || slot->conflicted != 0U) continue;
          slot->conflicted = 1U;
          slot->source_section_index = section_index;
          slot->source_offset = offset;
          if (io_changed != NULL) *io_changed = 1;
        }
      }
      return 0;
    }
    if (render_lookup_add_typed_storage_slot(lookup, storage_kind, storage_section, storage_displacement,
        storage_address, &value, section_index, offset, &added) != 0) {
      return -1;
    }
    if (instruction->size_suffix == 'l')
      typed_state_cache_absolute_store(state, lookup, section_index, dest_operand, &value);
    if (added && io_changed != NULL) *io_changed = 1;
    if (storage_kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT && value.struct_id != AMIGA_OS_STRUCT_ID_NONE) {
      added = 0;
      if (render_lookup_add_typed_app_slot(lookup, (int16_t)storage_displacement, value.struct_id,
          section_index, offset, &added) != 0) {
        return -1;
      }
      if (added && io_changed != NULL) *io_changed = 1;
    }
  }
  return 0;
}

static void render_lookup_conflict_typed_app_slot_for_write(M68kRenderLookup *lookup, int16_t displacement,
    size_t section_index, uint32_t offset, int *io_changed) {
  size_t app_index;
  if (lookup == NULL) return;
  for (app_index = 0U; app_index < lookup->typed_app_slot_count; ++app_index) {
    M68kRenderTypedAppSlot *slot = &lookup->typed_app_slots[app_index];
    if (slot->displacement != displacement || slot->conflicted != 0U) continue;
    slot->conflicted = 1U;
    slot->source_section_index = section_index;
    slot->source_offset = offset;
    if (io_changed != NULL) *io_changed = 1;
  }
}

static int render_lookup_record_untyped_memory_writes(M68kRenderLookup *lookup, M68kRenderTypedState *state,
    const M68kRenderPlatformState *platform_state, size_t section_index, const M68kInstructionIR *instruction,
    uint32_t offset, int allow_lookup_storage, int *io_changed) {
  const M68kSimFormMetadata *metadata = NULL;
  size_t source_index = 0U, dest_index = 0U, operand_index;
  uint8_t base_reg = 0U;
  int16_t base_displacement = 0, stack_displacement = 0;
  if (lookup == NULL || state == NULL || instruction == NULL) return 0;
  if (instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index, &metadata))
    return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    uint8_t storage_kind = 0U;
    size_t storage_section = (size_t)-1;
    int32_t storage_displacement = 0;
    uint32_t storage_address = 0U;
    int added = 0;
    if (platform_operand_memory_access(instruction, operand_index) != M68K_SIM_ACCESS_MEMORY_WRITE) continue;
    {
      M68kRenderTypedStoredValue updated;
      uint8_t span = 0U;
      uint32_t address, id = 0U;
      int64_t delta;
      typed_stored_value_clear(&updated);
      (void)platform_operand_memory_span(instruction, operand_index, NULL, NULL, &span);
      if (operand_index == 1U && instruction->size_suffix == 'l' && span == 4U &&
          operand_absolute_offset_local(operand, &address) && typed_app_cursor_immediate_delta(instruction, &delta)) {
        size_t owner_section = operand->symbol_ref.has_section ? operand->symbol_ref.section_index : section_index;
        const M68kRenderTypedBaseSlot *cell;
        id = typed_absolute_storage_id(lookup, owner_section, address);
        cell = typed_state_absolute_cell(state, id);
        if (cell != NULL && cell->value.entry_value_id)
          updated.entry_value_id = affine_entry_adjust(lookup->affine_entry_context,
            cell->value.entry_value_id, delta);
        if (cell != NULL && cell->value.app_address_known) {
          int64_t next = (int64_t)cell->value.app_displacement + delta;
          if (next >= INT16_MIN && next <= INT16_MAX) {
            updated.app_address_known = 1U;
            updated.app_displacement = (int16_t)next;
            updated.app_base_evidence_kind = cell->value.app_base_evidence_kind;
            updated.provenance = cell->value.provenance;
            typed_provenance_append_transfer(&updated.provenance, section_index, offset, 0U, 1U);
            typed_stored_value_update_known(&updated);
          }
        }
      }
      typed_state_note_absolute_write(state, lookup, section_index, operand, span);
      typed_state_set_absolute_cell(state, id, &updated);
    }
    if (operand_is_stack_displacement_local(operand, &stack_displacement)) {
      uint8_t span = 0U;
      (void)platform_operand_memory_span(instruction, operand_index, NULL, NULL, &span);
      typed_state_clear_stack_write(state, stack_displacement, span);
    }
    if (operand_is_address_memory_local(operand, &base_reg, &base_displacement) && base_reg < 8U &&
        base_reg != 7U && !render_state_operand_uses_app_base(platform_state, base_reg, base_displacement)) {
      uint8_t span = 0U;
      (void)platform_operand_memory_span(instruction, operand_index, NULL, NULL, &span);
      typed_state_clear_base_write(state, base_reg, base_displacement, span);
    }
    if (!allow_lookup_storage) continue;
    if (!typed_storage_key_for_lookup_memory_operand(lookup, state, platform_state, section_index, operand,
        metadata->operand_access_kinds[operand_index], &storage_kind, &storage_section, &storage_displacement,
        &storage_address)) {
      continue;
    }
    if (render_lookup_conflict_typed_storage_slot(lookup, storage_kind, storage_section, storage_displacement,
        storage_address, section_index, offset, &added) != 0) {
      return -1;
    }
    if (added && io_changed != NULL) *io_changed = 1;
    if (storage_kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT) {
      render_lookup_conflict_typed_app_slot_for_write(lookup, (int16_t)storage_displacement, section_index, offset,
        io_changed);
    }
  }
  return 0;
}

static int typed_stored_value_from_pointer_table_read(M68kRenderTypedStoredValue *value,
    const M68kRenderLookup *lookup, const M68kRenderTypedState *state, const M68kOperandIR *operand,
    size_t section_index, uint32_t offset, const M68kRenderTypedMemoryBaseValue *override_memory_base) {
  M68kRenderTypedMemoryBaseValue memory_base;
  const M68kAnalysisStructuredDataItem *item = NULL;
  uint16_t struct_id;
  uint32_t entry_stride = 4U;
  uint32_t domain_min = 0U, domain_max = 0U, entry_index;
  uint8_t has_domain = 0U;
  if (value == NULL || lookup == NULL || state == NULL || operand == NULL) return 0;
  if (override_memory_base != NULL) memory_base = *override_memory_base;
  else if (!typed_state_copy_memory_base(state, operand, &memory_base)) return 0;
  item = memory_base.pointer_table_known ?
    lookup_pointer_table_item_for_contract(lookup, memory_base.pointer_table_section_index,
      memory_base.pointer_table_offset, memory_base.pointer_table_size) :
    (memory_base.known ? lookup_pointer_table_item_covering_address(lookup, memory_base.section_index,
      memory_base.offset) : NULL);
  /* A PC-indexed pointer load has no address-register base to carry the
   * table identity.  The canonical structured item already names its exact
   * consumer, so use that durable relation when ordinary memory-base
   * propagation cannot identify the table. */
  if (item == NULL && lookup->policy != NULL) {
    size_t policy_index;
    for (policy_index = 0U; policy_index < lookup->policy->structured_data_item_count; ++policy_index) {
      const M68kAnalysisStructuredDataItem *candidate = &lookup->policy->structured_data_items[policy_index];
      if (!candidate->has_section_index || candidate->section_index != section_index ||
          !candidate->has_consumer || candidate->consumer_section != section_index ||
          candidate->consumer_offset != offset || candidate->table_kind_id != M68K_ANALYSIS_TABLE_KIND_POINTER ||
          m68k_analysis_structured_data_table_entry_size(candidate) != 4U || candidate->size < 4U) continue;
      item = candidate;
      break;
    }
  }
  /* One-past is a valid cursor value, not a dereferenceable table entry. */
  if (item != NULL && memory_base.known &&
      (memory_base.section_index != item->section_index || memory_base.offset < item->offset ||
       memory_base.offset - item->offset > item->size ||
       4U > item->size - (memory_base.offset - item->offset))) return 0;
  struct_id = memory_base.pointer_table_struct_id != AMIGA_OS_STRUCT_ID_NONE ?
    memory_base.pointer_table_struct_id : (item != NULL && item->pointer_struct_id != AMIGA_OS_STRUCT_ID_NONE ?
      item->pointer_struct_id : lookup_policy_struct_id_by_name(lookup->policy, item != NULL ? item->pointer_struct : NULL));
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE) return 0;
  typed_stored_value_clear(value);
  value->struct_id = struct_id;
  if (item != NULL) {
    entry_stride = m68k_analysis_structured_data_table_entry_size(item);
    if (entry_stride == 0U) entry_stride = 4U;
    value->table_origin.has_origin = 1U;
    value->table_origin.table_section_index = item->section_index;
    value->table_origin.table_start_offset = item->offset;
    value->table_origin.consumer_section_index = item->consumer_section;
    value->table_origin.consumer_offset = item->consumer_offset;
    value->table_origin.entry_index = UINT32_MAX;
    value->table_origin.index_min = 0U;
    value->table_origin.index_max = 0U;
    if (item->has_index_mask_domain) {
      domain_min = item->index_mask_min;
      domain_max = item->index_mask_max;
      has_domain = 1U;
    } else if (item->has_index_compare_domain) {
      domain_min = item->index_compare_min;
      domain_max = item->index_compare_max;
      has_domain = 1U;
    } else if (item->has_index_loop_domain) {
      domain_min = item->index_loop_min;
      domain_max = item->index_loop_max;
      has_domain = 1U;
    }
    if (item->has_consumer && item->has_index_register && has_domain) {
      value->table_origin.selection_kind = M68K_ADDRESS_VALUE_TABLE_SELECTION_FINITE;
      value->table_origin.index_min = domain_min;
      value->table_origin.index_max = domain_max;
      if (domain_max < domain_min || (domain_min % entry_stride) != 0U ||
          (domain_max % entry_stride) != 0U || domain_max / entry_stride >= item->size / entry_stride) {
        value->table_origin.selection_kind = M68K_ADDRESS_VALUE_TABLE_SELECTION_TERMINAL;
        value->table_origin.terminal_kind = M68K_ADDRESS_VALUE_TERMINAL_INVALID;
      } else {
        for (entry_index = domain_min / entry_stride; entry_index <= domain_max / entry_stride; ++entry_index) {
          if (entry_index - domain_min / entry_stride >= sizeof(value->pointer_candidates) / sizeof(value->pointer_candidates[0])) {
            value->address_value_candidate_overflow = 1U;
            value->table_origin.selection_kind = M68K_ADDRESS_VALUE_TABLE_SELECTION_TERMINAL;
            value->table_origin.terminal_kind = M68K_ADDRESS_VALUE_TERMINAL_CANDIDATE_OVERFLOW;
            break;
          }
        }
      }
    } else if (!item->has_index_register) {
      value->table_origin.selection_kind = M68K_ADDRESS_VALUE_TABLE_SELECTION_SINGLETON;
      if (memory_base.known && memory_base.section_index == item->section_index &&
          memory_base.offset >= item->offset && memory_base.offset - item->offset < item->size &&
          ((memory_base.offset - item->offset) % entry_stride) == 0U) {
        value->table_origin.entry_index = (memory_base.offset - item->offset) / entry_stride;
        if (item->has_target) {
          value->pointer_target_known = 1U;
          value->pointer_target_section_index = item->target_section;
          value->pointer_target_offset = item->target_offset;
        }
        /* The canonical source-analysis table entry supplies the value and
         * target later.  The renderer records only the table identity. */
      }
    } else {
      value->table_origin.selection_kind = M68K_ADDRESS_VALUE_TABLE_SELECTION_TERMINAL;
      value->table_origin.terminal_kind = M68K_ADDRESS_VALUE_TERMINAL_UNREPRESENTABLE;
    }
    /* A terminal selection is never a partially useful pointer value.  In
     * particular, candidate-capacity overflow must not leak the prefix that
     * happened to fit the transient array into later typed consumers. */
    if (value->table_origin.selection_kind == M68K_ADDRESS_VALUE_TABLE_SELECTION_TERMINAL) {
      value->pointer_value_known = 0U;
      value->pointer_candidate_count = 0U;
    }
  }
  value->provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA, section_index, offset);
  typed_stored_value_update_known(value);
  return 1;
}

/* A direct indexed JSR/JMP has no register destination, but its data target
 * is still the same table-entry load contract.  Seed the normal table-read
 * transfer with the decoder's already-proven data target and let the common
 * candidate/origin path feed the callable consumer. */
static int typed_stored_value_from_direct_pointer_table_read(M68kRenderTypedStoredValue *value,
    const M68kRenderLookup *lookup, const M68kDecodeCandidate *candidate, const M68kOperandIR *operand,
    size_t section_index, uint32_t offset) {
  M68kRenderTypedMemoryBaseValue memory_base;
  const M68kAnalysisStructuredDataItem *item;
  M68kRenderTypedState empty_state;
  size_t table_section_index;
  uint32_t table_offset;
  int64_t pc_target;
  int has_data_target;
  if (value == NULL || lookup == NULL || candidate == NULL || operand == NULL ||
      ((has_data_target = candidate_data_target_for_operand(candidate, 0U, &table_section_index, &table_offset)) == 0 &&
       !(operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U &&
         operand->value.ea_reg == 2U))) return 0;
  if (!has_data_target && operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 7U &&
      operand->value.ea_reg == 2U) {
    pc_target = (int64_t)candidate->offset + 2 + (int16_t)(operand->value.value & 0xffffU);
    if (pc_target < 0 || pc_target > UINT32_MAX) return 0;
    table_section_index = section_index;
    table_offset = (uint32_t)pc_target;
  }
  item = lookup_pointer_table_item_covering_address(lookup, table_section_index, table_offset);
  if (item == NULL) return 0;
  memset(&empty_state, 0, sizeof(empty_state));
  typed_memory_base_clear(&memory_base);
  memory_base.known = 1U;
  memory_base.section_index = table_section_index;
  memory_base.offset = table_offset;
  memory_base.pointer_table_known = 1U;
  memory_base.pointer_table_struct_id = item->pointer_struct_id != AMIGA_OS_STRUCT_ID_NONE ?
    item->pointer_struct_id : lookup_policy_struct_id_by_name(lookup->policy, item->pointer_struct);
  memory_base.pointer_table_section_index = item->section_index;
  memory_base.pointer_table_offset = item->offset;
  memory_base.pointer_table_size = item->size;
  return typed_stored_value_from_pointer_table_read(value, lookup, &empty_state, operand,
    section_index, offset, &memory_base);
}

/* A declared callback table is also a durable table-origin contract when the
 * ordinary pointer-table descriptor is not present in the render policy.  The
 * value carries only the table identity; callback entry validation and effect
 * intersection remain owned by the callback-summary path. */
static int typed_stored_value_bind_callback_table_origin(M68kRenderTypedStoredValue *value,
    const M68kRenderLookup *lookup, const M68kRenderTypedMemoryBaseValue *memory_base,
    size_t consumer_section_index, uint32_t consumer_offset) {
  const M68kAnalysisFunctionSummary *match = NULL;
  size_t index;
  if (value == NULL || lookup == NULL || lookup->policy == NULL || memory_base == NULL ||
      memory_base->known == 0U) return 0;
  for (index = 0U; index < lookup->policy->function_summary_count; ++index) {
    const M68kAnalysisFunctionSummary *summary = &lookup->policy->function_summaries[index];
    if (summary->callable_kind != M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_CALLBACK_TABLE ||
        summary->has_section_index == 0U || summary->section_index != memory_base->section_index ||
        summary->table_offset != memory_base->offset || summary->entry_count == 0U) continue;
    if (match != NULL) return 0;
    match = summary;
  }
  if (match == NULL) return 0;
  typed_stored_value_clear(value);
  value->table_origin.has_origin = 1U;
  value->table_origin.table_section_index = (uint32_t)memory_base->section_index;
  value->table_origin.table_start_offset = memory_base->offset;
  value->table_origin.consumer_section_index = (uint32_t)consumer_section_index;
  value->table_origin.consumer_offset = consumer_offset;
  value->table_origin.entry_index = UINT32_MAX;
  value->table_origin.selection_kind = M68K_ADDRESS_VALUE_TABLE_SELECTION_NONE;
  value->provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA,
    consumer_section_index, consumer_offset);
  typed_stored_value_update_known(value);
  return 1;
}

static uint8_t typed_flow_instruction_written_unsaved_address_mask(const M68kInstructionIR *instruction,
    uint8_t requested_mask, uint8_t saved_mask) {
  uint16_t writes = 0U;
  if (instruction == NULL || m68k_sim_metadata_for_instruction(instruction) == NULL)
    return requested_mask & (uint8_t)~saved_mask;
  for (size_t i = 0U; i < instruction->operand_count && i < 4U; ++i)
    writes |= platform_operand_register_write_mask(instruction, i);
  return (uint8_t)(writes >> 8U) & requested_mask & (uint8_t)~saved_mask;
}

static int typed_flow_local_absolute_jump_target(const M68kRenderLookup *lookup,
    const M68kDecodeCandidate *candidate, size_t *out_section, uint32_t *out_offset);

static int typed_flow_first_local_control_target(const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint32_t *out_target) {
  size_t index;
  int found = 0;
  if (out_target != NULL) *out_target = 0U;
  if (section == NULL || candidate == NULL || out_target == NULL) return 0;
  {
    size_t target_section;
    uint32_t target_offset;
    if (typed_flow_local_absolute_jump_target(lookup, candidate, &target_section, &target_offset)) {
      if (target_section != section->section_index || target_offset >= section->size) return 0;
      *out_target = target_offset; return 1;
    }
  }
  for (index = 0U; index < candidate->target_count; ++index) {
    const M68kDecodeTarget *target = &candidate->targets[index];
    if ((target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_JUMP) &&
        target->has_section && target->section_index == section->section_index && target->offset < section->size) {
      if (found && *out_target != target->offset) return 0;
      *out_target = target->offset; found = 1;
    }
  }
  return found;
}

static int typed_flow_local_absolute_control_target(const M68kRenderLookup *lookup,
    const M68kDecodeCandidate *candidate, uint8_t flow,
    size_t *out_section_index, uint32_t *out_target_offset) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  const M68kOperandIR *operand;
  uint32_t absolute_address;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (lookup == NULL || candidate == NULL || out_section_index == NULL || out_target_offset == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      (metadata = m68k_sim_metadata_for_instruction(&instruction)) == NULL ||
      metadata->flow_kind != flow || metadata->target_operand_index >= instruction.operand_count) {
    return candidate_direct_target(candidate, out_section_index, out_target_offset);
  }
  operand = &instruction.operands[metadata->target_operand_index];
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 7U || (operand->value.ea_reg != 0U && operand->value.ea_reg != 1U))
    return candidate_direct_target(candidate, out_section_index, out_target_offset);
  if (!operand_absolute_offset_local(operand, &absolute_address)) return 0;
  /* A pointer-only observed view is not generally executable.  An exact
     runtime code label independently proves this one absolute call target. */
  if (lookup->policy != NULL) {
    uint16_t label_index;
    for (label_index = 0U; label_index < lookup->policy->named_label_count; ++label_index) {
      const M68kAnalysisNamedLabel *label = &lookup->policy->named_labels[label_index];
      size_t range_index;
      if (label->domain != M68K_ANALYSIS_LABEL_DOMAIN_RUNTIME || label->offset != absolute_address) continue;
      for (range_index = 0U; range_index < lookup->policy->runtime_range_count; ++range_index) {
        const M68kAnalysisRuntimeRange *range = &lookup->policy->runtime_ranges[range_index];
        uint32_t delta;
        size_t section_index = range->has_section_index ? range->section_index : 0U;
        if ((range->use_mask != M68K_ANALYSIS_RUNTIME_RANGE_USE_DEFAULT &&
             (range->use_mask & M68K_ANALYSIS_RUNTIME_RANGE_USE_POINTER_TARGET) == 0U) ||
            section_index >= lookup->section_count || absolute_address < range->runtime_address) continue;
        delta = absolute_address - range->runtime_address;
        if (delta >= range->size || range->offset > UINT32_MAX - delta) continue;
        *out_section_index = section_index;
        *out_target_offset = range->offset + delta;
        return 1;
      }
    }
  }
  if (render_lookup_pointer_value_to_object_source_location(lookup, absolute_address, out_section_index,
      out_target_offset)) return 1;
  return candidate_direct_target(candidate, out_section_index, out_target_offset);
}

/* CALL and absolute JMP share the same executable runtime/source mapping.
 * Indirect multi-target jumps keep their existing complete successor vector. */
static int typed_flow_local_call_target(const M68kRenderLookup *lookup, const M68kDecodeCandidate *candidate,
    size_t *out_section_index, uint32_t *out_target_offset) {
  return typed_flow_local_absolute_control_target(lookup, candidate, M68K_SIM_FLOW_CALL,
    out_section_index, out_target_offset);
}

static int typed_flow_local_absolute_jump_target(const M68kRenderLookup *lookup,
    const M68kDecodeCandidate *candidate, size_t *out_section, uint32_t *out_offset) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  const M68kOperandIR *operand;
  if (candidate == NULL || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      (metadata = m68k_sim_metadata_for_instruction(&instruction)) == NULL ||
      metadata->flow_kind != M68K_SIM_FLOW_JUMP || metadata->target_operand_index >= instruction.operand_count)
    return 0;
  operand = &instruction.operands[metadata->target_operand_index];
  if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_mode != 7U || (operand->value.ea_reg != 0U && operand->value.ea_reg != 1U))
    return 0;
  return typed_flow_local_absolute_control_target(lookup, candidate, M68K_SIM_FLOW_JUMP, out_section, out_offset);
}

/* A bounded callee proof starts with no hardware constants. These compact
 * values are independent of caller origins and cannot manufacture inputs. */
typedef struct M68kLocalHardwareValues {
  uint32_t known[2];
  uint16_t ids[2][8];
} M68kLocalHardwareValues;

static void local_hardware_unpack(M68kRenderPlatformState *state, const M68kLocalHardwareValues *values) {
  memset(state, 0, sizeof(*state));
  state->data_hardware_base_known = values->known[0];
  state->address_hardware_base_known = values->known[1];
  memcpy(state->data_hardware_base_id, values->ids[0], sizeof(values->ids[0]));
  memcpy(state->address_hardware_base_id, values->ids[1], sizeof(values->ids[1]));
}

static void local_hardware_pack(M68kLocalHardwareValues *values, const M68kRenderPlatformState *state) {
  values->known[0] = state->data_hardware_base_known;
  values->known[1] = state->address_hardware_base_known;
  memcpy(values->ids[0], state->data_hardware_base_id, sizeof(values->ids[0]));
  memcpy(values->ids[1], state->address_hardware_base_id, sizeof(values->ids[1]));
}

static void local_hardware_apply_call(M68kLocalHardwareValues *values,
    const M68kAnalysisFunctionSummary *summary) {
  uint8_t kind, reg, index;
  if (summary != NULL && summary->effects_invalid != 0U) summary = NULL;
  for (kind = 0U; kind < 2U; ++kind) {
    for (reg = 0U; reg < 8U; ++reg) {
      if (function_summary_register_effect(summary,
          kind == 0U ? M68K_ANALYSIS_REGISTER_DATA : M68K_ANALYSIS_REGISTER_ADDRESS, reg) !=
          M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED) {
        values->known[kind] &= ~((uint32_t)1U << reg);
        values->ids[kind][reg] = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
      }
    }
  }
  if (summary == NULL || summary->result_contract_invalid != 0U) return;
  for (index = 0U; index < summary->result_count; ++index) {
    const M68kAnalysisFunctionSummaryResult *result = &summary->results[index];
    if (result->kind != M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_HARDWARE_BASE ||
        result->location.kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER ||
        result->location.width != 4U || result->location.register_count != 1U) continue;
    reg = result->location.registers[0].register_index;
    kind = result->location.registers[0].register_kind == M68K_ANALYSIS_REGISTER_DATA ? 0U : 1U;
    if (reg >= 8U) continue;
    values->known[kind] |= (uint32_t)1U << reg;
    values->ids[kind][reg] = result->hardware_base_id;
  }
}

/* Direct-body identity is a pointer-sized register value, not an address-mode
 * claim. Keep the entry register class in one compact encoding so an ABI
 * pointer can enter in Dn and return through An (or vice versa). */
#define M68K_TYPED_FLOW_ENTRY_ORIGIN_DATA_FLAG 0x80U
static uint8_t typed_flow_entry_origin_make(uint8_t register_kind, uint8_t register_index) {
  if (register_index >= 8U) return 0xffU;
  return register_kind == M68K_ANALYSIS_REGISTER_DATA ?
    (uint8_t)(M68K_TYPED_FLOW_ENTRY_ORIGIN_DATA_FLAG | register_index) : register_index;
}

static int typed_flow_entry_origin_decode(uint8_t origin, uint8_t *out_kind, uint8_t *out_index) {
  uint8_t index = origin & 0x7fU;
  if (index >= 8U) return 0;
  if (out_kind != NULL)
    *out_kind = (origin & M68K_TYPED_FLOW_ENTRY_ORIGIN_DATA_FLAG) != 0U ?
      M68K_ANALYSIS_REGISTER_DATA : M68K_ANALYSIS_REGISTER_ADDRESS;
  if (out_index != NULL) *out_index = index;
  return 1;
}

static uint8_t typed_flow_entry_origin_ordinal(uint8_t origin) {
  uint8_t kind = 0U, index = 0U;
  if (!typed_flow_entry_origin_decode(origin, &kind, &index)) return 0xffU;
  return kind == M68K_ANALYSIS_REGISTER_DATA ? (uint8_t)(8U + index) : index;
}

#include "m68k_direct_body_worklist.inc"

static int typed_flow_local_callee_effect_summary(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index, uint32_t target_offset,
    M68kAnalysisFunctionSummary *out_summary, uint8_t *out_limit_hit) {
  M68kTypedLocalCalleeState *worklist = NULL, initial = {0};
  M68kLocalCalleeInputs inputs = {0};
  size_t work_count = 0U, work_capacity = 0U, peak_pending = 0U;
  int result = 0, frame_conflict = 0;
  const M68kDecodeSectionIR *section;
  uint8_t returned = 0U, returned_mask = 0U;
  uint16_t input_origin_mask = 0U;
  uint8_t returned_origin[8], returned_data_origin[8];
  M68kLocalHardwareValues returned_hardware;
  M68kFunctionSummaryMemoryEffectIR static_writes[M68K_ANALYSIS_FUNCTION_SUMMARY_MEMORY_EFFECT_LIMIT] = {0};
  M68kFunctionSummaryEscapeIR escapes[M68K_ANALYSIS_FUNCTION_SUMMARY_ESCAPE_LIMIT] = {0};
  uint8_t static_write_count = 0U;
  uint8_t escape_count = 0U;
  uint8_t memory_effects_unknown = 0U, escape_effects_unknown = 0U;
  const uint8_t requested_mask = 0xffU;
  if (out_limit_hit != NULL) *out_limit_hit = 0U;
  if (out_summary == NULL || lookup == NULL || decode == NULL || accepted_start == NULL ||
      section_index >= decode->section_count || accepted_start[section_index] == NULL) goto cleanup;
  section = &decode->sections[section_index];
  if (target_offset >= section->size || accepted_start[section_index][target_offset] == 0U) goto cleanup;
  memset(&returned_hardware, 0, sizeof(returned_hardware));
  initial.offset = target_offset;
  initial.preserved_mask = requested_mask;
  initial.stack_entry_stable = 1U;
  for (uint8_t reg = 0U; reg < 8U; ++reg) {
    initial.entry_origin[reg] = reg;
    initial.data_origin[reg] = typed_flow_entry_origin_make(M68K_ANALYSIS_REGISTER_DATA, reg);
  }
  if (local_callee_push(&worklist, &work_count, &work_capacity, &initial) != 0) goto resource_limit;
  while (work_count != 0U) {
    M68kTypedLocalCalleeState state = worklist[--work_count];
    for (;;) {
      const M68kDecodeCandidate *candidate;
      M68kInstructionIR instruction;
      const M68kSimFormMetadata *metadata;
      uint32_t branch_target = 0U;
      uint8_t index, before_origins[16];
      M68kStackRegisterTransfer stack_transfer = {0};
      int has_stack_transfer;
      int visit = local_callee_input_visit(&inputs, &state);
      if (visit == 0) break;
      if (visit == -2) goto resource_limit;
      if (visit < 0) { frame_conflict = 1; goto cleanup; }
      candidate = m68k_decode_ir_find_candidate_at_offset(section, state.offset);
      if (state.offset >= section->size || candidate == NULL || candidate->byte_count == 0U ||
          accepted_start[section_index][state.offset] == 0U ||
          m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) goto cleanup;
      metadata = m68k_sim_metadata_for_instruction(&instruction);
      if (metadata == NULL) goto cleanup;
      has_stack_transfer = platform_instruction_stack_register_transfer(&instruction, &stack_transfer);
      for (uint8_t reg = 0U; reg < 8U; ++reg) {
        before_origins[reg] = state.data_origin[reg];
        before_origins[reg + 8U] = state.entry_origin[reg];
      }
      /* A private save-frame address must not escape this bounded ownership
       * proof. Such routines retain an explicit unsupported contract. */
      for (size_t operand_index = 0U; operand_index < instruction.operand_count; ++operand_index) {
        const M68kOperandIR *operand = &instruction.operands[operand_index];
        if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_COMPUTE_ADDRESS &&
            (operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
            operand->value.ea_mode != 7U && operand->value.ea_reg == 7U) {
          uint8_t dest_reg;
          int32_t delta;
          if (!(instruction.mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction.operand_count == 2U &&
                operand_address_register_index_local(&instruction.operands[1], &dest_reg) && dest_reg == 7U &&
                instruction_stack_delta_for_comment(&instruction, &delta))) goto cleanup;
        }
        if (metadata->operation_type == M68K_SIM_OP_MOVE && operand_index == metadata->source_operand_index &&
            operand_address_register_index_local(operand, &index) && index == 7U) goto cleanup;
      }
      /* Exact data targets give a durable static-storage subject.  Other
       * writes have no caller identity at this layer, so remain unknown. */
      for (uint8_t operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U;
           ++operand_index) {
        size_t static_section_index = section_index;
        uint32_t static_offset;
        uint8_t prior;
        size_t move_source_index = 0U, move_dest_index = 0U;
        uint8_t source_reg = 0U;
        uint8_t source_origin = 0xffU;
        if (platform_operand_memory_access(&instruction, operand_index) != M68K_SIM_ACCESS_MEMORY_WRITE) continue;
        if (operand_is_predec_a7_local(&instruction.operands[operand_index]) ||
            operand_is_postinc_a7_local(&instruction.operands[operand_index])) {
          state.stack_entry_stable = 0U;
          memory_effects_unknown = 1U;
          escape_effects_unknown = 1U;
          continue;
        }
        if (instruction_move_operand_indices_from_metadata(&instruction, &move_source_index, &move_dest_index,
              NULL) && move_dest_index == operand_index &&
            operand_address_register_index_local(&instruction.operands[move_source_index], &source_reg) &&
            source_reg < 8U && state.entry_origin[source_reg] < 8U) {
          source_origin = state.entry_origin[source_reg];
          input_origin_mask |= (uint16_t)(1U << source_origin);
        }
        {
          uint8_t base_reg = 0U;
          int16_t base_displacement = 0;
          if (operand_is_address_memory_local(&instruction.operands[operand_index], &base_reg,
              &base_displacement) && base_reg == 7U) {
            uint32_t caller_offset;
            M68kFunctionSummaryMemoryEffectIR *effect;
            /* JSR pushes a four-byte return address.  With the entry stack
             * still intact, callee `4(a7)` is caller argument offset zero. */
            if (state.stack_entry_stable == 0U || base_displacement < 4) {
              memory_effects_unknown = 1U;
              escape_effects_unknown = 1U;
              continue;
            }
            caller_offset = (uint32_t)(base_displacement - 4);
            for (prior = 0U; prior < static_write_count; ++prior) {
              const M68kFunctionSummaryEffectSubjectIR *subject = &static_writes[prior].subject;
              if (subject->kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STACK &&
                  subject->offset == caller_offset &&
                  subject->stack_convention == M68K_FUNCTION_SUMMARY_ABI_STACK_CALLER_ARGUMENT) break;
            }
            if (prior == static_write_count && static_write_count < M68K_ANALYSIS_FUNCTION_SUMMARY_MEMORY_EFFECT_LIMIT) {
              effect = &static_writes[static_write_count++];
              memset(effect, 0, sizeof(*effect));
              effect->kind = M68K_FUNCTION_SUMMARY_MEMORY_WRITE;
              effect->subject.kind = M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STACK;
              effect->subject.offset = caller_offset;
              effect->subject.stack_convention = M68K_FUNCTION_SUMMARY_ABI_STACK_CALLER_ARGUMENT;
            } else if (prior == static_write_count) memory_effects_unknown = 1U;
            if (source_origin >= 8U) {
              escape_effects_unknown = 1U;
            } else {
              for (prior = 0U; prior < escape_count; ++prior) {
                const M68kFunctionSummaryEscapeIR *escape = &escapes[prior];
                if (escape->source_location.registers[0].register_index == source_origin &&
                    escape->sink_subject.kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STACK &&
                    escape->sink_subject.offset == caller_offset &&
                    escape->sink_subject.stack_convention == M68K_FUNCTION_SUMMARY_ABI_STACK_CALLER_ARGUMENT) break;
              }
              if (prior == escape_count && escape_count < M68K_ANALYSIS_FUNCTION_SUMMARY_ESCAPE_LIMIT) {
                M68kFunctionSummaryEscapeIR *escape = &escapes[escape_count++];
                memset(escape, 0, sizeof(*escape));
                escape->source_kind = M68K_FUNCTION_SUMMARY_ESCAPE_SOURCE_INPUT;
                escape->source_location.kind = M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
                escape->source_location.width = 4U;
                escape->source_location.register_count = 1U;
                escape->source_location.registers[0].register_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
                escape->source_location.registers[0].register_index = source_origin;
                escape->sink_subject.kind = M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STACK;
                escape->sink_subject.offset = caller_offset;
                escape->sink_subject.stack_convention = M68K_FUNCTION_SUMMARY_ABI_STACK_CALLER_ARGUMENT;
              } else if (prior == escape_count) escape_effects_unknown = 1U;
            }
            continue;
          }
          if (operand_is_address_memory_local(&instruction.operands[operand_index], &base_reg,
              &base_displacement) && typed_flow_entry_origin_decode(state.entry_origin[base_reg], NULL, NULL)) {
            M68kFunctionSummaryMemoryEffectIR *effect;
            uint8_t origin = state.entry_origin[base_reg];
            input_origin_mask |= (uint16_t)(1U << typed_flow_entry_origin_ordinal(origin));
            for (prior = 0U; prior < static_write_count; ++prior) {
              const M68kFunctionSummaryEffectSubjectIR *subject = &static_writes[prior].subject;
              if (subject->kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_INPUT && subject->input_index == origin) break;
            }
            if (prior == static_write_count && static_write_count < M68K_ANALYSIS_FUNCTION_SUMMARY_MEMORY_EFFECT_LIMIT) {
              effect = &static_writes[static_write_count++];
              memset(effect, 0, sizeof(*effect));
              effect->kind = M68K_FUNCTION_SUMMARY_MEMORY_WRITE;
              effect->subject.kind = M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_INPUT;
              /* Temporarily the entry-register identity; compacted to an ABI
               * input index once every returned path has been examined. */
              effect->subject.input_index = origin;
            } else if (prior == static_write_count) memory_effects_unknown = 1U;
            if (source_origin >= 8U) {
              escape_effects_unknown = 1U;
            } else {
              for (prior = 0U; prior < escape_count; ++prior) {
                const M68kFunctionSummaryEscapeIR *escape = &escapes[prior];
                if (escape->source_location.registers[0].register_index == source_origin &&
                    escape->sink_subject.kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_INPUT &&
                    escape->sink_subject.input_index == origin) break;
              }
              if (prior == escape_count && escape_count < M68K_ANALYSIS_FUNCTION_SUMMARY_ESCAPE_LIMIT) {
                M68kFunctionSummaryEscapeIR *escape = &escapes[escape_count++];
                memset(escape, 0, sizeof(*escape));
                escape->source_kind = M68K_FUNCTION_SUMMARY_ESCAPE_SOURCE_INPUT;
                /* Entry identities are compacted after the full input set is known. */
                escape->source_location.kind = M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
                escape->source_location.width = 4U;
                escape->source_location.register_count = 1U;
                escape->source_location.registers[0].register_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
                escape->source_location.registers[0].register_index = source_origin;
                escape->sink_subject.kind = M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_INPUT;
                escape->sink_subject.input_index = origin;
              } else if (prior == escape_count) {
                escape_effects_unknown = 1U;
              }
            }
            continue;
          }
        }
        if (!candidate_data_target_for_operand(candidate, operand_index, &static_section_index, &static_offset) &&
            !operand_absolute_offset_local(&instruction.operands[operand_index], &static_offset)) {
          memory_effects_unknown = 1U;
          escape_effects_unknown = 1U;
          continue;
        }
        if (static_section_index >= decode->section_count)
          static_section_index = section_index;
        {
          const M68kAnalysisAbstractRegion *abstract_region = lookup_abstract_region_for_source_range(lookup,
            static_section_index, static_offset, instruction_size_suffix_bytes_local(instruction.size_suffix));
          if (abstract_region != NULL) {
            for (prior = 0U; prior < static_write_count; ++prior) {
              const M68kFunctionSummaryEffectSubjectIR *subject = &static_writes[prior].subject;
              if (subject->kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_ABSTRACT_REGION &&
                  strcmp(subject->abstract_region_id, abstract_region->region_id) == 0) break;
            }
            if (prior == static_write_count && static_write_count < M68K_ANALYSIS_FUNCTION_SUMMARY_MEMORY_EFFECT_LIMIT) {
              M68kFunctionSummaryMemoryEffectIR *effect = &static_writes[static_write_count++];
              memset(effect, 0, sizeof(*effect));
              effect->kind = M68K_FUNCTION_SUMMARY_MEMORY_WRITE;
              effect->subject.kind = M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_ABSTRACT_REGION;
              snprintf(effect->subject.abstract_region_id, sizeof(effect->subject.abstract_region_id), "%s",
                abstract_region->region_id);
            } else if (prior == static_write_count) memory_effects_unknown = 1U;
            if (source_origin >= 8U) {
              escape_effects_unknown = 1U;
            } else {
              for (prior = 0U; prior < escape_count; ++prior) {
                const M68kFunctionSummaryEscapeIR *escape = &escapes[prior];
                if (escape->source_location.registers[0].register_index == source_origin &&
                    escape->sink_subject.kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_ABSTRACT_REGION &&
                    strcmp(escape->sink_subject.abstract_region_id, abstract_region->region_id) == 0) break;
              }
              if (prior == escape_count && escape_count < M68K_ANALYSIS_FUNCTION_SUMMARY_ESCAPE_LIMIT) {
                M68kFunctionSummaryEscapeIR *escape = &escapes[escape_count++];
                memset(escape, 0, sizeof(*escape));
                escape->source_kind = M68K_FUNCTION_SUMMARY_ESCAPE_SOURCE_INPUT;
                escape->source_location.kind = M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
                escape->source_location.width = 4U;
                escape->source_location.register_count = 1U;
                escape->source_location.registers[0].register_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
                escape->source_location.registers[0].register_index = source_origin;
                escape->sink_subject.kind = M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_ABSTRACT_REGION;
                snprintf(escape->sink_subject.abstract_region_id, sizeof(escape->sink_subject.abstract_region_id),
                  "%s", abstract_region->region_id);
              } else if (prior == escape_count) escape_effects_unknown = 1U;
            }
            continue;
          }
        }
        for (prior = 0U; prior < static_write_count; ++prior) {
          const M68kFunctionSummaryEffectSubjectIR *subject = &static_writes[prior].subject;
          if (subject->section_index == static_section_index && subject->offset == static_offset) break;
        }
        if (prior == static_write_count) {
          if (static_write_count == M68K_ANALYSIS_FUNCTION_SUMMARY_MEMORY_EFFECT_LIMIT) {
            memory_effects_unknown = 1U;
          } else {
            M68kFunctionSummaryMemoryEffectIR *effect = &static_writes[static_write_count++];
            memset(effect, 0, sizeof(*effect));
            effect->kind = M68K_FUNCTION_SUMMARY_MEMORY_WRITE;
            effect->subject.kind = M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STATIC_STORAGE;
            effect->subject.section_index = (uint32_t)static_section_index;
            effect->subject.offset = static_offset;
          }
        }
        if (source_origin >= 8U) {
          escape_effects_unknown = 1U;
        } else {
          for (prior = 0U; prior < escape_count; ++prior) {
            const M68kFunctionSummaryEscapeIR *escape = &escapes[prior];
            if (escape->source_location.registers[0].register_index == source_origin &&
                escape->sink_subject.kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STATIC_STORAGE &&
                escape->sink_subject.section_index == static_section_index && escape->sink_subject.offset == static_offset)
              break;
          }
          if (prior == escape_count && escape_count < M68K_ANALYSIS_FUNCTION_SUMMARY_ESCAPE_LIMIT) {
            M68kFunctionSummaryEscapeIR *escape = &escapes[escape_count++];
            memset(escape, 0, sizeof(*escape));
            escape->source_kind = M68K_FUNCTION_SUMMARY_ESCAPE_SOURCE_INPUT;
            escape->source_location.kind = M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
            escape->source_location.width = 4U;
            escape->source_location.register_count = 1U;
            escape->source_location.registers[0].register_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
            escape->source_location.registers[0].register_index = source_origin;
            escape->sink_subject.kind = M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STATIC_STORAGE;
            escape->sink_subject.section_index = (uint32_t)static_section_index;
            escape->sink_subject.offset = static_offset;
          } else if (prior == escape_count) {
            escape_effects_unknown = 1U;
          }
        }
      }
      /* The decoded write footprint is shared with typed values and platform
       * bases. Only lossless LONG direct-register copies retain identity. */
      for (size_t i = 0U; i < instruction.operand_count && i < 4U; ++i) {
        uint16_t writes = platform_operand_register_write_mask(&instruction, i);
        for (uint8_t reg = 0U; reg < 8U; ++reg) {
          if (writes & (1U << reg)) state.data_origin[reg] = 0xffU;
          if (writes & (1U << (reg + 8U))) state.entry_origin[reg] = 0xffU;
        }
      }
      if (metadata->operation_type == M68K_SIM_OP_MOVE && instruction.size_suffix == 'l' &&
          instruction.operand_count == 2U) {
        uint8_t source_kind, source_reg, dest_kind, dest_reg;
        if (m68k_instruction_operand_direct_register(&instruction.operands[0], &source_kind, &source_reg) &&
            m68k_instruction_operand_direct_register(&instruction.operands[1], &dest_kind, &dest_reg) &&
            source_reg < 8U && dest_reg < 8U) {
          uint8_t origin = before_origins[source_reg + (source_kind ? 8U : 0U)];
          if (dest_kind) state.entry_origin[dest_reg] = origin;
          else state.data_origin[dest_reg] = origin;
        }
      }
      if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_LINK || instruction.mnemonic_id == M68K_ASM_MNEMONIC_UNLK)
        state.stack_entry_stable = 0U;
      for (uint8_t operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U;
           ++operand_index) {
        uint8_t written_reg = 0U;
        if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
            operand_address_register_index_local(&instruction.operands[operand_index], &written_reg) && written_reg == 7U)
          state.stack_entry_stable = 0U;
      }
      if (has_stack_transfer) {
        int frame_result = local_callee_stack_transfer(&inputs, &state, &stack_transfer, before_origins);
        if (frame_result == -2) goto resource_limit;
        if (frame_result < 0) goto cleanup;
      } else {
        state.preserved_mask &= (uint8_t)~typed_flow_instruction_written_unsaved_address_mask(&instruction,
          requested_mask, state.saved_mask);
        if (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_RETURN &&
            instruction_may_update_stack_pointer_from_metadata(&instruction)) {
          int32_t delta;
          uint8_t discarded;
          if (!instruction_stack_delta_for_comment(&instruction, &delta)) goto cleanup;
          if (delta > 0) {
            state.frame_id = local_callee_frame_intern(&inputs, state.frame_id, (uint32_t)delta, 0xffU);
            if (!state.frame_id) goto resource_limit;
          } else if (delta < 0) {
            int frame_result = local_callee_frame_pop(&inputs, &state.frame_id, (uint32_t)-(int64_t)delta, &discarded);
            if (frame_result == -2) goto resource_limit;
            if (frame_result < 0) goto cleanup;
          } else goto cleanup;
          local_callee_frame_saved_mask(&inputs, &state);
        }
        for (size_t operand_index = 0U; state.frame_id && operand_index < instruction.operand_count; ++operand_index) {
          int16_t displacement;
          uint8_t width = 0U;
          if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_WRITE) {
            const M68kOperandIR *operand = &instruction.operands[operand_index];
            if (operand_is_stack_displacement_local(operand, &displacement)) {
              (void)platform_operand_memory_span(&instruction, operand_index, NULL, NULL, &width);
              if (local_callee_frame_write(&inputs, &state, displacement, width) != 0) goto resource_limit;
            } else if ((operand->kind == M68K_ASM_OPERAND_EA || operand->kind == M68K_ASM_OPERAND_BF_EA) &&
                operand->value.ea_mode >= 2U && operand->value.ea_mode <= 6U &&
                operand->value.ea_reg == 7U) {
              if (local_callee_frame_write(&inputs, &state, 0, 0U) != 0) goto resource_limit;
            }
          }
        }
      }
      /* Every admitted SP update is represented by this owned frame. A
       * balanced frame restores entry A7 independently of instruction form. */
      if (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_RETURN) {
        state.entry_origin[7] = state.frame_id ? 0xffU : 7U;
        if (!state.frame_id) state.preserved_mask |= UINT8_C(0x80);
      }
      if (metadata->flow_kind != M68K_SIM_FLOW_CALL && metadata->flow_kind != M68K_SIM_FLOW_RETURN &&
          metadata->flow_kind != M68K_SIM_FLOW_JUMP) {
        M68kRenderPlatformState hardware;
        local_hardware_unpack(&hardware, &state.hardware);
        platform_state_update_after_instruction(&hardware, lookup, &instruction);
        local_hardware_pack(&state.hardware, &hardware);
      }
      if (metadata->flow_kind == M68K_SIM_FLOW_CALL) {
        size_t callee_section = 0U;
        uint32_t callee_offset = 0U;
        uint8_t live_mask = state.preserved_mask & (uint8_t)~state.saved_mask;
        int has_local_callee = typed_flow_local_call_target(lookup, candidate, &callee_section, &callee_offset);
        const M68kAnalysisFunctionSummary *callee_summary = NULL;
        if (has_local_callee) {
          callee_summary = lookup_configured_direct_function_summary(lookup, callee_section, callee_offset);
          if (callee_summary == NULL)
            callee_summary = lookup_inferred_direct_function_summary(lookup, callee_section, callee_offset);
        }
        if (callee_summary == NULL || callee_summary->effects_invalid != 0U ||
            callee_summary->memory_effect_state != M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT ||
            callee_summary->escape_effect_state != M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT ||
            callee_summary->memory_effect_count != 0U || callee_summary->escape_count != 0U) {
          memory_effects_unknown = 1U;
          escape_effects_unknown = 1U;
        }
        if (function_summary_register_effect(callee_summary,
            M68K_ANALYSIS_REGISTER_ADDRESS, 7U) != M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED) goto cleanup;
        local_hardware_apply_call(&state.hardware, callee_summary);
        local_callee_identity_call(&state, callee_summary, before_origins);
        if (live_mask != 0U) {
          uint8_t callee_preserved = 0U;
          uint8_t reg;
          if (!has_local_callee) goto cleanup;
          if (callee_summary == NULL || callee_summary->effects_invalid != 0U) goto cleanup;
          for (reg = 0U; reg < 8U; ++reg) {
            if (function_summary_register_effect(callee_summary, M68K_ANALYSIS_REGISTER_ADDRESS, reg) ==
                M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED)
              callee_preserved |= (uint8_t)(1U << reg);
          }
          state.preserved_mask = (state.preserved_mask & state.saved_mask) | callee_preserved;
        }
      }
      if (metadata->flow_kind == M68K_SIM_FLOW_RETURN) {
        if (state.frame_id != 0U) goto cleanup;
        state.preserved_mask = 0U;
        for (uint8_t reg = 0U; reg < 8U; ++reg)
          if (state.entry_origin[reg] == reg) state.preserved_mask |= (uint8_t)(1U << reg);
        if (returned == 0U) returned_hardware = state.hardware;
        else for (uint8_t kind = 0U; kind < 2U; ++kind) {
          returned_hardware.known[kind] &= state.hardware.known[kind];
          for (uint8_t reg = 0U; reg < 8U; ++reg) {
            if (returned_hardware.ids[kind][reg] != state.hardware.ids[kind][reg])
              returned_hardware.known[kind] &= ~((uint32_t)1U << reg);
          }
        }
        if (returned == 0U) returned_mask = state.preserved_mask;
        else returned_mask &= state.preserved_mask;
        if (returned == 0U) {
          memcpy(returned_origin, state.entry_origin, sizeof(returned_origin));
          memcpy(returned_data_origin, state.data_origin, sizeof(returned_data_origin));
        } else for (uint8_t reg = 0U; reg < 8U; ++reg) {
          if (returned_origin[reg] != state.entry_origin[reg]) returned_origin[reg] = 0xffU;
          if (returned_data_origin[reg] != state.data_origin[reg]) returned_data_origin[reg] = 0xffU;
        }
        returned = 1U;
        break;
      }
      if (typed_flow_first_local_control_target(lookup, section, candidate, &branch_target)) {
        if (metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
            (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U)) {
          state.offset = branch_target;
          continue;
        }
        {
          M68kTypedLocalCalleeState branch = state;
          branch.offset = branch_target;
          if (local_callee_push(&worklist, &work_count, &work_capacity, &branch) != 0) goto resource_limit;
          if (work_count > peak_pending) peak_pending = work_count;
        }
      }
      if (metadata->flow_kind == M68K_SIM_FLOW_JUMP || metadata->flow_kind == M68K_SIM_FLOW_TRAP) goto cleanup;
      if ((metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U) ||
          candidate->byte_count > section->size - state.offset) goto cleanup;
      state.offset += candidate->byte_count;
    }

  }
  if (returned == 0U) goto cleanup;
  memset(out_summary, 0, sizeof(*out_summary));
  /* An untouched entry register is not, by itself, a callable input.  Admit
   * it only when a body effect consumed it or when it is the source of a
   * distinct returned identity.  Otherwise every local helper would publish
   * eight invented ABI-pointer inputs merely because the entry state is
   * carried through its return path. */
  for (uint8_t reg = 0U; reg < 8U; ++reg) {
    uint8_t ordinal = typed_flow_entry_origin_ordinal(returned_origin[reg]);
    if (ordinal != 0xffU && returned_origin[reg] != typed_flow_entry_origin_make(M68K_ANALYSIS_REGISTER_ADDRESS, reg))
      input_origin_mask |= (uint16_t)(1U << ordinal);
    ordinal = typed_flow_entry_origin_ordinal(returned_data_origin[reg]);
    if (ordinal != 0xffU && returned_data_origin[reg] != typed_flow_entry_origin_make(M68K_ANALYSIS_REGISTER_DATA, reg))
      input_origin_mask |= (uint16_t)(1U << ordinal);
  }
  for (uint8_t ordinal = 0U; ordinal < 16U; ++ordinal) {
    M68kAnalysisFunctionSummaryInput *input;
    if ((input_origin_mask & (uint16_t)(1U << ordinal)) == 0U) continue;
    input = &out_summary->inputs[out_summary->input_count++];
    input->seed_kind = M68K_ANALYSIS_REGISTER_SEED_ABI_POINTER;
    input->location.kind = M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
    input->location.width = 4U;
    input->location.register_count = 1U;
    input->location.registers[0].register_kind = ordinal >= 8U ?
      M68K_ANALYSIS_REGISTER_DATA : M68K_ANALYSIS_REGISTER_ADDRESS;
    input->location.registers[0].register_index = ordinal & 7U;
  }
  for (uint8_t effect_index = 0U; effect_index < static_write_count; ++effect_index) {
    M68kFunctionSummaryEffectSubjectIR *subject = &static_writes[effect_index].subject;
    if (subject->kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_INPUT) {
      uint8_t compact = 0U;
      while (compact < out_summary->input_count &&
             out_summary->inputs[compact].location.registers[0].register_index != subject->input_index) ++compact;
      if (compact == out_summary->input_count) { memory_effects_unknown = 1U; break; }
      subject->input_index = compact;
    }
  }
  for (uint8_t escape_index = 0U; escape_index < escape_count; ++escape_index) {
    M68kFunctionSummaryEscapeIR *escape = &escapes[escape_index];
    uint8_t compact = 0U;
    uint8_t source_origin = escape->source_location.registers[0].register_index;
    while (compact < out_summary->input_count &&
           out_summary->inputs[compact].location.registers[0].register_index != source_origin) ++compact;
    if (compact == out_summary->input_count) { escape_effects_unknown = 1U; break; }
    if (escape->sink_subject.kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_INPUT) {
      uint8_t sink_origin = escape->sink_subject.input_index;
      compact = 0U;
      while (compact < out_summary->input_count &&
             out_summary->inputs[compact].location.registers[0].register_index != sink_origin) ++compact;
      if (compact == out_summary->input_count) { escape_effects_unknown = 1U; break; }
      escape->sink_subject.input_index = compact;
    }
  }
  for (uint8_t reg = 0U; reg < 8U; ++reg) {
    uint8_t input_index = 0U;
    uint8_t origin_kind = 0U, origin_reg = 0U;
    if (!typed_flow_entry_origin_decode(returned_origin[reg], &origin_kind, &origin_reg) ||
        returned_origin[reg] == typed_flow_entry_origin_make(M68K_ANALYSIS_REGISTER_ADDRESS, reg)) continue;
    while (input_index < out_summary->input_count &&
           (out_summary->inputs[input_index].location.registers[0].register_kind != origin_kind ||
            out_summary->inputs[input_index].location.registers[0].register_index != origin_reg)) ++input_index;
    if (input_index == out_summary->input_count || out_summary->result_count >= M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_LIMIT)
      continue;
    out_summary->results[out_summary->result_count].kind = M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_IDENTITY_INPUT;
    out_summary->results[out_summary->result_count].input_index = input_index;
    out_summary->results[out_summary->result_count].location.kind = M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
    out_summary->results[out_summary->result_count].location.width = 4U;
    out_summary->results[out_summary->result_count].location.register_count = 1U;
    out_summary->results[out_summary->result_count].location.registers[0].register_kind = M68K_ANALYSIS_REGISTER_ADDRESS;
    out_summary->results[out_summary->result_count++].location.registers[0].register_index = reg;
  }
  for (uint8_t reg = 0U; reg < 8U; ++reg) {
    uint8_t input_index = 0U;
    uint8_t origin_kind = 0U, origin_reg = 0U;
    if (!typed_flow_entry_origin_decode(returned_data_origin[reg], &origin_kind, &origin_reg) ||
        returned_data_origin[reg] == typed_flow_entry_origin_make(M68K_ANALYSIS_REGISTER_DATA, reg)) continue;
    while (input_index < out_summary->input_count &&
           (out_summary->inputs[input_index].location.registers[0].register_kind != origin_kind ||
            out_summary->inputs[input_index].location.registers[0].register_index != origin_reg)) ++input_index;
    if (input_index == out_summary->input_count || out_summary->result_count >= M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_LIMIT)
      continue;
    out_summary->results[out_summary->result_count].kind = M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_IDENTITY_INPUT;
    out_summary->results[out_summary->result_count].input_index = input_index;
    out_summary->results[out_summary->result_count].location.kind = M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
    out_summary->results[out_summary->result_count].location.width = 4U;
    out_summary->results[out_summary->result_count].location.register_count = 1U;
    out_summary->results[out_summary->result_count].location.registers[0].register_kind = M68K_ANALYSIS_REGISTER_DATA;
    out_summary->results[out_summary->result_count++].location.registers[0].register_index = reg;
  }
  for (uint8_t kind = 0U; kind < 2U; ++kind) {
    for (uint8_t reg = 0U; reg < 8U; ++reg) {
      M68kAnalysisFunctionSummaryResult *result;
      if ((returned_hardware.known[kind] & ((uint32_t)1U << reg)) == 0U ||
          out_summary->result_count >= M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_LIMIT) continue;
      result = &out_summary->results[out_summary->result_count++];
      memset(result, 0, sizeof(*result));
      result->kind = M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_HARDWARE_BASE;
      result->hardware_base_id = returned_hardware.ids[kind][reg];
      result->location.kind = M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
      result->location.width = 4U;
      result->location.register_count = 1U;
      result->location.registers[0].register_kind =
        kind == 0U ? M68K_ANALYSIS_REGISTER_DATA : M68K_ANALYSIS_REGISTER_ADDRESS;
      result->location.registers[0].register_index = reg;
    }
  }
  {
    uint8_t preserved_data = 0U;
    for (uint8_t reg = 0U; reg < 8U; ++reg)
      if (returned_data_origin[reg] == typed_flow_entry_origin_make(M68K_ANALYSIS_REGISTER_DATA, reg))
        preserved_data |= (uint8_t)(1U << reg);
    function_summary_set_register_partition(out_summary, preserved_data, returned_mask);
  }
  if (memory_effects_unknown == 0U) {
    memcpy(out_summary->memory_effects, static_writes, sizeof(static_writes));
    out_summary->memory_effect_count = static_write_count;
  } else {
    out_summary->memory_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_UNKNOWN;
    out_summary->memory_effect_count = 0U;
  }
  /* A complete traversal with no caller-visible write and only complete empty
   * nested contracts proves an empty escape partition. Any source that has no
   * durable ABI identity remains unknown, never silently empty. */
  if (escape_effects_unknown != 0U) {
    out_summary->escape_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_UNKNOWN;
    out_summary->escape_count = 0U;
  } else {
    memcpy(out_summary->escapes, escapes, sizeof(escapes));
    out_summary->escape_count = escape_count;
  }
  result = 1;
  goto cleanup;
resource_limit:
  if (out_limit_hit != NULL) *out_limit_hit = 1U;
cleanup:
  {
    const char *trace = getenv("AMIGA_REVERSING_DIRECT_BODY_TRACE");
    if (trace != NULL && (strcmp(trace, "*") == 0 || strtoul(trace, NULL, 0) == target_offset))
      fprintf(stderr, "direct-body section=%zu entry=%X result=%d pcs=%zu transfers=%zu peak_pending=%zu frame_conflict=%d state_bytes=%zu\n",
        section_index, target_offset, result, inputs.count, inputs.transfers, peak_pending, frame_conflict,
        inputs.capacity * sizeof(*inputs.states) + inputs.index_capacity * sizeof(*inputs.index) +
        work_capacity * sizeof(*worklist) + inputs.frame_capacity * sizeof(*inputs.frames) +
        inputs.frame_index_capacity * sizeof(*inputs.frame_index) +
        inputs.frame_scratch_capacity * sizeof(*inputs.frame_scratch));
  }
  free(worklist); free(inputs.states); free(inputs.index);
  free(inputs.frames); free(inputs.frame_index); free(inputs.frame_scratch);
  return result;
}

static const M68kAnalysisFunctionSummary *lookup_inferred_direct_function_summary(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t entry_offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->inferred_function_summary_count; ++index) {
    const M68kAnalysisFunctionSummary *summary = &lookup->inferred_function_summaries[index].summary;
    if (summary->has_section_index != 0U &&
        summary->callable_kind == M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT &&
        summary->section_index == section_index && summary->entry_offset == entry_offset) return summary;
  }
  return NULL;
}

static size_t lookup_inferred_direct_function_summary_index(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t entry_offset) {
  size_t index;
  if (lookup == NULL) return SIZE_MAX;
  for (index = 0U; index < lookup->inferred_function_summary_count; ++index) {
    const M68kAnalysisFunctionSummary *summary = &lookup->inferred_function_summaries[index].summary;
    if (summary->has_section_index != 0U &&
        summary->callable_kind == M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT &&
        summary->section_index == section_index && summary->entry_offset == entry_offset) return index;
  }
  return SIZE_MAX;
}

static const M68kPlatformCallThunkIR *lookup_platform_call_thunk(const M68kRenderLookup *lookup,
    size_t wrapper_section_index, uint32_t wrapper_entry_offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->platform_call_thunk_count; ++index) {
    const M68kPlatformCallThunkIR *thunk = &lookup->platform_call_thunks[index];
    if (thunk->wrapper_section_index == wrapper_section_index &&
        thunk->wrapper_entry_offset == wrapper_entry_offset) return thunk;
  }
  return NULL;
}

/* Accept a wrapper only when one concrete platform dispatch is followed solely
 * by ordinary wrapper cleanup and return. This produces durable evidence for
 * composition without treating a rendered local-helper name as an identity. */
static const AmigaOsLibraryVectorInfo *discover_direct_platform_thunk_at(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index, uint32_t entry_offset,
    uint32_t *out_call_offset) {
  const M68kDecodeSectionIR *section;
  M68kRenderPlatformState state;
  const AmigaOsLibraryVectorInfo *resolved = NULL;
  uint32_t cursor;
  if (out_call_offset != NULL) *out_call_offset = 0U;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || section_index >= decode->section_count) return NULL;
  section = &decode->sections[section_index];
  if (!accepted_start_at(section, accepted_start[section_index], entry_offset)) return NULL;
  memset(&state, 0, sizeof(state));
  cursor = entry_offset;
  while (cursor < section->size && cursor - entry_offset < 128U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const AmigaOsLibraryVectorInfo *vector;
    if (!accepted_start_at(section, accepted_start[section_index], cursor)) return NULL;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U || m68k_decode_candidate_to_instruction(candidate, &instruction) != 0)
      return NULL;
    attach_known_instruction_relocations(lookup, section_index, candidate, &instruction);
    platform_state_apply_policy_register_seeds(&state, lookup->policy, section_index, candidate->offset);
    if (resolved != NULL) {
      if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_RTS) return resolved;
      /* The local summary owns post-call adaptation (for example D0-to-A0
       * result aliases) and its branch effects. A second call would require
       * another callable relation and is intentionally not folded into this
       * thunk. */
      if (instruction_has_call_flow_local(&instruction)) return NULL;
      cursor += candidate->byte_count;
      continue;
    }
    vector = attach_amiga_lvo_symbol_if_known(&state, &instruction);
    if (vector == NULL) vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[section_index],
      candidate, &instruction);
    if (vector == NULL && instruction_has_call_flow_local(&instruction)) {
      /* A wrapper may adapt the result of one nested local platform thunk.
       * The direct call instruction is durable evidence for this wrapper's
       * relation; the nested resolver still requires an exact vector target. */
      vector = resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start, section_index, candidate);
    }
    if (vector != NULL) {
      if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_JMP) {
        if (out_call_offset != NULL) *out_call_offset = candidate->offset;
        return vector;
      }
      if (instruction.mnemonic_id != M68K_ASM_MNEMONIC_JSR && !instruction_has_call_flow_local(&instruction)) return NULL;
      resolved = vector;
      if (out_call_offset != NULL) *out_call_offset = candidate->offset;
    }
    if (vector == NULL && (instruction_has_call_flow_local(&instruction) ||
        candidate_has_non_call_control_target(candidate))) return NULL;
    platform_state_update_data_lvo_after_instruction(&state, &instruction);
    platform_state_update_after_instruction(&state, lookup, &instruction);
    if (candidate_terminates_a6_state(candidate)) return NULL;
    cursor += candidate->byte_count;
  }
  return NULL;
}

static int render_lookup_collect_platform_call_thunks(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  uint16_t configured_index;
  size_t inferred_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return -1;
  for (configured_index = 0U; lookup->policy != NULL && configured_index < lookup->policy->function_summary_count &&
       configured_index < M68K_ANALYSIS_FUNCTION_SUMMARY_LIMIT; ++configured_index) {
    const M68kAnalysisFunctionSummary *summary = &lookup->policy->function_summaries[configured_index];
    const AmigaOsLibraryVectorInfo *vector;
    M68kPlatformCallThunkIR thunk;
    if (summary->callable_kind != M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT || !summary->has_section_index) continue;
    memset(&thunk, 0, sizeof(thunk));
    vector = discover_direct_platform_thunk_at(lookup, decode, accepted_start, summary->section_index,
      summary->entry_offset, &thunk.wrapper_call_offset);
    if (vector == NULL) continue;
    thunk.wrapper_section_index = summary->section_index;
    thunk.wrapper_entry_offset = summary->entry_offset;
    thunk.platform_library_id = vector->library_id;
    thunk.platform_function_id = vector->function_id;
    thunk.relation_kind = M68K_PLATFORM_CALL_THUNK_RELATION_PLATFORM_CALL_THUNK;
    if (render_lookup_add_platform_call_thunk(lookup, &thunk) != 0) return -1;
  }
  for (inferred_index = 0U; inferred_index < lookup->inferred_function_summary_count; ++inferred_index) {
    const M68kAnalysisFunctionSummary *summary = &lookup->inferred_function_summaries[inferred_index].summary;
    const AmigaOsLibraryVectorInfo *vector;
    M68kPlatformCallThunkIR thunk;
    if (summary->callable_kind != M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT || !summary->has_section_index) continue;
    memset(&thunk, 0, sizeof(thunk));
    vector = discover_direct_platform_thunk_at(lookup, decode, accepted_start, summary->section_index,
      summary->entry_offset, &thunk.wrapper_call_offset);
    if (vector == NULL) continue;
    thunk.wrapper_section_index = summary->section_index;
    thunk.wrapper_entry_offset = summary->entry_offset;
    thunk.platform_library_id = vector->library_id;
    thunk.platform_function_id = vector->function_id;
    thunk.relation_kind = M68K_PLATFORM_CALL_THUNK_RELATION_PLATFORM_CALL_THUNK;
    if (render_lookup_add_platform_call_thunk(lookup, &thunk) != 0) return -1;
  }
  return 0;
}

static int render_lookup_append_inferred_direct_function_summary(M68kRenderLookup *lookup,
    size_t section_index, uint32_t entry_offset) {
  M68kRenderInferredFunctionSummary *grown;
  M68kRenderInferredFunctionSummary *record;
  size_t next_capacity;
  if (lookup == NULL || lookup_inferred_direct_function_summary(lookup, section_index, entry_offset) != NULL) return 0;
  if (lookup->inferred_function_summary_count == lookup->inferred_function_summary_capacity) {
    next_capacity = lookup->inferred_function_summary_capacity == 0U ? 16U :
      lookup->inferred_function_summary_capacity * 2U;
    grown = (M68kRenderInferredFunctionSummary *)render_lookup_grow_array(lookup,
      lookup->inferred_function_summaries, lookup->inferred_function_summary_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->inferred_function_summaries = grown;
    lookup->inferred_function_summary_capacity = next_capacity;
  }
  record = &lookup->inferred_function_summaries[lookup->inferred_function_summary_count++];
  memset(record, 0, sizeof(*record));
  record->summary.callable_kind = M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT;
  record->summary.has_section_index = 1U;
  record->summary.section_index = (uint32_t)section_index;
  record->summary.entry_offset = entry_offset;
  snprintf(record->summary.function_summary_id, sizeof(record->summary.function_summary_id),
    "inferred_local_s%u_o%08X", (unsigned)section_index, (unsigned)entry_offset);
  /* The graph solver owns body inference after every direct target has a
   * stable node. Start from the conservative clobbering boundary: until a
   * callee body proves a location survives, recursive edges cannot invent a
   * caller-visible value. A later SCC layer may refine this only with a
   * converged component proof. */
  function_summary_set_register_partition(&record->summary, 0U, 0U);
  record->summary.memory_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_UNKNOWN;
  record->summary.escape_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_UNKNOWN;
  return 0;
}

static int render_lookup_collect_inferred_direct_function_summaries(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return -1;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      size_t target_section_index;
      uint32_t target_offset;
      M68kFunctionSummaryUseIR use;
      if (candidate->offset >= section->size || accepted_start[section_index] == NULL ||
          accepted_start[section_index][candidate->offset] == 0U ||
          !typed_flow_local_call_target(lookup, candidate, &target_section_index, &target_offset)) continue;
      if (lookup_configured_direct_function_summary(lookup, target_section_index, target_offset) == NULL) {
        if (render_lookup_append_inferred_direct_function_summary(lookup,
              target_section_index, target_offset) != 0) return -1;
      }
      memset(&use, 0, sizeof(use));
      snprintf(use.function_summary_id, sizeof(use.function_summary_id), "inferred_local_s%u_o%08X",
        (unsigned)target_section_index, (unsigned)target_offset);
      use.caller_section_index = (uint32_t)section_index;
      use.caller_offset = candidate->offset;
      use.kind = M68K_FUNCTION_SUMMARY_USE_CALL;
      if (render_lookup_add_function_summary_use(lookup, &use) != 0) return -1;
    }
  }
  return 0;
}

static int typed_flow_successors_for_candidate(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const size_t *node_by_offset, uint32_t node_by_offset_count, const M68kDecodeCandidate *candidate,
    size_t *out_successors, size_t successor_capacity);

#include "m68k_direct_call_graph.inc"

static int render_lookup_solve_inferred_direct_function_summaries(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return -1;
  return direct_call_graph_prove(lookup, decode, accepted_start);
}

/* Resolve the callback table backing an indirect dispatch from the common
 * typed value/origin state.  Direct table-EA dispatch has no synthetic
 * register destination and follows this same query. */
static int typed_flow_callback_table_identity(const M68kRenderTypedState *state,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, const M68kRenderTypedStoredValue *direct_value,
    size_t *out_table_section_index, uint32_t *out_table_offset) {
  uint8_t dispatch_reg;
  if (out_table_section_index != NULL) *out_table_section_index = 0U;
  if (out_table_offset != NULL) *out_table_offset = 0U;
  if (state == NULL || section == NULL || candidate == NULL || instruction == NULL ||
      out_table_section_index == NULL || out_table_offset == NULL || instruction->operand_count != 1U) {
    return 0;
  }
  if (direct_value != NULL && direct_value->table_origin.has_origin != 0U &&
      direct_value->table_origin.selection_kind != M68K_ADDRESS_VALUE_TABLE_SELECTION_TERMINAL) {
    *out_table_section_index = direct_value->table_origin.table_section_index;
    *out_table_offset = direct_value->table_origin.table_start_offset;
    return 1;
  }
  if (!operand_is_address_memory_local(&instruction->operands[0], &dispatch_reg, NULL) || dispatch_reg >= 8U) return 0;
  if (state->addr_regs[dispatch_reg].table_origin.has_origin != 0U &&
      state->addr_regs[dispatch_reg].table_origin.selection_kind != M68K_ADDRESS_VALUE_TABLE_SELECTION_TERMINAL) {
    *out_table_section_index = state->addr_regs[dispatch_reg].table_origin.table_section_index;
    *out_table_offset = state->addr_regs[dispatch_reg].table_origin.table_start_offset;
    return 1;
  }
  return 0;
}

/* Callback-table facts are owned by the table, not by an individual indirect
 * call.  The collector below runs after flow convergence and intersects the
 * complete-domain facts for every declared entry. */
static const M68kAnalysisFunctionSummary *lookup_inferred_callback_table_function_summary(
    const M68kRenderLookup *lookup, size_t section_index, uint32_t table_offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->inferred_function_summary_count; ++index) {
    const M68kAnalysisFunctionSummary *summary = &lookup->inferred_function_summaries[index].summary;
    if (summary->has_section_index != 0U &&
        summary->callable_kind == M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_CALLBACK_TABLE &&
        summary->section_index == section_index && summary->table_offset == table_offset) return summary;
  }
  return NULL;
}

/* Keep only stable table coordinates while flow converges.  Appending a
 * summary or reverse use here would make source-analysis ownership depend on
 * CFG worklist order. */
static int render_lookup_record_observed_callback_table(M68kRenderLookup *lookup,
    size_t section_index, uint32_t table_offset) {
  M68kRenderObservedCallbackTable *grown;
  size_t index;
  size_t next_capacity;
  if (lookup != NULL && lookup->affine_entry_context != NULL) return 0;
  if (lookup == NULL) return -1;
  for (index = 0U; index < lookup->observed_callback_table_count; ++index) {
    const M68kRenderObservedCallbackTable *observed = &lookup->observed_callback_tables[index];
    if (observed->section_index == section_index && observed->table_offset == table_offset) return 0;
  }
  if (lookup->observed_callback_table_count == lookup->observed_callback_table_capacity) {
    next_capacity = lookup->observed_callback_table_capacity == 0U ? 8U :
      lookup->observed_callback_table_capacity * 2U;
    grown = (M68kRenderObservedCallbackTable *)render_lookup_grow_array(lookup,
      lookup->observed_callback_tables, lookup->observed_callback_table_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->observed_callback_tables = grown;
    lookup->observed_callback_table_capacity = next_capacity;
  }
  lookup->observed_callback_tables[lookup->observed_callback_table_count].section_index = section_index;
  lookup->observed_callback_tables[lookup->observed_callback_table_count].table_offset = table_offset;
  lookup->observed_callback_table_count += 1U;
  return 0;
}

static int render_lookup_append_inferred_callback_table_function_summary(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, const M68kAnalysisFunctionSummary *declared) {
  M68kRenderInferredFunctionSummary *grown;
  M68kRenderInferredFunctionSummary *record;
  const M68kSection *table_section;
  size_t next_capacity;
  uint32_t entry_index;
  uint8_t preserved_mask = 0xffU;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || declared == NULL || !declared->has_section_index ||
      declared->callable_kind != M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_CALLBACK_TABLE ||
      declared->section_index >= lookup->object->section_count || declared->entry_count == 0U) return -1;
  if (lookup_inferred_callback_table_function_summary(lookup, declared->section_index, declared->table_offset) != NULL)
    return 0;
  if (lookup->inferred_function_summary_count == lookup->inferred_function_summary_capacity) {
    next_capacity = lookup->inferred_function_summary_capacity == 0U ? 16U :
      lookup->inferred_function_summary_capacity * 2U;
    grown = (M68kRenderInferredFunctionSummary *)render_lookup_grow_array(lookup,
      lookup->inferred_function_summaries, lookup->inferred_function_summary_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->inferred_function_summaries = grown;
    lookup->inferred_function_summary_capacity = next_capacity;
  }
  record = &lookup->inferred_function_summaries[lookup->inferred_function_summary_count++];
  memset(record, 0, sizeof(*record));
  record->summary.callable_kind = M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_CALLBACK_TABLE;
  record->summary.has_section_index = 1U;
  record->summary.section_index = declared->section_index;
  record->summary.table_offset = declared->table_offset;
  record->summary.entry_count = declared->entry_count;
  record->summary.input_count = declared->input_count;
  record->summary.result_count = declared->result_count;
  record->summary.result_contract_invalid = declared->result_contract_invalid;
  memcpy(record->summary.inputs, declared->inputs, sizeof(record->summary.inputs));
  memcpy(record->summary.results, declared->results, sizeof(record->summary.results));
  /* The table contract owns its declared memory and escape relations.  The
   * entries determine only the register partition below; dropping these
   * components would turn a valid callback write into a false preservation
   * proof on the second typed-flow pass. */
  record->summary.memory_effect_state = declared->memory_effect_state;
  record->summary.escape_effect_state = declared->escape_effect_state;
  record->summary.memory_effect_count = declared->memory_effect_count;
  record->summary.escape_count = declared->escape_count;
  memcpy(record->summary.memory_effects, declared->memory_effects,
    sizeof(record->summary.memory_effects));
  memcpy(record->summary.escapes, declared->escapes, sizeof(record->summary.escapes));
  snprintf(record->summary.function_summary_id, sizeof(record->summary.function_summary_id),
    "inferred_callback_s%u_o%08X_n%u", (unsigned)declared->section_index,
    (unsigned)declared->table_offset, (unsigned)declared->entry_count);
  table_section = &lookup->object->sections[declared->section_index];
  if (table_section->data == NULL || declared->table_offset > table_section->size ||
      declared->entry_count > (table_section->size - declared->table_offset) / 4U) goto invalid;
  for (entry_index = 0U; entry_index < declared->entry_count; ++entry_index) {
    size_t target_section_index = 0U;
    uint32_t target_offset = 0U;
    const M68kAnalysisFunctionSummary *target;
    uint8_t reg;
    uint32_t value = m68k_read_u32be(table_section->data + declared->table_offset + entry_index * 4U);
    if (!render_lookup_pointer_value_to_object_source_location(lookup, value, &target_section_index, &target_offset)) {
      record->terminal_reason = M68K_FUNCTION_SUMMARY_TERMINAL_CALLBACK_ENTRY_UNRESOLVED;
      goto invalid;
    }
    if (lookup_configured_direct_function_summary(lookup, target_section_index, target_offset) == NULL &&
        render_lookup_append_inferred_direct_function_summary(lookup,
          target_section_index, target_offset) != 0) {
      record->terminal_reason = M68K_FUNCTION_SUMMARY_TERMINAL_CALLBACK_ENTRY_INCOMPATIBLE;
      goto invalid;
    }
    if (render_lookup_solve_inferred_direct_function_summaries(lookup, decode, accepted_start) != 0) {
      record->terminal_reason = M68K_FUNCTION_SUMMARY_TERMINAL_CALLBACK_ENTRY_INCOMPATIBLE;
      goto invalid;
    }
    target = lookup_inferred_direct_function_summary(lookup, target_section_index, target_offset);
    if (target == NULL || target->effects_invalid != 0U)
      target = lookup_configured_direct_function_summary(lookup, target_section_index, target_offset);
    if (target == NULL || target->effects_invalid != 0U) {
      record->terminal_reason = M68K_FUNCTION_SUMMARY_TERMINAL_CALLBACK_ENTRY_INCOMPATIBLE;
      goto invalid;
    }
    for (reg = 0U; reg < 8U; ++reg) {
      if (function_summary_register_effect(target, M68K_ANALYSIS_REGISTER_ADDRESS, reg) !=
          M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED) preserved_mask &= (uint8_t)~(1U << reg);
    }
  }
  function_summary_set_register_partition(&record->summary, 0U, preserved_mask);
  /* `function_summary_set_register_partition` is also used by the generated
   * platform and local-body writers, where an empty explicit memory/escape
   * partition is intentional.  Here the table interface owns those two
   * components.  Restore their exact declared terminal state after deriving
   * only the register intersection: an unknown callback memory/escape
   * contract must stay unknown and force the common call transfer to clear
   * typed state, rather than becoming an empty explicit partition. */
  record->summary.memory_effect_state = declared->memory_effect_state;
  record->summary.escape_effect_state = declared->escape_effect_state;
  return 0;
invalid:
  record->summary.effects_invalid = 1U;
  record->summary.register_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_INVALID;
  record->summary.memory_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_INVALID;
  record->summary.escape_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_INVALID;
  return 0;
}

static int render_lookup_collect_inferred_callback_table_function_summaries(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  size_t observed_index;
  if (lookup == NULL || lookup->policy == NULL) return 0;
  for (observed_index = 0U; observed_index < lookup->observed_callback_table_count; ++observed_index) {
    const M68kRenderObservedCallbackTable *observed = &lookup->observed_callback_tables[observed_index];
    uint16_t summary_index;
    for (summary_index = 0U; summary_index < lookup->policy->function_summary_count &&
         summary_index < M68K_ANALYSIS_FUNCTION_SUMMARY_LIMIT; ++summary_index) {
      const M68kAnalysisFunctionSummary *declared = &lookup->policy->function_summaries[summary_index];
      if (!declared->has_section_index ||
          declared->callable_kind != M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_CALLBACK_TABLE ||
          declared->section_index != observed->section_index || declared->table_offset != observed->table_offset) continue;
      if (render_lookup_append_inferred_callback_table_function_summary(lookup, decode, accepted_start, declared) != 0)
        return -1;
      break;
    }
  }
  return 0;
}

/* Affine entry identity is an orthogonal shared value component. MOVE,
 * storage, stack and callable paths transport it with the existing packet;
 * only the arithmetic offset operations need this component-specific rule. */
static void affine_entry_transfer_after(M68kRenderTypedState *state, const M68kRenderLookup *lookup,
    const M68kInstructionIR *instruction, const uint32_t before[16],
    const M68kStackRegisterTransfer *stack, int has_stack) {
  M68kAffineEntryContext *context = lookup ? lookup->affine_entry_context : NULL;
  const M68kSimFormMetadata *metadata;
  uint8_t address, reg;
  int64_t delta;
  if (!context || !(metadata = m68k_sim_metadata_for_instruction(instruction))) return;
  if (instruction->operand_count == 2U &&
      m68k_instruction_operand_direct_register(&instruction->operands[1], &address, &reg) && reg < 8U) {
    const M68kAffineEntryValue *input = affine_entry_value(context, before[reg + (address ? 8U : 0U)]);
    if (input && (instruction->size_suffix == 'l' ||
        (instruction->size_suffix == 'w' && (address || input->width == 2U))) &&
        typed_app_cursor_immediate_delta(instruction, &delta)) {
      uint32_t id = affine_entry_adjust(context, before[reg + (address ? 8U : 0U)], delta);
      if (address) state->addr_regs[reg].entry_value_id = id;
      else state->data_regs[reg].entry_value_id = id;
    }
    if (metadata->operation_class == M68K_SIM_CLASS_LOAD_EFFECTIVE_ADDRESS && address) {
      uint8_t base;
      int16_t displacement;
      if (operand_is_address_memory_local(&instruction->operands[0], &base, &displacement)) {
        input = affine_entry_value(context, before[base + 8U]);
        if (input && input->width == 4U)
          state->addr_regs[reg].entry_value_id = affine_entry_adjust(context, before[base + 8U], displacement);
      }
    }
  }
  for (size_t i = 0U; i < instruction->operand_count; ++i) {
    const M68kOperandIR *operand = &instruction->operands[i];
    uint8_t shape = m68k_instruction_operand_decoded_ea_shape(operand), span = 0U;
    uint8_t explicit_address = 0U, explicit_reg = 0U, updates = 0U;
    if (shape != M68K_SIM_EA_SHAPE_POSTINCREMENT && shape != M68K_SIM_EA_SHAPE_PREDECREMENT) continue;
    reg = operand->kind == M68K_ASM_OPERAND_PREDEC || operand->kind == M68K_ASM_OPERAND_POSTINC
      ? operand->value.reg : operand->value.ea_reg;
    if (reg >= 7U) continue; /* A7 has its normalized stack rule below. */
    for (size_t j = 0U; j < instruction->operand_count; ++j) {
      const M68kOperandIR *other = &instruction->operands[j];
      uint8_t other_shape = m68k_instruction_operand_decoded_ea_shape(other);
      if ((other_shape == M68K_SIM_EA_SHAPE_POSTINCREMENT || other_shape == M68K_SIM_EA_SHAPE_PREDECREMENT) &&
          ((other->kind == M68K_ASM_OPERAND_PREDEC || other->kind == M68K_ASM_OPERAND_POSTINC)
            ? other->value.reg : other->value.ea_reg) == reg) ++updates;
      if (j != i && instruction_operand_writes_register_from_metadata(instruction, j) &&
          m68k_instruction_operand_direct_register(other, &explicit_address, &explicit_reg) &&
          explicit_address && explicit_reg == reg) updates = 2U;
    }
    const M68kAffineEntryValue *input = affine_entry_value(context, before[reg + 8U]);
    state->addr_regs[reg].entry_value_id = 0U;
    if (updates == 1U && input && input->width == 4U &&
        platform_operand_memory_span(instruction, i, NULL, NULL, &span))
      state->addr_regs[reg].entry_value_id = affine_entry_adjust(context, before[reg + 8U],
        shape == M68K_SIM_EA_SHAPE_PREDECREMENT ? -(int64_t)span : span);
  }
  if (metadata->flow_kind != M68K_SIM_FLOW_CALL && instruction_may_update_stack_pointer_from_metadata(instruction)) {
    int32_t stack_delta;
    state->addr_regs[7].entry_value_id = 0U;
    if (has_stack) {
      stack_delta = (int32_t)stack->width * stack->count;
      if (stack->direction == M68K_STACK_TRANSFER_POP) stack_delta = -stack_delta;
      state->addr_regs[7].entry_value_id = affine_entry_adjust(context, before[15], -(int64_t)stack_delta);
    } else if (instruction_stack_delta_for_comment(instruction, &stack_delta)) {
      state->addr_regs[7].entry_value_id = affine_entry_adjust(context, before[15], -(int64_t)stack_delta);
    }
  }
}

static void typed_state_update_after_instruction(M68kRenderTypedState *state, M68kRenderLookup *lookup,
    const M68kRenderPlatformState *platform_state, size_t section_index, const M68kInstructionIR *instruction,
    const M68kDecodeCandidate *candidate, const M68kAnalysisFunctionSummary *local_effects, uint32_t offset,
    int record_table_load_consumers) {
  const M68kSimFormMetadata *move_metadata = NULL;
  const M68kSimFormMetadata *metadata;
  const AmigaOsCallOutputInfo *source_output = NULL;
  uint16_t source_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  M68kRenderTypedStorageOrigin source_origin;
  M68kRenderTypedProvenance source_provenance;
  M68kRenderTypedMemoryBaseValue source_memory_base;
  size_t operand_index, source_index = 0U, dest_index = 0U;
  uint8_t dest_reg = 0U, bit;
  uint8_t source_addr_reg = 0U;
  uint8_t source_data_reg = 0U;
  uint8_t table_load_dest_reg = 0U;
  uint16_t source_array_element_count = 0U;
  uint16_t source_array_element_index = 0U;
  int32_t source_byte_cursor = 0;
  uint32_t immediate_value = 0U;
  int16_t source_app_displacement = 0;
  uint8_t source_app_base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
  int source_is_app_address = 0;
  int source_has_memory_base = 0;
  int recognized_stack_update = 0;
  uint8_t app_update_reg = 0U, app_update_width = 0U;
  M68kRenderTypedAppAddressValue app_after_update = {0};
  M68kStackRegisterTransfer stack_transfer = {0};
  int has_stack_transfer;
  uint32_t entry_values_before[16] = {0};
  uint8_t alias_roots_before[8];
  if (state == NULL || instruction == NULL) return;
  typed_addr_alias_roots(state, alias_roots_before);
  if (lookup != NULL && lookup->affine_entry_context != NULL) for (uint8_t reg = 0U; reg < 8U; ++reg) {
    entry_values_before[reg] = state->data_regs[reg].entry_value_id;
    entry_values_before[reg + 8U] = state->addr_regs[reg].entry_value_id;
  }
  has_stack_transfer = platform_instruction_stack_register_transfer(instruction, &stack_transfer);
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    uint8_t access, element_width, count;
    int16_t displacement;
    if (m68k_instruction_operand_decoded_ea_shape(operand) != M68K_SIM_EA_SHAPE_POSTINCREMENT ||
        !typed_app_memory_span(lookup, state, instruction, operand_index, &app_update_reg,
          &displacement, &access, &app_update_width, &element_width, &count)) continue;
    if ((int32_t)state->app_addr_regs[app_update_reg].displacement + app_update_width <= INT16_MAX) {
      app_after_update = state->app_addr_regs[app_update_reg];
      app_after_update.displacement = (int16_t)(app_after_update.displacement + app_update_width);
    }
  }
  typed_origin_clear(&source_origin);
  typed_provenance_clear(&source_provenance);
  typed_memory_base_clear(&source_memory_base);
  if (instruction_has_call_flow_local(instruction)) {
    if (local_effects != NULL) {
      uint8_t preserved_reg;
      typed_state_apply_function_summary_effects(state, local_effects);
      /* A locally proven preserved register is a real value-flow edge across
       * this call.  Source and destination are the same physical register;
       * the call instruction offset identifies the contract boundary. */
      for (preserved_reg = 0U; preserved_reg < 8U; ++preserved_reg) {
        if (function_summary_register_effect(local_effects, M68K_ANALYSIS_REGISTER_ADDRESS, preserved_reg) !=
            M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED) continue;
        typed_provenance_append_transfer(&state->addr_regs[preserved_reg].provenance, section_index, offset,
          preserved_reg, preserved_reg);
      }
    }
    else {
      /* An unresolved direct/indirect call has no preservation contract.
       * Keeping register-held source identities here would turn an unknown
       * callee into an unsound affine transfer. */
      typed_state_apply_function_summary_effects(state, NULL);
    }
  } else if (has_stack_transfer && stack_transfer.multiple && stack_transfer.width == 4U &&
      stack_transfer.direction == M68K_STACK_TRANSFER_PUSH) {
    uint32_t mask = stack_transfer.register_mask;
    int16_t displacement = 0;
    for (bit = 0U; bit < 16U; ++bit) if ((mask & (1UL << bit)) != 0U) ++displacement;
    typed_state_rebase_stack_slots(state, (int16_t)(displacement * 4));
    recognized_stack_update = 1;
    displacement = 0;
    for (bit = 0U; bit < 16U; ++bit) {
      M68kRenderTypedStoredValue saved;
      uint8_t reg = (uint8_t)(bit & 7U);
      if ((mask & (1UL << bit)) == 0U) continue;
      {
        M68kOperandIR operand = {0};
        operand.kind = bit >= 8U ? M68K_ASM_OPERAND_AN : M68K_ASM_OPERAND_DN;
        operand.value.reg = reg;
        saved = typed_stored_value_for_operand(state, &operand);
        typed_state_set_stack_slot(state, displacement, 1U, M68K_FUNCTION_SUMMARY_ABI_STACK_NONE,
          &saved, bit >= 8U ? &state->memory_base_regs[reg] : &state->data_memory_base_regs[reg]);
      }
      displacement = (int16_t)(displacement + 4);
    }
  } else if (has_stack_transfer && stack_transfer.multiple && stack_transfer.width == 4U &&
      stack_transfer.direction == M68K_STACK_TRANSFER_POP) {
    uint32_t mask = stack_transfer.register_mask;
    int16_t displacement = 0;
    for (bit = 0U; bit < 16U; ++bit) {
      const M68kRenderTypedStoredValue *saved;
      const M68kRenderTypedMemoryBaseValue *memory_base;
      uint8_t reg = (uint8_t)(bit & 7U);
      if ((mask & (1UL << bit)) == 0U) continue;
      saved = typed_state_stack_slot_value(state, displacement);
      memory_base = typed_state_stack_slot_memory_base(state, displacement);
      typed_state_restore_stored_register(state, bit >= 8U ? M68K_ANALYSIS_REGISTER_ADDRESS :
        M68K_ANALYSIS_REGISTER_DATA, reg, saved, memory_base);
      displacement = (int16_t)(displacement + 4);
    }
    typed_state_rebase_stack_slots(state, (int16_t)-displacement);
    recognized_stack_update = 1;
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    for (bit = 0U; bit < 8U; ++bit) {
      if ((instruction->operands[1].value.value & (1UL << bit)) != 0U) typed_state_clear_reg(state, 1U, bit);
      if ((instruction->operands[1].value.value & (1UL << (8U + bit))) != 0U) typed_state_clear_reg(state, 2U, bit);
    }
  } else if (instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index,
      &move_metadata)) {
    M68kRenderTypedStoredValue stored_value;
    M68kRenderTypedStoredValue table_value;
    const M68kOperandIR *source_operand = &instruction->operands[source_index];
    const M68kOperandIR *dest_operand = &instruction->operands[dest_index];
    typed_stored_value_clear(&stored_value);
    typed_stored_value_clear(&table_value);
    if (instruction->size_suffix == 'l' && m68k_ir_operand_immediate_value(source_operand, &immediate_value)) {
      typed_stored_value_set_raw_long(&stored_value, immediate_value);
      stored_value.provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_IMMEDIATE,
        section_index, offset);
      stored_value.provenance.producer_operand_index = (uint8_t)source_index;
    } else {
      stored_value = typed_stored_value_for_operand(state, source_operand);
    }
    source_output = typed_state_output_for_operand(state, source_operand, NULL, NULL);
    source_struct_id = typed_state_struct_id_for_operand(state, source_operand);
    if (operand_address_register_index_local(source_operand, &source_addr_reg) && source_addr_reg < 8U &&
        state->addr_regs[source_addr_reg].known) {
      source_array_element_count = state->addr_regs[source_addr_reg].array_element_count;
      source_array_element_index = state->addr_regs[source_addr_reg].array_element_index;
      source_byte_cursor = state->addr_regs[source_addr_reg].byte_cursor;
    } else if (operand_is_data_register_local(source_operand, &source_data_reg) && source_data_reg < 8U &&
               state->data_regs[source_data_reg].known) {
      source_array_element_count = state->data_regs[source_data_reg].array_element_count;
      source_array_element_index = state->data_regs[source_data_reg].array_element_index;
      source_byte_cursor = state->data_regs[source_data_reg].byte_cursor;
    }
    source_is_app_address = typed_state_copy_app_address(state, source_operand, &source_app_displacement, &source_app_base_evidence_kind);
    source_has_memory_base = typed_state_copy_memory_base(state, source_operand, &source_memory_base);
    if (!source_has_memory_base && candidate != NULL && move_metadata != NULL && instruction->size_suffix == 'l' &&
        move_metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ) {
      size_t data_target_section = 0U;
      uint32_t data_target_offset = 0U;
      if (candidate_data_target_for_operand(candidate, (uint32_t)source_index, &data_target_section,
          &data_target_offset)) {
        source_memory_base.known = 1U;
        source_memory_base.section_index = data_target_section;
        source_memory_base.offset = data_target_offset;
        typed_memory_base_bind_pointer_table(&source_memory_base, lookup);
        source_has_memory_base = 1;
      } else {
        const M68kFact *relocation = analysis_operand_relocation_ref(lookup, section_index, candidate, source_index);
        if (relocation != NULL && relocation->target_section_index < lookup->section_count) {
          source_memory_base.known = 1U;
          source_memory_base.section_index = relocation->target_section_index;
          source_memory_base.offset = relocation->target_offset;
          typed_memory_base_bind_pointer_table(&source_memory_base, lookup);
          source_has_memory_base = 1;
        }
      }
    }
    if (!source_has_memory_base && move_metadata != NULL && instruction->size_suffix == 'l' &&
        move_metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ) {
      source_has_memory_base = typed_memory_base_bind_runtime_pointer_table_slot(&source_memory_base, lookup,
        platform_state, source_operand);
    }
    if (!source_has_memory_base && operand_is_postinc_a7_local(source_operand)) {
      const M68kRenderTypedMemoryBaseValue *stack_memory_base = typed_state_stack_slot_memory_base(state, 0);
      if (stack_memory_base != NULL) {
        source_memory_base = *stack_memory_base;
        source_has_memory_base = 1;
      }
    }
    (void)typed_state_origin_for_operand(state, source_operand, &source_origin);
    source_provenance = typed_stored_value_for_operand(state, source_operand).provenance;
    if (stored_value.provenance.kind == M68K_PLATFORM_TYPE_PROVENANCE_IMMEDIATE)
      source_provenance = stored_value.provenance;
    if (source_struct_id == AMIGA_OS_STRUCT_ID_NONE && !typed_stored_value_has_useful_info(&stored_value) &&
        move_metadata != NULL &&
        move_metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
        typed_value_for_memory_read_operand(lookup, state, platform_state, section_index, source_operand,
          move_metadata->operand_access_kinds[source_index], &stored_value, &source_origin)) {
      source_output = stored_value.output;
      source_struct_id = stored_value.struct_id;
      source_is_app_address = stored_value.app_address_known;
      source_app_displacement = stored_value.app_displacement;
      source_app_base_evidence_kind = stored_value.app_base_evidence_kind;
      source_array_element_count = stored_value.array_element_count;
      source_array_element_index = stored_value.array_element_index;
      source_byte_cursor = stored_value.byte_cursor;
      source_provenance = stored_value.provenance;
    }
    if (instruction->size_suffix == 'l' && move_metadata != NULL &&
        (move_metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ ||
         (source_operand->kind == M68K_ASM_OPERAND_EA && source_operand->value.ea_mode == 6U))) {
      /* A table base is retained as memory-base bookkeeping. That bookkeeping
       * is useful, but is not the pointee type of the long read from the
       * table, so it must not suppress pointer-table propagation. */
      if (typed_stored_value_from_pointer_table_read(&table_value, lookup, state, source_operand,
          section_index, offset, source_has_memory_base ? &source_memory_base : NULL)) {
        table_value.provenance.producer_operand_index = (uint8_t)source_index;
        if (source_struct_id == AMIGA_OS_STRUCT_ID_NONE && !typed_stored_value_has_useful_info(&stored_value))
          stored_value = table_value;
        else {
          stored_value.table_origin = table_value.table_origin;
          stored_value.pointer_target_known = table_value.pointer_target_known;
          stored_value.pointer_target_section_index = table_value.pointer_target_section_index;
          stored_value.pointer_target_offset = table_value.pointer_target_offset;
        }
        if (source_struct_id == AMIGA_OS_STRUCT_ID_NONE) source_struct_id = table_value.struct_id;
        source_provenance = table_value.provenance;
        if (record_table_load_consumers != 0 && operand_address_register_index_local(dest_operand, &table_load_dest_reg)) {
          (void)render_lookup_record_typed_table_load(lookup, section_index, offset, source_index,
            table_load_dest_reg, lookup_policy_struct_name_by_id(lookup->policy, table_value.struct_id), &table_value);
        }
        if (table_value.pointer_target_known) {
          source_memory_base.known = 1U;
          source_memory_base.section_index = table_value.pointer_target_section_index;
          source_memory_base.offset = table_value.pointer_target_offset;
          source_has_memory_base = 1;
          source_memory_base.pointer_table_known = 0U;
          {
            const M68kAnalysisStructuredDataItem *target_item =
              lookup_pointer_table_item_covering_address(lookup,
                table_value.pointer_target_section_index, table_value.pointer_target_offset);
            if (target_item != NULL) {
              source_memory_base.pointer_table_known = 1U;
              source_memory_base.pointer_table_struct_id = target_item->pointer_struct_id != AMIGA_OS_STRUCT_ID_NONE ?
                target_item->pointer_struct_id : lookup_policy_struct_id_by_name(lookup->policy,
                  target_item->pointer_struct);
              source_memory_base.pointer_table_section_index = target_item->section_index;
              source_memory_base.pointer_table_offset = target_item->offset;
              source_memory_base.pointer_table_size = target_item->size;
            }
          }
        }
      } else if (!typed_stored_value_has_useful_info(&stored_value) && source_memory_base.known &&
          typed_stored_value_bind_callback_table_origin(&stored_value, lookup, &source_memory_base,
            section_index, offset)) {
        source_provenance = stored_value.provenance;
      } else if (!typed_stored_value_has_useful_info(&stored_value) &&
          typed_stored_value_from_field_pointer_read(&stored_value, lookup, state, source_operand,
            section_index, offset)) {
        uint8_t base_reg = 0U;
        int16_t base_displacement = 0;
        /* A field-pointer read is a cached value derived from its base input.
         * Preserve that identity so a declared write/escape through the input
         * can invalidate the derived register without discarding the input. */
        if (operand_is_address_memory_local(source_operand, &base_reg, &base_displacement) &&
            base_reg < 8U) {
          source_origin.kind = M68K_RENDER_TYPED_ORIGIN_BASE_SLOT;
          source_origin.base_reg = base_reg;
          source_origin.displacement = state->addr_regs[base_reg].byte_cursor + base_displacement;
        }
        source_struct_id = stored_value.struct_id;
        source_provenance = stored_value.provenance;
      }
    }
    if (source_struct_id == AMIGA_OS_STRUCT_ID_NONE) {
      source_struct_id = typed_struct_id_for_base_slot_operand(lookup, platform_state, source_operand);
      if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE)
        source_provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_BASE_SLOT, section_index, offset);
    }
    if (source_origin.kind == M68K_RENDER_TYPED_ORIGIN_NONE && instruction->size_suffix == 'l' &&
        move_metadata != NULL && move_metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ) {
      uint8_t base_reg = 0U;
      int16_t base_displacement = 0;
      if (operand_is_address_memory_local(source_operand, &base_reg, &base_displacement) && base_reg < 8U &&
          state->addr_regs[base_reg].known && state->addr_regs[base_reg].struct_id != AMIGA_OS_STRUCT_ID_NONE) {
        /* A long read through a typed base is a value derived from that base,
         * even when field metadata supplied its pointee type directly. */
        source_origin.kind = M68K_RENDER_TYPED_ORIGIN_BASE_SLOT;
        source_origin.base_reg = base_reg;
        source_origin.displacement = state->addr_regs[base_reg].byte_cursor + base_displacement;
      }
    }
    if (instruction->size_suffix != 'l') {
      source_is_app_address = 0;
      stored_value.layout_base_id = 0U;
      stored_value.entry_value_id = 0U;
      typed_stored_value_forget_concrete_long(&stored_value);
    }
    /* Retain the lossless transfer path with the value itself.  It remains
     * transient until a typed pointer consumer promotes it to a durable
     * address-value fact. */
    typed_provenance_append_transfer(&stored_value.provenance, section_index, offset,
      (uint8_t)source_index, (uint8_t)dest_index);
    source_provenance = stored_value.provenance;
    if (operand_is_data_register_local(dest_operand, &dest_reg)) {
      typed_state_clear_reg(state, 1U, dest_reg);
      if (source_output != NULL &&
          (source_struct_id == AMIGA_OS_STRUCT_ID_NONE || source_output->struct_id != AMIGA_OS_STRUCT_ID_NONE)) {
        typed_state_set_reg(state, 1U, dest_reg, source_output, &source_provenance);
      } else if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
        typed_state_set_reg_struct_id_array(state, 1U, dest_reg, source_struct_id,
          source_array_element_count, source_array_element_index, &source_provenance);
        state->data_regs[dest_reg].byte_cursor = source_byte_cursor;
      }
      if (source_is_app_address) typed_state_set_data_app_address(state, dest_reg, source_app_displacement, source_app_base_evidence_kind);
      if (source_has_memory_base) state->data_memory_base_regs[dest_reg] = source_memory_base;
      if (stored_value.pointer_value_known) {
        state->data_regs[dest_reg].known = 1U;
        state->data_regs[dest_reg].pointer_value_known = 1U;
        state->data_regs[dest_reg].pointer_value = stored_value.pointer_value;
        state->data_regs[dest_reg].pointer_candidate_count = stored_value.pointer_candidate_count;
        memcpy(state->data_regs[dest_reg].pointer_candidates, stored_value.pointer_candidates,
          sizeof(state->data_regs[dest_reg].pointer_candidates));
      }
      state->data_regs[dest_reg].layout_base_id = stored_value.layout_base_id;
      state->data_regs[dest_reg].entry_value_id = stored_value.entry_value_id;
      if (stored_value.layout_base_id != 0U) state->data_regs[dest_reg].known = 1U;
      state->data_regs[dest_reg].table_origin = stored_value.table_origin;
      state->data_regs[dest_reg].pointer_target_known = stored_value.pointer_target_known;
      state->data_regs[dest_reg].pointer_target_section_index = stored_value.pointer_target_section_index;
      state->data_regs[dest_reg].pointer_target_offset = stored_value.pointer_target_offset;
      state->data_regs[dest_reg].address_value_candidate_overflow =
        stored_value.address_value_candidate_overflow;
      if (stored_value.raw_long_value_known) {
        state->data_regs[dest_reg].known = 1U;
        state->data_regs[dest_reg].raw_long_value_known = 1U;
        state->data_regs[dest_reg].raw_long_value = stored_value.raw_long_value;
        state->data_regs[dest_reg].raw_long_candidate_count = stored_value.raw_long_candidate_count;
        memcpy(state->data_regs[dest_reg].raw_long_candidates, stored_value.raw_long_candidates,
          sizeof(state->data_regs[dest_reg].raw_long_candidates));
      }
      if (stored_value.pointer_value_known || stored_value.raw_long_value_known)
        state->data_regs[dest_reg].provenance = stored_value.provenance;
      typed_state_set_reg_origin(state, 1U, dest_reg, &source_origin);
    } else if (operand_address_register_index_local(dest_operand, &dest_reg)) {
      typed_state_clear_reg(state, 2U, dest_reg);
      if (source_is_app_address) typed_state_set_app_address(state, dest_reg, source_app_displacement,
        source_struct_id, &source_provenance, source_app_base_evidence_kind);
      else if (source_output != NULL &&
          (source_struct_id == AMIGA_OS_STRUCT_ID_NONE || source_output->struct_id != AMIGA_OS_STRUCT_ID_NONE)) {
        typed_state_set_reg(state, 2U, dest_reg, source_output, &source_provenance);
      } else if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
        typed_state_set_reg_struct_id_array(state, 2U, dest_reg, source_struct_id,
          source_array_element_count, source_array_element_index, &source_provenance);
        state->addr_regs[dest_reg].byte_cursor = source_byte_cursor;
      }
      if (source_has_memory_base) state->memory_base_regs[dest_reg] = source_memory_base;
      if (stored_value.pointer_value_known) {
        state->addr_regs[dest_reg].known = 1U;
        state->addr_regs[dest_reg].pointer_value_known = 1U;
        state->addr_regs[dest_reg].pointer_value = stored_value.pointer_value;
        state->addr_regs[dest_reg].pointer_candidate_count = stored_value.pointer_candidate_count;
        memcpy(state->addr_regs[dest_reg].pointer_candidates, stored_value.pointer_candidates,
          sizeof(state->addr_regs[dest_reg].pointer_candidates));
      }
      state->addr_regs[dest_reg].layout_base_id = stored_value.layout_base_id;
      state->addr_regs[dest_reg].entry_value_id = stored_value.entry_value_id;
      if (stored_value.layout_base_id != 0U) state->addr_regs[dest_reg].known = 1U;
      state->addr_regs[dest_reg].table_origin = stored_value.table_origin;
      state->addr_regs[dest_reg].pointer_target_known = stored_value.pointer_target_known;
      state->addr_regs[dest_reg].pointer_target_section_index = stored_value.pointer_target_section_index;
      state->addr_regs[dest_reg].pointer_target_offset = stored_value.pointer_target_offset;
      state->addr_regs[dest_reg].address_value_candidate_overflow =
        stored_value.address_value_candidate_overflow;
      if (stored_value.raw_long_value_known) {
        state->addr_regs[dest_reg].known = 1U;
        state->addr_regs[dest_reg].raw_long_value_known = 1U;
        state->addr_regs[dest_reg].raw_long_value = stored_value.raw_long_value;
        state->addr_regs[dest_reg].raw_long_candidate_count = stored_value.raw_long_candidate_count;
        memcpy(state->addr_regs[dest_reg].raw_long_candidates, stored_value.raw_long_candidates,
          sizeof(state->addr_regs[dest_reg].raw_long_candidates));
      }
      if (stored_value.pointer_value_known || stored_value.raw_long_value_known)
        state->addr_regs[dest_reg].provenance = stored_value.provenance;
      typed_state_set_reg_origin(state, 2U, dest_reg, &source_origin);
    }
    if (instruction->size_suffix == 'l' && operand_is_predec_a7_local(dest_operand)) {
      typed_state_rebase_stack_slots(state, 4);
      if (typed_stored_value_has_useful_info(&stored_value) || source_has_memory_base)
        typed_state_set_stack_slot(state, 0, 1U, M68K_FUNCTION_SUMMARY_ABI_STACK_NONE, &stored_value,
          source_has_memory_base ? &source_memory_base : NULL);
      recognized_stack_update = 1;
    } else if (instruction->size_suffix == 'l' && operand_is_postinc_a7_local(source_operand)) {
      typed_state_rebase_stack_slots(state, -4);
      recognized_stack_update = 1;
    }
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U) {
    if (operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
      uint8_t source_base_reg = 0U, target_address_reg = 0U;
      int16_t source_displacement = 0;
      M68kRenderTypedAppAddressValue source_app_base = {0};
      size_t target_section_index = 0U;
      uint32_t target_offset = 0U;
      if (operand_is_address_memory_local(&instruction->operands[0], &source_base_reg, &source_displacement) &&
          source_base_reg < 8U) source_app_base = state->app_addr_regs[source_base_reg];
      typed_state_clear_reg(state, 2U, dest_reg);
      source_struct_id = AMIGA_OS_STRUCT_ID_NONE;
      if (typed_app_address_operand_info(lookup, platform_state, &instruction->operands[0],
          &source_app_displacement, &source_struct_id, &source_app_base_evidence_kind)) {
        M68kRenderTypedProvenance app_provenance =
          typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_APP_SLOT, section_index, offset);
        typed_state_set_app_address(state, dest_reg, source_app_displacement, source_struct_id, &app_provenance,
          source_app_base_evidence_kind);
      } else if (operand_is_address_memory_local(&instruction->operands[0], &source_base_reg,
          &source_displacement) && source_base_reg < 8U && state->addr_regs[source_base_reg].known) {
        if (source_displacement == 0) {
          source_struct_id = state->addr_regs[source_base_reg].struct_id;
          if (state->app_addr_regs[source_base_reg].known) {
            typed_state_set_app_address(state, dest_reg, state->app_addr_regs[source_base_reg].displacement,
              source_struct_id, &state->addr_regs[source_base_reg].provenance,
              state->app_addr_regs[source_base_reg].base_evidence_kind);
          } else if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
            typed_state_set_reg_struct_id_array(state, 2U, dest_reg, source_struct_id,
              state->addr_regs[source_base_reg].array_element_count,
              state->addr_regs[source_base_reg].array_element_index,
              &state->addr_regs[source_base_reg].provenance);
            state->addr_regs[dest_reg].byte_cursor = state->addr_regs[source_base_reg].byte_cursor;
            typed_state_set_reg_origin(state, 2U, dest_reg, &state->addr_regs[source_base_reg].origin);
          }
        } else {
          source_struct_id = typed_nested_struct_id_for_field_address(lookup, state, &instruction->operands[0]);
          if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
            M68kRenderTypedProvenance field_provenance =
              typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_FIELD_ADDRESS, section_index, offset);
            typed_state_set_reg_struct_id(state, 2U, dest_reg, source_struct_id, &field_provenance);
          } else {
            const M68kRenderTypedRegValue *source_value = &state->addr_regs[source_base_reg];
            uint16_t source_struct_size = lookup_policy_struct_size_by_id(lookup->policy,
              source_value->struct_id);
            int64_t source_relative_offset = (int64_t)source_value->byte_cursor + source_displacement;
            uint16_t destination_array_index = source_value->array_element_index;
            int32_t destination_cursor = 0;
            int valid = 0;
            if (source_value->array_element_count != 0U && source_struct_size != 0U) {
              source_relative_offset += (int64_t)source_value->array_element_index * source_struct_size;
              if (source_relative_offset >= 0 && source_relative_offset <
                  (int64_t)source_value->array_element_count * source_struct_size) {
                destination_array_index = (uint16_t)(source_relative_offset / source_struct_size);
                destination_cursor = (int32_t)(source_relative_offset % source_struct_size);
                valid = 1;
              }
            } else if (source_relative_offset >= 0 && source_relative_offset < source_struct_size) {
              destination_cursor = (int32_t)source_relative_offset;
              valid = 1;
            }
            if (valid) {
              M68kRenderTypedProvenance field_provenance =
                typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_FIELD_ADDRESS, section_index, offset);
              typed_state_set_reg_struct_id_array(state, 2U, dest_reg, source_value->struct_id,
                source_value->array_element_count, destination_array_index, &field_provenance);
              state->addr_regs[dest_reg].byte_cursor = destination_cursor;
              typed_state_set_reg_origin(state, 2U, dest_reg, &source_value->origin);
            }
          }
        }
      }
      if (!typed_operand_is_runtime_only(lookup, section_index, offset, 0U) &&
          ((candidate_loads_data_target_to_address_reg(candidate, instruction, &target_section_index, &target_offset,
            &target_address_reg) && target_address_reg == dest_reg) ||
          (candidate_loads_runtime_address_ref_target_to_address_reg(lookup, section_index, candidate, instruction,
            &target_section_index, &target_offset, &target_address_reg) && target_address_reg == dest_reg))) {
        uint16_t static_array_element_count = 0U, static_array_element_index = 0U;
        uint16_t static_conflict_struct_id = AMIGA_OS_STRUCT_ID_NONE;
        int32_t static_byte_cursor = 0;
        source_struct_id = lookup_policy_struct_id_for_static_data_target(lookup != NULL ? lookup->policy : NULL,
          target_section_index, target_offset, &static_array_element_count, &static_array_element_index,
          &static_byte_cursor, &static_conflict_struct_id);
        if (static_conflict_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
          M68kRenderTypedRegValue *value = &state->addr_regs[dest_reg];
          M68kRenderTypedProvenance static_data_provenance =
            typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA, target_section_index, target_offset);
          typed_reg_value_clear(value);
          value->type_conflicted = 1U;
          value->struct_id = source_struct_id;
          value->conflict_struct_id = static_conflict_struct_id;
          value->provenance = static_data_provenance;
        } else if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
          M68kRenderTypedProvenance static_data_provenance =
            typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA, target_section_index, target_offset);
          typed_state_set_reg_struct_id_array(state, 2U, dest_reg, source_struct_id,
            static_array_element_count, static_array_element_index, &static_data_provenance);
          state->addr_regs[dest_reg].byte_cursor = static_byte_cursor;
        }
        typed_state_set_memory_base(state, 2U, dest_reg, target_section_index, target_offset);
        typed_memory_base_bind_pointer_table(&state->memory_base_regs[dest_reg], lookup);
        {
          uint32_t target_runtime_address = 0U;
          if (lookup_source_runtime_address(lookup, target_section_index, target_offset,
              &target_runtime_address)) {
            /* A static address remains a pointer value even when overlapping
             * structured-data facts leave its pointee type conflicted.  Do
             * not turn that conflict into a trusted typed base. */
            if (static_conflict_struct_id == AMIGA_OS_STRUCT_ID_NONE)
              state->addr_regs[dest_reg].known = 1U;
            state->addr_regs[dest_reg].pointer_value_known = 1U;
            state->addr_regs[dest_reg].pointer_value = target_runtime_address;
            state->addr_regs[dest_reg].pointer_candidate_count = 1U;
            state->addr_regs[dest_reg].pointer_candidates[0] = target_runtime_address;
          }
        }
      } else if (operand_is_address_memory_local(&instruction->operands[0], &source_base_reg,
          &source_displacement) && source_base_reg < 8U && state->memory_base_regs[source_base_reg].known) {
        M68kRenderTypedMemoryBaseValue derived_base;
        if (typed_memory_base_with_displacement(&state->memory_base_regs[source_base_reg], source_displacement,
            &derived_base)) {
          state->memory_base_regs[dest_reg] = derived_base;
          typed_memory_base_bind_pointer_table(&state->memory_base_regs[dest_reg], lookup);
        }
      }
      /* An explicit absolute LEA outside mapped source is still an exact
       * runtime number. Keep raw bits only; no source pointer/type is guessed. */
      if (!state->memory_base_regs[dest_reg].known && !state->addr_regs[dest_reg].pointer_value_known &&
          operand_absolute_offset_local(&instruction->operands[0], &immediate_value)) {
        M68kRenderTypedRegValue *value = &state->addr_regs[dest_reg];
        value->raw_long_value_known = value->raw_long_candidate_count = value->known = 1U;
        value->raw_long_value = value->raw_long_candidates[0] = immediate_value;
        value->provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_CONSTANT_VALUE,
          section_index, offset);
      }
      /* An address into an untyped byte array is still an address. Keep this
       * independent of pointee-struct inference and of a self-LEA overwrite. */
      if (source_app_base.known) {
        int32_t next = (int32_t)source_app_base.displacement + source_displacement;
        if (next >= INT16_MIN && next <= INT16_MAX) {
          state->app_addr_regs[dest_reg] = source_app_base;
          state->app_addr_regs[dest_reg].displacement = (int16_t)next;
        }
      }
    }
  } else if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADD ||
              instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDA ||
              instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDI ||
              instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDQ ||
              instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUB ||
              instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBA ||
              instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBI ||
              instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBQ) &&
             instruction->operand_count == 2U &&
             m68k_ir_operand_immediate_value(&instruction->operands[0], &immediate_value) &&
             operand_address_register_index_local(&instruction->operands[1], &dest_reg) && dest_reg < 8U) {
    M68kRenderTypedAppAddressValue previous_app = state->app_addr_regs[dest_reg];
    M68kRenderTypedRegValue *value = &state->addr_regs[dest_reg];
    M68kRenderTypedRegValue raw_before = *value;
    int32_t delta = (instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUB ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBA ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBI ||
      instruction->mnemonic_id == M68K_ASM_MNEMONIC_SUBQ) ? -(int32_t)immediate_value : (int32_t)immediate_value;
    uint16_t struct_size = lookup_policy_struct_size_by_id(lookup->policy, value->struct_id);
    int32_t next_index;
    if (value->known != 0U && (value->array_element_count == 0U || struct_size == 0U ||
        delta % (int32_t)struct_size != 0)) {
      int64_t next_cursor = (int64_t)value->byte_cursor + (int64_t)delta;
      if (next_cursor < INT32_MIN || next_cursor > INT32_MAX) {
        typed_state_clear_address_reg_preserving_affine(state, dest_reg, delta);
      } else {
        value->output = NULL;
        value->byte_cursor = (int32_t)next_cursor;
        if (state->memory_base_regs[dest_reg].known &&
            typed_memory_base_apply_affine_delta(&state->memory_base_regs[dest_reg], delta)) {
        } else if (state->memory_base_regs[dest_reg].known) {
          typed_memory_base_clear(&state->memory_base_regs[dest_reg]);
        }
      }
    } else if (value->known == 0U || value->array_element_count == 0U || struct_size == 0U ||
               delta % (int32_t)struct_size != 0) {
      typed_state_clear_address_reg_preserving_affine(state, dest_reg, delta);
    } else {
      next_index = (int32_t)value->array_element_index + delta / (int32_t)struct_size;
      if (next_index < 0 || next_index >= (int32_t)value->array_element_count) {
        typed_state_clear_address_reg_preserving_affine(state, dest_reg, delta);
      } else {
        value->output = NULL;
        value->array_element_index = (uint16_t)next_index;
        state->app_addr_regs[dest_reg].known = 0U;
        state->app_addr_regs[dest_reg].displacement = 0;
        state->app_addr_regs[dest_reg].base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
        if (state->memory_base_regs[dest_reg].known &&
            typed_memory_base_apply_affine_delta(&state->memory_base_regs[dest_reg], delta)) {
        } else if (state->memory_base_regs[dest_reg].known) {
          typed_memory_base_clear(&state->memory_base_regs[dest_reg]);
        }
      }
    }
    typed_address_raw_long_after_immediate(&state->addr_regs[dest_reg], &raw_before,
      instruction, section_index, offset);
    /* Retain only exactly represented arithmetic. Signed WORD immediates
     * outside the nonnegative range need a separate signed decode contract. */
    int64_t app_delta;
    if (previous_app.known && typed_app_cursor_immediate_delta(instruction, &app_delta)) {
      int64_t next = (int64_t)previous_app.displacement + app_delta;
      if (next >= INT16_MIN && next <= INT16_MAX) {
        state->app_addr_regs[dest_reg] = previous_app;
        state->app_addr_regs[dest_reg].displacement = (int16_t)next;
      }
    }
  } else if (instruction->operand_count != 0U) {
    for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
      const M68kOperandIR *operand = &instruction->operands[operand_index];
      if (!instruction_operand_writes_register_from_metadata(instruction, operand_index)) continue;
      if (operand_is_data_register_local(operand, &dest_reg)) {
        typed_state_clear_reg(state, 1U, dest_reg);
      } else if (operand_address_register_index_local(operand, &dest_reg)) {
        typed_state_clear_reg(state, 2U, dest_reg);
      }
    }
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata != NULL) {
    for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
      const M68kOperandIR *operand = &instruction->operands[operand_index];
      uint8_t ea_shape = m68k_instruction_operand_decoded_ea_shape(operand);
      /* Generic memory forms leave the update to the decoded EA shape, as
         the simulator does. Only a proven bounded single access retains type. */
      if (operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_reg >= 8U ||
          (metadata->operand_ea_register_updates[operand_index] == M68K_SIM_EA_UPDATE_NONE &&
           !((metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_READ ||
              metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_MEMORY_WRITE) &&
             (ea_shape == M68K_SIM_EA_SHAPE_POSTINCREMENT || ea_shape == M68K_SIM_EA_SHAPE_PREDECREMENT)))) {
        continue;
      }
      {
        M68kRenderTypedMemoryBaseValue memory_base = state->memory_base_regs[operand->value.ea_reg];
        M68kRenderTypedRegValue previous = state->addr_regs[operand->value.ea_reg];
        uint8_t update_width = 0U;
        int preserve_cursor = typed_single_auto_update_cursor(lookup, state, instruction, operand_index,
          NULL, &update_width);
        int32_t access_size = (int32_t)instruction_size_suffix_bytes_local(instruction->size_suffix);
        int32_t delta = operand->value.ea_mode == 3U ? access_size :
          (operand->value.ea_mode == 4U ? -access_size : 0);
        if (metadata->multi_transfer_direction != M68K_SIM_MULTI_NONE) {
          /* Multi-transfer source-affine retention is not this lane. Clearing
           * is preferable to silently advancing by one element. */
          typed_memory_base_clear(&memory_base);
          delta = 0;
        }
        typed_state_clear_reg(state, M68K_ANALYSIS_REGISTER_ADDRESS, operand->value.ea_reg);
        if (preserve_cursor) {
          uint16_t struct_size = lookup_policy_struct_size_by_id(lookup->policy, previous.struct_id);
          int64_t next;
          uint16_t next_index = previous.array_element_index;
          delta = ea_shape == M68K_SIM_EA_SHAPE_PREDECREMENT ? -(int32_t)update_width : (int32_t)update_width;
          next = (int64_t)previous.byte_cursor + delta;
          if (previous.array_element_count != 0U && next == struct_size &&
              (uint32_t)next_index + 1U < previous.array_element_count) {
            next = 0;
            ++next_index;
          }
          /* Retain a one-past cursor for bounded predecrement back into the
           * record. Access guards still reject a read/write at that endpoint. */
          if (next >= 0 && next <= struct_size) {
            typed_state_set_reg_struct_id_array(state, M68K_ANALYSIS_REGISTER_ADDRESS, operand->value.ea_reg,
              previous.struct_id, previous.array_element_count, next_index, &previous.provenance);
            state->addr_regs[operand->value.ea_reg].byte_cursor = (int32_t)next;
            state->addr_regs[operand->value.ea_reg].origin = previous.origin;
            state->addr_regs[operand->value.ea_reg].table_origin = previous.table_origin;
          }
        }
        if (delta == 0 || (!memory_base.known && !memory_base.pointer_table_known)) continue;
        if (memory_base.known) {
          if (!typed_memory_base_apply_affine_delta(&memory_base, delta)) continue;
        }
        state->memory_base_regs[operand->value.ea_reg] = memory_base;
      }
    }
  }
  {
    const M68kSimFormMetadata *metadata = m68k_sim_metadata_for_instruction(instruction);
    int full_copy = instruction->size_suffix == 'l' &&
      (instruction_move_operand_indices_from_metadata(instruction, NULL, NULL, NULL) ||
       (metadata != NULL && metadata->operation_type == M68K_SIM_OP_MOVE_MULTIPLE));
    if (!full_copy) for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
      uint16_t writes = platform_operand_register_write_mask(instruction, operand_index);
      uint8_t reg;
      for (reg = 0U; reg < 8U; ++reg) {
        if ((writes & (1U << reg)) != 0U) {
          state->data_regs[reg].layout_base_id = 0U;
          state->data_regs[reg].entry_value_id = 0U;
        }
        if ((writes & (1U << (8U + reg))) != 0U) {
          state->addr_regs[reg].layout_base_id = 0U;
          state->addr_regs[reg].entry_value_id = 0U;
        }
      }
    }
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    if (platform_operand_updates_address_register(instruction, operand_index) &&
        instruction->operands[operand_index].value.ea_reg < 8U)
      state->addr_regs[instruction->operands[operand_index].value.ea_reg].layout_base_id = 0U;
  }
  if (app_after_update.known) state->app_addr_regs[app_update_reg] = app_after_update;
  if (instruction_may_update_stack_pointer_from_metadata(instruction) && !recognized_stack_update &&
      !instruction_has_call_flow_local(instruction)) {
    int32_t adjustment;
    if (has_stack_transfer && stack_transfer.width == 2U) {
      adjustment = (int32_t)stack_transfer.width * stack_transfer.count;
      if (stack_transfer.direction == M68K_STACK_TRANSFER_POP) adjustment = -adjustment;
      typed_state_rebase_stack_slots(state, (int16_t)adjustment);
    } else if (instruction_stack_delta_for_comment(instruction, &adjustment) &&
        adjustment >= INT16_MIN && adjustment <= INT16_MAX) {
      typed_state_rebase_stack_slots(state, (int16_t)adjustment);
    } else typed_state_clear_stack_slots(state);
  }
  typed_addr_alias_transfer(state, instruction, alias_roots_before);
  affine_entry_transfer_after(state, lookup, instruction, entry_values_before, &stack_transfer,
    has_stack_transfer);
}

static int typed_reg_values_equal(const M68kRenderTypedRegValue *left,
    const M68kRenderTypedRegValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->type_conflicted == right->type_conflicted &&
    left->pointer_value_known == right->pointer_value_known && left->pointer_value == right->pointer_value &&
    left->pointer_candidate_count == right->pointer_candidate_count &&
    left->address_value_candidate_overflow == right->address_value_candidate_overflow &&
    memcmp(left->pointer_candidates, right->pointer_candidates, sizeof(left->pointer_candidates)) == 0 &&
    left->raw_long_value_known == right->raw_long_value_known && left->raw_long_value == right->raw_long_value &&
    left->raw_long_candidate_count == right->raw_long_candidate_count &&
    memcmp(left->raw_long_candidates, right->raw_long_candidates, sizeof(left->raw_long_candidates)) == 0 &&
    left->output == right->output && left->struct_id == right->struct_id &&
    left->conflict_struct_id == right->conflict_struct_id &&
    left->array_element_count == right->array_element_count && left->array_element_index == right->array_element_index &&
    left->byte_cursor == right->byte_cursor && left->layout_base_id == right->layout_base_id &&
    left->entry_value_id == right->entry_value_id &&
    typed_origins_equal(&left->origin, &right->origin) &&
    /* A provenance marker without any value cannot justify a consumer or a
     * new transfer. Do not schedule a loop merely because this dead marker
     * was cleared by a register overwrite. Conflicts and real values retain
     * their full provenance comparison. */
    ((!left->known && !right->known && !left->type_conflicted && !right->type_conflicted &&
      !left->pointer_value_known && !right->pointer_value_known &&
      !left->raw_long_value_known && !right->raw_long_value_known &&
      !left->address_value_candidate_overflow && !right->address_value_candidate_overflow &&
      left->struct_id == AMIGA_OS_STRUCT_ID_NONE && right->struct_id == AMIGA_OS_STRUCT_ID_NONE &&
      !left->table_origin.has_origin && !right->table_origin.has_origin) ||
      typed_provenances_equal(&left->provenance, &right->provenance));
}

static int typed_stored_values_equal(const M68kRenderTypedStoredValue *left,
    const M68kRenderTypedStoredValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->output == right->output && left->struct_id == right->struct_id &&
    left->layout_base_id == right->layout_base_id && left->entry_value_id == right->entry_value_id &&
    left->pointer_value_known == right->pointer_value_known && left->pointer_value == right->pointer_value &&
    left->pointer_candidate_count == right->pointer_candidate_count &&
    left->address_value_candidate_overflow == right->address_value_candidate_overflow &&
    memcmp(left->pointer_candidates, right->pointer_candidates, sizeof(left->pointer_candidates)) == 0 &&
    left->raw_long_value_known == right->raw_long_value_known && left->raw_long_value == right->raw_long_value &&
    left->raw_long_candidate_count == right->raw_long_candidate_count &&
    memcmp(left->raw_long_candidates, right->raw_long_candidates, sizeof(left->raw_long_candidates)) == 0 &&
    left->array_element_count == right->array_element_count &&
    left->array_element_index == right->array_element_index && left->byte_cursor == right->byte_cursor &&
    left->app_address_known == right->app_address_known && left->app_displacement == right->app_displacement &&
    left->app_base_evidence_kind == right->app_base_evidence_kind &&
    typed_provenances_equal(&left->provenance, &right->provenance);
}

static int typed_app_addresses_equal(const M68kRenderTypedAppAddressValue *left,
    const M68kRenderTypedAppAddressValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->displacement == right->displacement &&
    left->base_evidence_kind == right->base_evidence_kind;
}

static int typed_memory_bases_equal(const M68kRenderTypedMemoryBaseValue *left,
    const M68kRenderTypedMemoryBaseValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->section_index == right->section_index && left->offset == right->offset &&
    left->affine_known == right->affine_known &&
    left->affine_origin_section_index == right->affine_origin_section_index &&
    left->affine_origin_offset == right->affine_origin_offset &&
    left->affine_signed_addend == right->affine_signed_addend &&
    left->pointer_table_known == right->pointer_table_known &&
    left->pointer_table_struct_id == right->pointer_table_struct_id &&
    left->pointer_table_section_index == right->pointer_table_section_index &&
    left->pointer_table_offset == right->pointer_table_offset &&
    left->pointer_table_size == right->pointer_table_size;
}

static int typed_io_request_values_equal(const M68kRenderIoRequestSetupValue *left,
    const M68kRenderIoRequestSetupValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->value == right->value && left->source_offset == right->source_offset;
}

static int typed_io_request_setups_equal(const M68kRenderIoRequestSetup *left,
    const M68kRenderIoRequestSetup *right) {
  if (left == NULL || right == NULL) return 0;
  return typed_io_request_values_equal(&left->command, &right->command) &&
    typed_io_request_values_equal(&left->disk_offset, &right->disk_offset) &&
    typed_io_request_values_equal(&left->byte_length, &right->byte_length) &&
    typed_io_request_values_equal(&left->destination, &right->destination);
}

static int typed_stack_slots_equal(const M68kRenderTypedStackSlot *left,
    const M68kRenderTypedStackSlot *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->caller_save_temporary == right->caller_save_temporary &&
    left->abi_stack_convention == right->abi_stack_convention &&
    left->displacement == right->displacement &&
    typed_memory_bases_equal(&left->memory_base, &right->memory_base) &&
    typed_stored_values_equal(&left->value, &right->value);
}

static int typed_base_slots_equal(const M68kRenderTypedBaseSlot *left,
    const M68kRenderTypedBaseSlot *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->base_reg == right->base_reg &&
    left->displacement == right->displacement && left->storage_id == right->storage_id &&
    typed_stored_values_equal(&left->value, &right->value);
}

static int typed_base_slot_sets_equal(const M68kRenderTypedState *left, const M68kRenderTypedState *right) {
  size_t index;
  if (left == NULL || right == NULL || left->base_slot_count != right->base_slot_count) return 0;
  for (index = 0U; index < left->base_slot_count; ++index) {
    const M68kRenderTypedBaseSlot *left_slot = &left->base_slots[index];
    const M68kRenderTypedBaseSlot *right_slot = left_slot->storage_id != 0U ?
      typed_state_absolute_cell(right, left_slot->storage_id) :
      typed_state_base_slot_entry(right, left_slot->base_reg, left_slot->displacement);
    if (!typed_base_slots_equal(left_slot, right_slot)) return 0;
  }
  return 1;
}

static int typed_field_slot_sets_equal(const M68kRenderTypedState *left, const M68kRenderTypedState *right) {
  size_t index;
  if (left == NULL || right == NULL || left->field_slot_count != right->field_slot_count) return 0;
  for (index = 0U; index < left->field_slot_count; ++index) {
    const M68kRenderTypedFieldSlot *left_slot = &left->field_slots[index];
    const M68kRenderTypedFieldSlot *right_slot = typed_state_field_slot_entry(right, left_slot->base_reg,
      left_slot->struct_id, left_slot->displacement);
    if (right_slot == NULL || right_slot->known != left_slot->known ||
        !typed_stored_values_equal(&left_slot->value, &right_slot->value)) return 0;
  }
  return 1;
}

static int typed_state_equal(const M68kRenderTypedState *left, const M68kRenderTypedState *right) {
  size_t index;
  if (left == NULL || right == NULL || left->stack_slot_count != right->stack_slot_count ||
      left->base_slot_count != right->base_slot_count || left->field_slot_count != right->field_slot_count ||
      left->absolute_memory_written != right->absolute_memory_written) {
    return 0;
  }
  for (index = 0U; index < 8U; ++index) {
    if (!typed_reg_values_equal(&left->data_regs[index], &right->data_regs[index])) return 0;
    if (!typed_reg_values_equal(&left->addr_regs[index], &right->addr_regs[index])) return 0;
    if (!typed_app_addresses_equal(&left->data_app_addr_regs[index], &right->data_app_addr_regs[index])) return 0;
    if (!typed_app_addresses_equal(&left->app_addr_regs[index], &right->app_addr_regs[index])) return 0;
    if (!typed_memory_bases_equal(&left->data_memory_base_regs[index], &right->data_memory_base_regs[index]))
      return 0;
    if (!typed_memory_bases_equal(&left->memory_base_regs[index], &right->memory_base_regs[index])) return 0;
    if (!typed_io_request_setups_equal(&left->io_request_setups[index], &right->io_request_setups[index])) return 0;
    if (m68k_bitset_u32_has(left->addr_reg_alias_known, (uint8_t)index) !=
        m68k_bitset_u32_has(right->addr_reg_alias_known, (uint8_t)index)) {
      return 0;
    }
    if (m68k_bitset_u32_has(left->addr_reg_alias_known, (uint8_t)index) &&
        left->addr_reg_alias_source[index] != right->addr_reg_alias_source[index]) {
      return 0;
    }
  }
  for (index = 0U; index < left->stack_slot_count; ++index) {
    if (!typed_stack_slots_equal(&left->stack_slots[index], &right->stack_slots[index])) return 0;
  }
  if (!typed_base_slot_sets_equal(left, right)) return 0;
  if (!typed_field_slot_sets_equal(left, right)) return 0;
  return 1;
}

static int platform_states_equal(const M68kRenderPlatformState *left, const M68kRenderPlatformState *right) {
  if (left == NULL || right == NULL) return 0;
  return memcmp(left, right, sizeof(*left)) == 0;
}

static void typed_reg_value_mark_address_value_candidate_overflow(M68kRenderTypedRegValue *value) {
  if (value == NULL) return;
  value->layout_base_id = 0U;
  value->pointer_value_known = 0U;
  value->pointer_value = 0U;
  value->pointer_candidate_count = 0U;
  memset(value->pointer_candidates, 0, sizeof(value->pointer_candidates));
  value->raw_long_value_known = 0U;
  value->raw_long_value = 0U;
  value->raw_long_candidate_count = 0U;
  memset(value->raw_long_candidates, 0, sizeof(value->raw_long_candidates));
  value->address_value_candidate_overflow = 1U;
  typed_table_origin_clear(&value->table_origin);
}

static void typed_stored_value_mark_address_value_candidate_overflow(M68kRenderTypedStoredValue *value) {
  if (value == NULL) return;
  value->layout_base_id = 0U;
  value->pointer_value_known = 0U;
  value->pointer_value = 0U;
  value->pointer_candidate_count = 0U;
  memset(value->pointer_candidates, 0, sizeof(value->pointer_candidates));
  value->raw_long_value_known = 0U;
  value->raw_long_value = 0U;
  value->raw_long_candidate_count = 0U;
  memset(value->raw_long_candidates, 0, sizeof(value->raw_long_candidates));
  value->address_value_candidate_overflow = 1U;
  typed_table_origin_clear(&value->table_origin);
}

/* Pointer origin and current object position are different components.
 * A join cannot retain an exact source pointer while choosing one incoming
 * cursor. Both register and stored packets use this same position rule. */
static int typed_pointer_position_disagrees(uint16_t left_count, uint16_t left_index, int32_t left_cursor,
    uint16_t right_count, uint16_t right_index, int32_t right_cursor) {
  return left_index != right_index || left_cursor != right_cursor ||
    (left_count != right_count && (left_index != 0U || right_index != 0U));
}

#define TYPED_FORGET_CURRENT_SOURCE_POINTER(value) do { \
  (value)->pointer_value_known = (value)->pointer_candidate_count = (value)->pointer_target_known = 0U; \
  (value)->pointer_value = (value)->pointer_target_offset = 0U; \
  (value)->pointer_target_section_index = 0U; \
  memset((value)->pointer_candidates, 0, sizeof((value)->pointer_candidates)); \
  typed_table_origin_clear(&(value)->table_origin); \
} while (0)

static int typed_reg_merge_payload(M68kRenderTypedRegValue *dest, const M68kRenderTypedRegValue *source) {
  M68kRenderTypedRegValue old_value;
  if (dest == NULL || source == NULL) return 0;
  old_value = *dest;
  if (dest->layout_base_id != source->layout_base_id) dest->layout_base_id = 0U;
  if (dest->table_origin.has_origin != 0U && source->table_origin.has_origin != 0U &&
      !typed_table_origins_equal(&dest->table_origin, &source->table_origin)) {
    typed_table_origin_clear(&dest->table_origin);
  }
  if (dest->type_conflicted != 0U || source->type_conflicted != 0U) {
    if (dest->type_conflicted == 0U) *dest = *source;
    dest->layout_base_id = 0U;
    dest->known = 0U;
    dest->type_conflicted = 1U;
    dest->output = NULL;
    dest->array_element_count = 0U;
    dest->array_element_index = 0U;
    dest->byte_cursor = 0;
    dest->pointer_value_known = 0U;
    dest->pointer_value = 0U;
    dest->pointer_candidate_count = 0U;
    dest->raw_long_value_known = 0U;
    dest->raw_long_value = 0U;
    dest->raw_long_candidate_count = 0U;
    dest->address_value_candidate_overflow |= source->address_value_candidate_overflow;
    typed_origin_clear(&dest->origin);
    typed_provenance_merge(&dest->provenance, &source->provenance);
    return !typed_reg_values_equal(dest, &old_value);
  }
  /* The caller copies the first reachable predecessor before merging. An
   * unknown value here is therefore a real incoming path, not an empty
   * accumulator. It must absorb later pointer/scalar facts in either order. */
  if (dest->known == 0U || source->known == 0U) {
    typed_reg_value_clear(dest);
    return !typed_reg_values_equal(dest, &old_value);
  }
  if (dest->layout_base_id == 0U &&
      (old_value.layout_base_id != 0U || source->layout_base_id != 0U) &&
      dest->output == NULL && source->output == NULL &&
      dest->struct_id == AMIGA_OS_STRUCT_ID_NONE && source->struct_id == AMIGA_OS_STRUCT_ID_NONE &&
      !dest->pointer_value_known && !source->pointer_value_known &&
      !dest->raw_long_value_known && !source->raw_long_value_known) {
    typed_reg_value_clear(dest);
    return !typed_reg_values_equal(dest, &old_value);
  }
  if (dest->address_value_candidate_overflow != 0U || source->address_value_candidate_overflow != 0U) {
    typed_reg_value_mark_address_value_candidate_overflow(dest);
    typed_origin_clear(&dest->origin);
    typed_provenance_merge(&dest->provenance, &source->provenance);
    return !typed_reg_values_equal(dest, &old_value);
  }
  if (typed_pointer_position_disagrees(dest->array_element_count, dest->array_element_index, dest->byte_cursor,
      source->array_element_count, source->array_element_index, source->byte_cursor) ||
      (dest->array_element_index != 0U &&
       (dest->struct_id != source->struct_id || dest->output != source->output))) {
    int same_cursor = dest->byte_cursor == source->byte_cursor;
    dest->struct_id = same_cursor ? typed_struct_id_common_merge(dest->struct_id, source->struct_id) : AMIGA_OS_STRUCT_ID_NONE;
    if (!same_cursor || dest->output != source->output) dest->output = NULL;
    dest->array_element_count = dest->array_element_index = 0U;
    if (!same_cursor) dest->byte_cursor = 0;
    TYPED_FORGET_CURRENT_SOURCE_POINTER(dest);
    if (typed_must_candidates_merge(&dest->raw_long_value_known, &dest->raw_long_candidate_count,
        &dest->raw_long_value, dest->raw_long_candidates, source->raw_long_value_known,
        source->raw_long_candidate_count, source->raw_long_value, source->raw_long_candidates) ==
        M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW) typed_reg_value_mark_address_value_candidate_overflow(dest);
    typed_origin_clear(&dest->origin);
    typed_provenance_merge(&dest->provenance, &source->provenance);
    dest->known = dest->layout_base_id || dest->output || dest->struct_id != AMIGA_OS_STRUCT_ID_NONE ||
      dest->raw_long_value_known || dest->address_value_candidate_overflow;
    if (!dest->known) typed_reg_value_clear(dest);
    return !typed_reg_values_equal(dest, &old_value);
  }
  /* A bounds disagreement at element zero loses the array extent, not
   * an otherwise identical current pointer/subobject coordinate. */
  if (dest->array_element_count != source->array_element_count) {
    dest->array_element_count = dest->array_element_index = 0U;
  }
  if (dest->output == NULL && source->output == NULL &&
      dest->struct_id == AMIGA_OS_STRUCT_ID_NONE && source->struct_id == AMIGA_OS_STRUCT_ID_NONE &&
      dest->address_value_candidate_overflow == 0U && source->address_value_candidate_overflow == 0U) {
    M68kRenderPointerCandidateMergeResult pointer_merged = typed_must_candidates_merge(
      &dest->pointer_value_known, &dest->pointer_candidate_count,
      &dest->pointer_value, dest->pointer_candidates, source->pointer_value_known,
      source->pointer_candidate_count, source->pointer_value, source->pointer_candidates);
    M68kRenderPointerCandidateMergeResult raw_merged = typed_must_candidates_merge(
      &dest->raw_long_value_known, &dest->raw_long_candidate_count,
      &dest->raw_long_value, dest->raw_long_candidates, source->raw_long_value_known,
      source->raw_long_candidate_count, source->raw_long_value, source->raw_long_candidates);
    if (pointer_merged == M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW ||
        raw_merged == M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW) {
      typed_reg_value_mark_address_value_candidate_overflow(dest);
      typed_origin_clear(&dest->origin);
      typed_provenance_merge(&dest->provenance, &source->provenance);
      return !typed_reg_values_equal(dest, &old_value);
    }
    if (pointer_merged == M68K_RENDER_POINTER_CANDIDATE_MERGE_EXACT ||
        raw_merged == M68K_RENDER_POINTER_CANDIDATE_MERGE_EXACT) {
      typed_origin_clear(&dest->origin);
      typed_provenance_merge(&dest->provenance, &source->provenance);
      return !typed_reg_values_equal(dest, &old_value);
    }
  }
  if (dest->output == source->output && dest->struct_id == source->struct_id &&
      dest->pointer_value_known == source->pointer_value_known && dest->pointer_value == source->pointer_value &&
      dest->raw_long_value_known == source->raw_long_value_known && dest->raw_long_value == source->raw_long_value &&
      (dest->array_element_count == source->array_element_count ||
       (dest->array_element_index == 0U && source->array_element_index == 0U)) &&
      dest->array_element_index == source->array_element_index && dest->byte_cursor == source->byte_cursor) {
    if (!typed_origins_equal(&dest->origin, &source->origin)) typed_origin_clear(&dest->origin);
    typed_provenance_merge(&dest->provenance, &source->provenance);
    return !typed_reg_values_equal(dest, &old_value);
  }
  {
    uint16_t common_struct_id = typed_struct_id_common_merge(dest->struct_id, source->struct_id);
    if (common_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
      dest->struct_id = common_struct_id;
      dest->output = NULL;
      if (dest->array_element_index != 0U) TYPED_FORGET_CURRENT_SOURCE_POINTER(dest);
      dest->array_element_count = 0U;
      dest->array_element_index = 0U;
      if (typed_must_candidates_merge(&dest->pointer_value_known, &dest->pointer_candidate_count,
          &dest->pointer_value, dest->pointer_candidates, source->pointer_value_known,
          source->pointer_candidate_count, source->pointer_value, source->pointer_candidates) ==
          M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW) {
        dest->pointer_value_known = 0U;
        dest->pointer_value = 0U;
        dest->pointer_candidate_count = 0U;
        dest->address_value_candidate_overflow = 1U;
      }
      if (typed_must_candidates_merge(&dest->raw_long_value_known, &dest->raw_long_candidate_count,
          &dest->raw_long_value, dest->raw_long_candidates, source->raw_long_value_known,
          source->raw_long_candidate_count, source->raw_long_value, source->raw_long_candidates) ==
          M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW) {
        dest->raw_long_value_known = 0U;
        dest->raw_long_value = 0U;
        dest->raw_long_candidate_count = 0U;
        dest->address_value_candidate_overflow = 1U;
      }
      if (dest->address_value_candidate_overflow != 0U) {
        typed_reg_value_mark_address_value_candidate_overflow(dest);
      }
      if (!typed_origins_equal(&dest->origin, &source->origin)) typed_origin_clear(&dest->origin);
      typed_provenance_merge(&dest->provenance, &source->provenance);
      return !typed_reg_values_equal(dest, &old_value);
    }
  }
  if (dest->struct_id != AMIGA_OS_STRUCT_ID_NONE && dest->struct_id == source->struct_id) {
    dest->output = NULL;
    if (dest->array_element_index != 0U) TYPED_FORGET_CURRENT_SOURCE_POINTER(dest);
    dest->array_element_count = 0U;
    dest->array_element_index = 0U;
    if (typed_must_candidates_merge(&dest->pointer_value_known, &dest->pointer_candidate_count,
        &dest->pointer_value, dest->pointer_candidates, source->pointer_value_known,
        source->pointer_candidate_count, source->pointer_value, source->pointer_candidates) ==
        M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW) {
      dest->pointer_value_known = 0U;
      dest->pointer_value = 0U;
      dest->pointer_candidate_count = 0U;
      dest->address_value_candidate_overflow = 1U;
    }
    if (typed_must_candidates_merge(&dest->raw_long_value_known, &dest->raw_long_candidate_count,
        &dest->raw_long_value, dest->raw_long_candidates, source->raw_long_value_known,
        source->raw_long_candidate_count, source->raw_long_value, source->raw_long_candidates) ==
        M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW) {
      dest->raw_long_value_known = 0U;
      dest->raw_long_value = 0U;
      dest->raw_long_candidate_count = 0U;
      dest->address_value_candidate_overflow = 1U;
    }
    if (dest->address_value_candidate_overflow != 0U) {
      typed_reg_value_mark_address_value_candidate_overflow(dest);
    }
    return !typed_reg_values_equal(dest, &old_value);
  }
  dest->layout_base_id = 0U;
  dest->known = 0U;
  dest->type_conflicted = 1U;
  dest->output = NULL;
  dest->conflict_struct_id = source->struct_id;
  dest->array_element_count = 0U;
  dest->array_element_index = 0U;
  dest->byte_cursor = 0;
  dest->pointer_value_known = 0U;
  dest->pointer_value = 0U;
  dest->pointer_candidate_count = 0U;
  dest->raw_long_value_known = 0U;
  dest->raw_long_value = 0U;
  dest->raw_long_candidate_count = 0U;
  dest->address_value_candidate_overflow |= source->address_value_candidate_overflow;
  typed_origin_clear(&dest->origin);
  typed_provenance_merge(&dest->provenance, &source->provenance);
  return !typed_reg_values_equal(dest, &old_value);
}

static int typed_reg_merge(M68kRenderTypedRegValue *dest, const M68kRenderTypedRegValue *source) {
  M68kRenderTypedRegValue old, payload;
  uint32_t id;
  if (!dest || !source) return 0;
  if (!dest->entry_value_id && !source->entry_value_id) return typed_reg_merge_payload(dest, source);
  old = *dest; payload = *source;
  id = dest->entry_value_id == source->entry_value_id ? dest->entry_value_id : 0U;
  dest->entry_value_id = payload.entry_value_id = 0U;
  (void)typed_reg_merge_payload(dest, &payload);
  dest->entry_value_id = id;
  return !typed_reg_values_equal(dest, &old);
}

static int typed_stored_value_merge_payload(M68kRenderTypedStoredValue *dest,
    const M68kRenderTypedStoredValue *source) {
  M68kRenderTypedStoredValue old_value;
  if (dest == NULL || source == NULL) return 0;
  old_value = *dest;
  if (dest->layout_base_id != source->layout_base_id) dest->layout_base_id = 0U;
  if (dest->table_origin.has_origin != 0U && source->table_origin.has_origin != 0U &&
      !typed_table_origins_equal(&dest->table_origin, &source->table_origin)) {
    typed_table_origin_clear(&dest->table_origin);
  }
  if (!typed_stored_value_has_useful_info(dest) || !typed_stored_value_has_useful_info(source)) {
    typed_stored_value_clear(dest);
    return !typed_stored_values_equal(dest, &old_value);
  }
  if (dest->app_address_known != source->app_address_known ||
      dest->app_displacement != source->app_displacement) {
    dest->app_address_known = 0U;
    dest->app_displacement = 0;
    dest->app_base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
  } else if (dest->app_base_evidence_kind != source->app_base_evidence_kind) {
    dest->app_base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
  }
  if (typed_pointer_position_disagrees(dest->array_element_count, dest->array_element_index, dest->byte_cursor,
      source->array_element_count, source->array_element_index, source->byte_cursor) ||
      (dest->array_element_index != 0U &&
       (dest->struct_id != source->struct_id || dest->output != source->output))) {
    int same_cursor = dest->byte_cursor == source->byte_cursor;
    dest->struct_id = same_cursor ? typed_struct_id_common_merge(dest->struct_id, source->struct_id) : AMIGA_OS_STRUCT_ID_NONE;
    if (!same_cursor || dest->output != source->output) dest->output = NULL;
    dest->array_element_count = dest->array_element_index = 0U;
    if (!same_cursor) dest->byte_cursor = 0;
    TYPED_FORGET_CURRENT_SOURCE_POINTER(dest);
    dest->address_value_candidate_overflow |= source->address_value_candidate_overflow;
    if (typed_must_candidates_merge(&dest->raw_long_value_known, &dest->raw_long_candidate_count,
        &dest->raw_long_value, dest->raw_long_candidates, source->raw_long_value_known,
        source->raw_long_candidate_count, source->raw_long_value, source->raw_long_candidates) ==
        M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW) typed_stored_value_mark_address_value_candidate_overflow(dest);
    typed_provenance_merge(&dest->provenance, &source->provenance);
    typed_stored_value_update_known(dest);
    if (!dest->known && !dest->address_value_candidate_overflow) typed_stored_value_clear(dest);
    return !typed_stored_values_equal(dest, &old_value);
  }
  if (dest->output != source->output) dest->output = NULL;
  dest->address_value_candidate_overflow |= source->address_value_candidate_overflow;
  typed_provenance_merge(&dest->provenance, &source->provenance);
  dest->struct_id = typed_struct_id_common_merge(dest->struct_id, source->struct_id);
  if (dest->struct_id != old_value.struct_id || dest->struct_id != source->struct_id ||
      dest->array_element_count != source->array_element_count) {
    dest->array_element_count = dest->array_element_index = 0U;
  }
  if (typed_must_candidates_merge(&dest->pointer_value_known, &dest->pointer_candidate_count,
      &dest->pointer_value, dest->pointer_candidates, source->pointer_value_known,
      source->pointer_candidate_count, source->pointer_value, source->pointer_candidates) ==
      M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW) {
    dest->pointer_value_known = 0U;
    dest->pointer_value = 0U;
    dest->pointer_candidate_count = 0U;
    dest->address_value_candidate_overflow = 1U;
  }
  if (typed_must_candidates_merge(&dest->raw_long_value_known, &dest->raw_long_candidate_count,
      &dest->raw_long_value, dest->raw_long_candidates, source->raw_long_value_known,
      source->raw_long_candidate_count, source->raw_long_value, source->raw_long_candidates) ==
      M68K_RENDER_POINTER_CANDIDATE_MERGE_OVERFLOW) {
    dest->raw_long_value_known = 0U;
    dest->raw_long_value = 0U;
    dest->raw_long_candidate_count = 0U;
    dest->address_value_candidate_overflow = 1U;
  }
  if (dest->address_value_candidate_overflow != 0U) {
    typed_stored_value_mark_address_value_candidate_overflow(dest);
  }
  if (dest->output != NULL && dest->struct_id != AMIGA_OS_STRUCT_ID_NONE &&
      dest->output->struct_id != dest->struct_id) {
    dest->output = NULL;
  }
  typed_stored_value_update_known(dest);
  return !typed_stored_values_equal(dest, &old_value);
}

static int typed_stored_value_merge(M68kRenderTypedStoredValue *dest, const M68kRenderTypedStoredValue *source) {
  M68kRenderTypedStoredValue old, payload;
  uint32_t id;
  if (!dest || !source) return 0;
  if (!dest->entry_value_id && !source->entry_value_id) return typed_stored_value_merge_payload(dest, source);
  old = *dest; payload = *source;
  id = dest->entry_value_id == source->entry_value_id ? dest->entry_value_id : 0U;
  dest->entry_value_id = payload.entry_value_id = 0U;
  (void)typed_stored_value_merge_payload(dest, &payload);
  dest->entry_value_id = id;
  return !typed_stored_values_equal(dest, &old);
}

#undef TYPED_FORGET_CURRENT_SOURCE_POINTER

static int typed_state_merge_stack_slots(M68kRenderTypedState *dest, const M68kRenderTypedState *source) {
  size_t dest_index;
  int changed = 0;
  if (dest == NULL || source == NULL) return 0;
  for (dest_index = 0U; dest_index < dest->stack_slot_count;) {
    M68kRenderTypedStackSlot *dest_slot = &dest->stack_slots[dest_index];
    const M68kRenderTypedStackSlot *source_slot = NULL;
    size_t source_index;
    for (source_index = 0U; source_index < source->stack_slot_count; ++source_index) {
      if (source->stack_slots[source_index].known != 0U &&
          source->stack_slots[source_index].caller_save_temporary == dest_slot->caller_save_temporary &&
          source->stack_slots[source_index].abi_stack_convention == dest_slot->abi_stack_convention &&
          source->stack_slots[source_index].displacement == dest_slot->displacement) {
        source_slot = &source->stack_slots[source_index];
        break;
      }
    }
    if (source_slot == NULL || !typed_memory_bases_equal(&dest_slot->memory_base, &source_slot->memory_base) ||
        typed_stored_value_merge(&dest_slot->value, &source_slot->value) ||
        (!typed_stored_value_has_useful_info(&dest_slot->value) && dest_slot->memory_base.known == 0U &&
         dest_slot->memory_base.pointer_table_known == 0U)) {
      if (source_slot == NULL || (!typed_stored_value_has_useful_info(&dest_slot->value) &&
          dest_slot->memory_base.known == 0U && dest_slot->memory_base.pointer_table_known == 0U)) {
        dest->stack_slots[dest_index] = dest->stack_slots[dest->stack_slot_count - 1U];
        --dest->stack_slot_count;
        changed = 1;
        continue;
      }
      changed = 1;
    }
    ++dest_index;
  }
  return changed;
}

static int typed_state_merge_base_slots(M68kRenderTypedState *dest, const M68kRenderTypedState *source) {
  size_t dest_index;
  int changed = 0;
  if (dest == NULL || source == NULL) return 0;
  for (dest_index = 0U; dest_index < dest->base_slot_count;) {
    M68kRenderTypedBaseSlot *dest_slot = &dest->base_slots[dest_index];
    const M68kRenderTypedBaseSlot *source_slot = dest_slot->storage_id != 0U ?
      typed_state_absolute_cell(source, dest_slot->storage_id) :
      typed_state_base_slot_entry(source, dest_slot->base_reg, dest_slot->displacement);
    if (source_slot == NULL || typed_stored_value_merge(&dest_slot->value, &source_slot->value) ||
        !typed_stored_value_has_useful_info(&dest_slot->value)) {
      if (source_slot == NULL || !typed_stored_value_has_useful_info(&dest_slot->value)) {
        dest->base_slots[dest_index] = dest->base_slots[dest->base_slot_count - 1U];
        --dest->base_slot_count;
        changed = 1;
        continue;
      }
      changed = 1;
    }
    ++dest_index;
  }
  return changed;
}

static int typed_state_merge_field_slots(M68kRenderTypedState *dest, const M68kRenderTypedState *source) {
  size_t dest_index;
  int changed = 0;
  if (dest == NULL || source == NULL) return 0;
  for (dest_index = 0U; dest_index < dest->field_slot_count;) {
    M68kRenderTypedFieldSlot *dest_slot = &dest->field_slots[dest_index];
    const M68kRenderTypedFieldSlot *source_slot = typed_state_field_slot_entry(source, dest_slot->base_reg,
      dest_slot->struct_id, dest_slot->displacement);
    if (source_slot == NULL || typed_stored_value_merge(&dest_slot->value, &source_slot->value) ||
        !typed_stored_value_has_useful_info(&dest_slot->value)) {
      if (source_slot == NULL || !typed_stored_value_has_useful_info(&dest_slot->value)) {
        dest->field_slots[dest_index] = dest->field_slots[dest->field_slot_count - 1U];
        --dest->field_slot_count;
        changed = 1;
        continue;
      }
      changed = 1;
    }
    ++dest_index;
  }
  return changed;
}


static int typed_state_merge_into(M68kRenderTypedState *dest, const M68kRenderTypedState *source) {
  size_t index;
  int changed = 0;
  if (dest == NULL || source == NULL) return 0;
  if (source->absolute_memory_written && !dest->absolute_memory_written) {
    dest->absolute_memory_written = 1U; changed = 1;
  }
  for (index = 0U; index < 8U; ++index) {
    M68kRenderTypedAppAddressValue old_data_app = dest->data_app_addr_regs[index];
    M68kRenderTypedAppAddressValue old_app = dest->app_addr_regs[index];
    M68kRenderTypedMemoryBaseValue old_data_memory_base = dest->data_memory_base_regs[index];
    M68kRenderTypedMemoryBaseValue old_memory_base = dest->memory_base_regs[index];
    M68kRenderIoRequestSetup old_io_request_setup = dest->io_request_setups[index];
    changed |= typed_reg_merge(&dest->data_regs[index], &source->data_regs[index]);
    changed |= typed_reg_merge(&dest->addr_regs[index], &source->addr_regs[index]);
    if (dest->data_app_addr_regs[index].known == 0U || source->data_app_addr_regs[index].known == 0U ||
        dest->data_app_addr_regs[index].displacement != source->data_app_addr_regs[index].displacement) {
      dest->data_app_addr_regs[index].known = 0U;
      dest->data_app_addr_regs[index].displacement = 0;
      dest->data_app_addr_regs[index].base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
    } else if (dest->data_app_addr_regs[index].base_evidence_kind != source->data_app_addr_regs[index].base_evidence_kind) {
      dest->data_app_addr_regs[index].base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
    }
    if (!typed_app_addresses_equal(&old_data_app, &dest->data_app_addr_regs[index])) changed = 1;
    if (dest->app_addr_regs[index].known == 0U || source->app_addr_regs[index].known == 0U ||
        dest->app_addr_regs[index].displacement != source->app_addr_regs[index].displacement) {
      dest->app_addr_regs[index].known = 0U;
      dest->app_addr_regs[index].displacement = 0;
      dest->app_addr_regs[index].base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
    } else if (dest->app_addr_regs[index].base_evidence_kind != source->app_addr_regs[index].base_evidence_kind) {
      dest->app_addr_regs[index].base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
    }
    if (!typed_app_addresses_equal(&old_app, &dest->app_addr_regs[index])) changed = 1;
    if (dest->data_memory_base_regs[index].known == 0U || source->data_memory_base_regs[index].known == 0U ||
        dest->data_memory_base_regs[index].section_index != source->data_memory_base_regs[index].section_index ||
        dest->data_memory_base_regs[index].offset != source->data_memory_base_regs[index].offset) {
      dest->data_memory_base_regs[index].known = 0U;
      dest->data_memory_base_regs[index].section_index = 0U;
      dest->data_memory_base_regs[index].offset = 0U;
      dest->data_memory_base_regs[index].affine_known = 0U;
      dest->data_memory_base_regs[index].affine_origin_section_index = 0U;
      dest->data_memory_base_regs[index].affine_origin_offset = 0U;
      dest->data_memory_base_regs[index].affine_signed_addend = 0;
    }
    if (dest->data_memory_base_regs[index].pointer_table_known == 0U ||
        source->data_memory_base_regs[index].pointer_table_known == 0U ||
        dest->data_memory_base_regs[index].pointer_table_struct_id !=
          source->data_memory_base_regs[index].pointer_table_struct_id ||
        dest->data_memory_base_regs[index].pointer_table_section_index !=
          source->data_memory_base_regs[index].pointer_table_section_index ||
        dest->data_memory_base_regs[index].pointer_table_offset !=
          source->data_memory_base_regs[index].pointer_table_offset ||
        dest->data_memory_base_regs[index].pointer_table_size !=
          source->data_memory_base_regs[index].pointer_table_size) {
      dest->data_memory_base_regs[index].pointer_table_known = 0U;
      dest->data_memory_base_regs[index].pointer_table_struct_id = AMIGA_OS_STRUCT_ID_NONE;
      dest->data_memory_base_regs[index].pointer_table_section_index = 0U;
      dest->data_memory_base_regs[index].pointer_table_offset = 0U;
      dest->data_memory_base_regs[index].pointer_table_size = 0U;
    }
    if (!typed_memory_bases_equal(&old_data_memory_base, &dest->data_memory_base_regs[index])) changed = 1;
    if (dest->memory_base_regs[index].known == 0U || source->memory_base_regs[index].known == 0U ||
        dest->memory_base_regs[index].section_index != source->memory_base_regs[index].section_index ||
        dest->memory_base_regs[index].offset != source->memory_base_regs[index].offset) {
      dest->memory_base_regs[index].known = 0U;
      dest->memory_base_regs[index].section_index = 0U;
      dest->memory_base_regs[index].offset = 0U;
      dest->memory_base_regs[index].affine_known = 0U;
      dest->memory_base_regs[index].affine_origin_section_index = 0U;
      dest->memory_base_regs[index].affine_origin_offset = 0U;
      dest->memory_base_regs[index].affine_signed_addend = 0;
    }
    if (dest->memory_base_regs[index].pointer_table_known == 0U ||
        source->memory_base_regs[index].pointer_table_known == 0U ||
        dest->memory_base_regs[index].pointer_table_struct_id != source->memory_base_regs[index].pointer_table_struct_id ||
        dest->memory_base_regs[index].pointer_table_section_index !=
          source->memory_base_regs[index].pointer_table_section_index ||
        dest->memory_base_regs[index].pointer_table_offset != source->memory_base_regs[index].pointer_table_offset ||
        dest->memory_base_regs[index].pointer_table_size != source->memory_base_regs[index].pointer_table_size) {
      dest->memory_base_regs[index].pointer_table_known = 0U;
      dest->memory_base_regs[index].pointer_table_struct_id = AMIGA_OS_STRUCT_ID_NONE;
      dest->memory_base_regs[index].pointer_table_section_index = 0U;
      dest->memory_base_regs[index].pointer_table_offset = 0U;
      dest->memory_base_regs[index].pointer_table_size = 0U;
    }
    if (!typed_memory_bases_equal(&old_memory_base, &dest->memory_base_regs[index])) changed = 1;
    if (!typed_io_request_setups_equal(&dest->io_request_setups[index], &source->io_request_setups[index])) {
      memset(&dest->io_request_setups[index], 0, sizeof(dest->io_request_setups[index]));
    }
    if (!typed_io_request_setups_equal(&old_io_request_setup, &dest->io_request_setups[index])) changed = 1;
  }
  changed |= typed_addr_alias_meet(dest, source);
  if (typed_state_merge_stack_slots(dest, source)) changed = 1;
  if (typed_state_merge_base_slots(dest, source)) changed = 1;
  if (typed_state_merge_field_slots(dest, source)) changed = 1;
  return changed;
}

static void platform_state_merge_register_name(uint32_t *dest_known, uint8_t reg_index, char *dest_name,
    size_t dest_name_size, uint32_t source_known, const char *source_name, int *io_changed) {
  if (dest_known == NULL || dest_name == NULL || source_name == NULL || io_changed == NULL) return;
  if (!m68k_bitset_u32_has(*dest_known, reg_index) || !m68k_bitset_u32_has(source_known, reg_index) ||
      strcmp(dest_name, source_name) != 0) {
    if (m68k_bitset_u32_has(*dest_known, reg_index) || dest_name[0] != '\0') *io_changed = 1;
    m68k_bitset_u32_clear(dest_known, reg_index);
    if (dest_name_size != 0U) dest_name[0] = '\0';
  }
}

static void platform_state_merge_register_base(uint32_t *dest_known, uint8_t reg_index, uint16_t *dest_base_id,
    char *dest_name, size_t dest_name_size, uint32_t source_known, uint16_t source_base_id,
    const char *source_name, int *io_changed) {
  if (dest_known == NULL || dest_base_id == NULL || dest_name == NULL || source_name == NULL ||
      io_changed == NULL) {
    return;
  }
  if (!m68k_bitset_u32_has(*dest_known, reg_index) || !m68k_bitset_u32_has(source_known, reg_index) ||
      *dest_base_id != source_base_id) {
    if (m68k_bitset_u32_has(*dest_known, reg_index) || *dest_base_id != 0U || dest_name[0] != '\0')
      *io_changed = 1;
    m68k_bitset_u32_clear(dest_known, reg_index);
    *dest_base_id = 0U;
    if (dest_name_size != 0U) dest_name[0] = '\0';
    return;
  }
  platform_state_merge_register_name(dest_known, reg_index, dest_name, dest_name_size, source_known, source_name,
    io_changed);
}

static void platform_state_merge_register_id(uint32_t *dest_known, uint8_t reg_index, uint16_t *dest_id, uint32_t source_known,
    uint16_t source_id, int *io_changed) {
  if (dest_known == NULL || dest_id == NULL || io_changed == NULL) return;
  if (!m68k_bitset_u32_has(*dest_known, reg_index) || !m68k_bitset_u32_has(source_known, reg_index) ||
      *dest_id != source_id) {
    if (m68k_bitset_u32_has(*dest_known, reg_index) || *dest_id != 0U) *io_changed = 1;
    m68k_bitset_u32_clear(dest_known, reg_index);
    *dest_id = 0U;
  }
}

static int hardware_word_set_add(M68kHardwareWordSet *set, uint16_t value) {
  uint8_t i, j;
  for (i = 0U; i < set->count && set->values[i] < value; ++i) {}
  if (i < set->count && set->values[i] == value) return 1;
  if (set->count == M68K_HARDWARE_VALUE_LIMIT) return 0;
  for (j = set->count; j > i; --j) set->values[j] = set->values[j - 1U];
  set->values[i] = value;
  ++set->count;
  return 1;
}

static void hardware_word_set_merge(M68kHardwareWordSet *dest, const M68kHardwareWordSet *source) {
  uint8_t i;
  if (dest->count == 0U || source->count == 0U) goto unknown;
  dest->requires_input_contract |= source->requires_input_contract;
  for (i = 0U; i < source->count; ++i)
    if (!hardware_word_set_add(dest, source->values[i])) goto unknown;
  return;
unknown:
  memset(dest, 0, sizeof(*dest));
}

static M68kHardwareWordSet hardware_operand_word_values(const M68kRenderPlatformState *state,
    const M68kOperandIR *operand) {
  M68kHardwareWordSet result = {0};
  uint32_t immediate;
  uint8_t reg;
  if (m68k_ir_operand_immediate_value(operand, &immediate)) {
    result.count = 1U;
    result.values[0] = (uint16_t)immediate;
  } else if (operand_is_data_register_local(operand, &reg) && reg < 8U) result = state->word_values[reg];
  return result;
}

static M68kHardwareRelativeBase hardware_relative_register(const M68kRenderPlatformState *state, uint8_t reg) {
  M68kHardwareRelativeBase result = state->relative_hardware[reg];
  if (result.offsets.count == 0U && m68k_bitset_u32_has(state->address_hardware_base_known, reg)) {
    result.base_id = state->address_hardware_base_id[reg];
    result.offsets.count = 1U;
    result.offsets.values[0] = 0U;
  }
  return result;
}

/* This domain tracks low WORDs only. It cannot manufacture full data-register
 * addresses. Unmodelled writes, memory loads, overflow and opaque calls are top. */
static void hardware_relative_transfer(M68kRenderPlatformState *state, const M68kRenderPlatformState *before,
    const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *meta = m68k_sim_metadata_for_instruction(instruction);
  uint8_t i, reg, dest;
  M68kHardwareWordSet source;
  if (meta == NULL) {
    memset(state->word_values, 0, sizeof(state->word_values));
    memset(state->relative_hardware, 0, sizeof(state->relative_hardware));
    return;
  }
  if (meta->flow_kind == M68K_SIM_FLOW_CALL) {
    memset(state->word_values, 0, sizeof(state->word_values));
    memset(state->relative_hardware, 0, sizeof(state->relative_hardware));
    return;
  }
  for (reg = 0U; reg < 8U; ++reg) {
    state->word_values[reg] = before->word_values[reg];
    state->relative_hardware[reg] = hardware_relative_register(before, reg);
  }
  for (i = 0U; i < instruction->operand_count; ++i) {
    const M68kOperandIR *operand = &instruction->operands[i];
    if (meta->operand_access_kinds[i] == M68K_SIM_ACCESS_REGISTER_WRITE ||
        meta->operand_access_kinds[i] == M68K_SIM_ACCESS_MEMORY_WRITE) {
      if (operand_is_data_register_local(operand, &reg))
        memset(&state->word_values[reg], 0, sizeof(state->word_values[reg]));
      if (operand_address_register_index_local(operand, &reg))
        memset(&state->relative_hardware[reg], 0, sizeof(state->relative_hardware[reg]));
    }
    if ((m68k_instruction_operand_decoded_ea_shape(operand) == M68K_SIM_EA_SHAPE_POSTINCREMENT ||
         m68k_instruction_operand_decoded_ea_shape(operand) == M68K_SIM_EA_SHAPE_PREDECREMENT) &&
        operand->value.ea_reg < 8U)
      memset(&state->relative_hardware[operand->value.ea_reg], 0,
        sizeof(state->relative_hardware[operand->value.ea_reg]));
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count == 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    for (reg = 0U; reg < 8U; ++reg) {
      if (reglist_contains_data_register_local(&instruction->operands[1], reg))
        memset(&state->word_values[reg], 0, sizeof(state->word_values[reg]));
      if (reglist_contains_address_register_local(&instruction->operands[1], reg))
        memset(&state->relative_hardware[reg], 0, sizeof(state->relative_hardware[reg]));
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_DBF &&
      operand_is_data_register_local(&instruction->operands[0], &reg)) {
    M68kHardwareWordSet result = {0};
    result.requires_input_contract = before->word_values[reg].requires_input_contract;
    for (i = 0U; i < before->word_values[reg].count; ++i)
      (void)hardware_word_set_add(&result, (uint16_t)(before->word_values[reg].values[i] - 1U));
    state->word_values[reg] = result;
    return;
  }
  if (instruction->operand_count < 2U) return;
  /* Full address construction is distinct from reading a hardware register.
   * Retain an interior hardware address as base+offset, never as base zero. */
  if (operand_address_register_index_local(&instruction->operands[1], &dest)) {
    uint32_t address = 0U, hardware_offset = 0U;
    uint16_t base_id = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
    int address_value =
      (meta->operand_access_kinds[0] == M68K_SIM_ACCESS_COMPUTE_ADDRESS &&
       operand_absolute_offset_local(&instruction->operands[0], &address)) ||
      (instruction->size_suffix == 'l' &&
       m68k_ir_operand_immediate_value(&instruction->operands[0], &address));
    if (address_value && platform_facts_v2_hardware_base_offset_for_address(
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, address, &base_id, &hardware_offset) &&
        base_id != PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE && hardware_offset <= INT16_MAX) {
      state->relative_hardware[dest].base_id = base_id;
      state->relative_hardware[dest].offsets.count = 1U;
      state->relative_hardware[dest].offsets.values[0] = (uint16_t)hardware_offset;
      return;
    }
  }
  source = hardware_operand_word_values(before, &instruction->operands[0]);
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDA && instruction->size_suffix == 'w' &&
      operand_address_register_index_local(&instruction->operands[1], &dest)) {
    M68kHardwareRelativeBase base = hardware_relative_register(before, dest), result;
    uint8_t j;
    memset(&result, 0, sizeof(result));
    result.base_id = base.base_id;
    result.offsets.requires_input_contract = base.offsets.requires_input_contract | source.requires_input_contract;
    if (source.count == 0U || base.offsets.count == 0U) return;
    for (i = 0U; i < base.offsets.count; ++i) for (j = 0U; j < source.count; ++j) {
      int32_t offset = (int32_t)base.offsets.values[i] + (int16_t)source.values[j];
      if (offset < 0 || offset > INT16_MAX || !hardware_word_set_add(&result.offsets, (uint16_t)offset)) return;
    }
    state->relative_hardware[dest] = result;
  } else if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA ||
              instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE) && instruction->size_suffix == 'l' &&
      operand_address_register_index_local(&instruction->operands[1], &dest) &&
      operand_address_register_index_local(&instruction->operands[0], &reg)) {
    state->relative_hardware[dest] = hardware_relative_register(before, reg);
  } else if (operand_is_data_register_local(&instruction->operands[1], &dest)) {
    M68kHardwareWordSet result = {0};
    result.requires_input_contract = source.requires_input_contract | before->word_values[dest].requires_input_contract;
    if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEQ ||
        (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE &&
         (instruction->size_suffix == 'w' || instruction->size_suffix == 'l'))) {
      state->word_values[dest] = source;
    } else if ((meta->operation_type == M68K_SIM_OP_ADD || meta->operation_type == M68K_SIM_OP_SUB) &&
        (instruction->size_suffix == 'w' || instruction->size_suffix == 'l')) {
      if (!source.count) return;
      for (i = 0U; i < before->word_values[dest].count; ++i)
        for (uint8_t j = 0U; j < source.count; ++j) {
          uint16_t value = meta->operation_type == M68K_SIM_OP_ADD
            ? (uint16_t)(before->word_values[dest].values[i] + source.values[j])
            : (uint16_t)(before->word_values[dest].values[i] - source.values[j]);
          if (!hardware_word_set_add(&result, value)) return;
        }
      state->word_values[dest] = result;
    } else if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_LSL ||
                instruction->mnemonic_id == M68K_ASM_MNEMONIC_MULU) &&
        instruction->size_suffix == 'w' && source.count == 1U) {
      uint16_t amount = source.values[0];
      if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LSL && amount > 15U) return;
      for (i = 0U; i < before->word_values[dest].count; ++i) {
        uint32_t value = before->word_values[dest].values[i];
        value = instruction->mnemonic_id == M68K_ASM_MNEMONIC_LSL ? value << amount : value * amount;
        if (!hardware_word_set_add(&result, (uint16_t)value)) return;
      }
      state->word_values[dest] = result;
    }
  }
  for (reg = 0U; reg < 8U; ++reg)
    if (state->relative_hardware[reg].offsets.count == 0U)
      state->relative_hardware[reg] = hardware_relative_register(state, reg);
}

void hardware_relative_transfer_linear(M68kRenderPlatformState *state,
    const M68kRenderPlatformState *before, const M68kInstructionIR *instruction) {
  const M68kSimFormMetadata *meta = m68k_sim_metadata_for_instruction(instruction);
  if (platform_instruction_has_terminal_state_flow(instruction) ||
      (meta != NULL && meta->flow_kind == M68K_SIM_FLOW_BRANCH && !meta->flow_conditional)) {
    memset(state->word_values, 0, sizeof(state->word_values));
    memset(state->relative_hardware, 0, sizeof(state->relative_hardware));
    return;
  }
  hardware_relative_transfer(state, before, instruction);
}

static void hardware_relative_apply_policy_inputs(M68kRenderPlatformState *state,
    const M68kAnalysisPolicy *policy, uint32_t section_index, uint32_t offset) {
  {
    uint16_t seed_index;
    for (seed_index = 0U; policy != NULL && seed_index < policy->register_seed_count; ++seed_index) {
      const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[seed_index];
      M68kHardwareRelativeBase *relative;
      uint8_t value_index;
      if (!seed->has_entry_offset || seed->entry_offset != offset ||
          (seed->has_section_index && seed->section_index != section_index)) continue;
      if (seed->reg_index >= 8U) continue;
      if (seed->kind != M68K_ANALYSIS_REGISTER_SEED_HARDWARE_INDEXED) {
        if (seed->reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS)
          memset(&state->relative_hardware[seed->reg_index], 0, sizeof(state->relative_hardware[seed->reg_index]));
        if (seed->reg_kind == M68K_ANALYSIS_REGISTER_DATA)
          memset(&state->word_values[seed->reg_index], 0, sizeof(state->word_values[seed->reg_index]));
        continue;
      }
      if (seed->reg_kind != M68K_ANALYSIS_REGISTER_ADDRESS || seed->hardware_index_register >= 8U ||
          seed->hardware_index_count == 0U || seed->hardware_index_count > 8U) continue;
      relative = &state->relative_hardware[seed->reg_index];
      memset(relative, 0, sizeof(*relative));
      memset(&state->word_values[seed->hardware_index_register], 0,
        sizeof(state->word_values[seed->hardware_index_register]));
      if (!platform_facts_v2_hardware_base_id_for_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
          seed->name, &relative->base_id)) continue;
      relative->offsets.requires_input_contract = 1U;
      state->word_values[seed->hardware_index_register].requires_input_contract = 1U;
      for (value_index = 0U; value_index < seed->hardware_index_count; ++value_index) {
        (void)hardware_word_set_add(&relative->offsets,
          seed->hardware_index_values[value_index] * seed->hardware_stride);
        (void)hardware_word_set_add(&state->word_values[seed->hardware_index_register],
          seed->hardware_index_values[value_index]);
      }
      m68k_bitset_u32_clear(&state->address_hardware_base_known, seed->reg_index);
      state->address_hardware_base_id[seed->reg_index] = 0U;
    }
  }
}

static int platform_state_merge_into(M68kRenderPlatformState *dest, const M68kRenderPlatformState *source) {
  M68kRenderPlatformState old_state;
  size_t index;
  int changed = 0;
  if (dest == NULL || source == NULL) return 0;
  old_state = *dest;
  for (index = 0U; index < 8U; ++index) {
    hardware_word_set_merge(&dest->word_values[index], &source->word_values[index]);
    if (dest->relative_hardware[index].base_id != source->relative_hardware[index].base_id)
      memset(&dest->relative_hardware[index], 0, sizeof(dest->relative_hardware[index]));
    else {
      hardware_word_set_merge(&dest->relative_hardware[index].offsets, &source->relative_hardware[index].offsets);
      if (dest->relative_hardware[index].offsets.count == 0U) dest->relative_hardware[index].base_id = 0U;
    }
    platform_state_merge_register_base(&dest->data_base_known, (uint8_t)index, &dest->data_base_id[index],
      dest->data_base_library[index], sizeof(dest->data_base_library[index]), source->data_base_known,
      source->data_base_id[index], source->data_base_library[index], &changed);
    platform_state_merge_register_base(&dest->address_base_known, (uint8_t)index, &dest->address_base_id[index],
      dest->address_base_library[index], sizeof(dest->address_base_library[index]),
      source->address_base_known, source->address_base_id[index], source->address_base_library[index],
      &changed);
    platform_state_merge_register_id(&dest->address_hardware_base_known, (uint8_t)index,
      &dest->address_hardware_base_id[index], source->address_hardware_base_known,
      source->address_hardware_base_id[index], &changed);
    platform_state_merge_register_id(&dest->data_hardware_base_known, (uint8_t)index,
      &dest->data_hardware_base_id[index], source->data_hardware_base_known,
      source->data_hardware_base_id[index], &changed);
    platform_state_merge_register_name(&dest->data_layout_base_known, (uint8_t)index,
      dest->data_layout_base_symbol[index], sizeof(dest->data_layout_base_symbol[index]),
      source->data_layout_base_known,
      source->data_layout_base_symbol[index], &changed);
    platform_state_merge_register_name(&dest->address_layout_base_known, (uint8_t)index,
      dest->address_layout_base_symbol[index], sizeof(dest->address_layout_base_symbol[index]),
      source->address_layout_base_known, source->address_layout_base_symbol[index], &changed);
    if (m68k_bitset_u32_has(dest->data_app_base_known, (uint8_t)index) &&
        !m68k_bitset_u32_has(source->data_app_base_known, (uint8_t)index)) {
      m68k_bitset_u32_clear(&dest->data_app_base_known, (uint8_t)index);
    }
    if (m68k_bitset_u32_has(dest->address_app_base_known, (uint8_t)index) &&
        !m68k_bitset_u32_has(source->address_app_base_known, (uint8_t)index)) {
      m68k_bitset_u32_clear(&dest->address_app_base_known, (uint8_t)index);
    }
  }
  for (index = 0U; index < 8U; ++index) {
    if (!m68k_bitset_u32_has(dest->data_lvo_known, (uint8_t)index) ||
        !m68k_bitset_u32_has(source->data_lvo_known, (uint8_t)index) ||
        dest->data_lvo[index] != source->data_lvo[index]) {
      m68k_bitset_u32_clear(&dest->data_lvo_known, (uint8_t)index);
      dest->data_lvo[index] = 0;
    }
  }
  return changed || !platform_states_equal(dest, &old_state);
}

static int typed_flow_merge_input(M68kRenderTypedFlowNode *node, const M68kRenderTypedState *typed_state,
    const M68kRenderPlatformState *platform_state) {
  int changed = 0;
  if (node == NULL || typed_state == NULL || platform_state == NULL) return 0;
  if (node->has_in == 0U) {
    node->typed_in = *typed_state;
    node->platform_in = *platform_state;
    node->has_in = 1U;
    return 1;
  }
  if (typed_state_merge_into(&node->typed_in, typed_state)) changed = 1;
  if (platform_state_merge_into(&node->platform_in, platform_state)) changed = 1;
  return changed;
}

static int typed_flow_successors_for_candidate(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const size_t *node_by_offset, uint32_t node_by_offset_count, const M68kDecodeCandidate *candidate,
    size_t *out_successors, size_t successor_capacity) {
  size_t count = 0U;
  size_t target_index;
  uint32_t next_offset;
  int has_fallthrough;
  if (section == NULL || accepted_start == NULL || node_by_offset == NULL || candidate == NULL ||
      out_successors == NULL) {
    return 0;
  }
  {
    size_t target_section;
    uint32_t target_offset;
    if (typed_flow_local_absolute_jump_target(lookup, candidate, &target_section, &target_offset)) {
      if (target_section == section->section_index && target_offset < node_by_offset_count &&
          node_by_offset[target_offset] != SIZE_MAX && successor_capacity != 0U) {
        out_successors[0] = node_by_offset[target_offset]; return 1;
      }
      return 0;
    }
  }
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if ((target->kind != M68K_DECODE_TARGET_BRANCH && target->kind != M68K_DECODE_TARGET_JUMP) ||
        !target->has_section || target->section_index != section->section_index ||
        target->offset >= node_by_offset_count || node_by_offset[target->offset] == SIZE_MAX) {
      continue;
    }
    if (count < successor_capacity) out_successors[count++] = node_by_offset[target->offset];
  }
  has_fallthrough = render_cfg_candidate_has_fallthrough(candidate);
  next_offset = candidate->offset + candidate->byte_count;
  if (has_fallthrough && next_offset < node_by_offset_count && accepted_start_at(section, accepted_start, next_offset) &&
      node_by_offset[next_offset] != SIZE_MAX && count < successor_capacity) {
    out_successors[count++] = node_by_offset[next_offset];
  }
  return (int)count;
}

typedef struct M68kTypedFlowCallResolution {
  const AmigaOsLibraryVectorInfo *vector;
  uint8_t output_reg_known;
  uint8_t output_reg_kind;
  uint8_t output_reg_index;
} M68kTypedFlowCallResolution;

static void typed_flow_call_resolution_init(M68kTypedFlowCallResolution *resolution) {
  if (resolution == NULL) return;
  memset(resolution, 0, sizeof(*resolution));
}

static int typed_flow_reg_matches_output(const M68kRenderTypedRegValue *value,
    const AmigaOsCallOutputInfo *output) {
  if (value == NULL || output == NULL || value->known == 0U) return 0;
  if (value->output == output) return 1;
  return output->struct_id != AMIGA_OS_STRUCT_ID_NONE && value->struct_id == output->struct_id;
}

static int typed_flow_choose_helper_output_reg(const M68kRenderTypedState *state,
    const AmigaOsCallOutputInfo *output, uint8_t *out_reg_kind, uint8_t *out_reg_index) {
  uint8_t reg;
  if (out_reg_kind != NULL) *out_reg_kind = 0U;
  if (out_reg_index != NULL) *out_reg_index = 0U;
  if (state == NULL || output == NULL) return 0;
  for (reg = 0U; reg < 8U; ++reg) {
    if (typed_flow_reg_matches_output(&state->addr_regs[reg], output)) {
      if (out_reg_kind != NULL) *out_reg_kind = AMIGA_OS_REGISTER_ADDRESS;
      if (out_reg_index != NULL) *out_reg_index = reg;
      return 1;
    }
  }
  for (reg = 0U; reg < 8U; ++reg) {
    if (typed_flow_reg_matches_output(&state->data_regs[reg], output)) {
      if (out_reg_kind != NULL) *out_reg_kind = AMIGA_OS_REGISTER_DATA;
      if (out_reg_index != NULL) *out_reg_index = reg;
      return 1;
    }
  }
  return 0;
}

static int typed_flow_infer_local_helper_output_reg_at(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index, uint32_t helper_offset,
    const AmigaOsLibraryVectorInfo *expected_vector, unsigned depth, uint8_t *out_reg_kind,
    uint8_t *out_reg_index) {
  const M68kDecodeSectionIR *section;
  M68kRenderTypedState typed_state;
  M68kRenderPlatformState platform_state;
  uint32_t cursor;
  if (out_reg_kind != NULL) *out_reg_kind = 0U;
  if (out_reg_index != NULL) *out_reg_index = 0U;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || expected_vector == NULL || depth > 4U ||
      section_index >= decode->section_count) {
    return 0;
  }
  section = &decode->sections[section_index];
  if (!accepted_start_at(section, accepted_start[section_index], helper_offset)) return 0;
  typed_state_clear_all(&typed_state);
  memset(&platform_state, 0, sizeof(platform_state));
  cursor = helper_offset;
  while (cursor < section->size && cursor - helper_offset < 256U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const AmigaOsLibraryVectorInfo *platform_vector;
    const AmigaOsLibraryVectorInfo *immediate_vector;
    const AmigaOsLibraryVectorInfo *wrapper_vector;
    const AmigaOsLibraryVectorInfo *direct_vector;
    const AmigaOsLibraryVectorInfo *local_helper_vector;
    const AmigaOsLibraryVectorInfo *vector;
    M68kTypedFlowCallResolution nested_resolution;
    M68kAnalysisFunctionSummary generated_platform_summary;
    const M68kAnalysisFunctionSummary *call_summary = NULL;
    M68kRenderTypedState call_input_state;
    if (!accepted_start_at(section, accepted_start[section_index], cursor)) break;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    platform_state_apply_policy_register_seeds(&platform_state, lookup->policy, section->section_index,
      candidate->offset);
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
    if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_RTS) {
      return typed_flow_choose_helper_output_reg(&typed_state, &expected_vector->output,
        out_reg_kind, out_reg_index);
    }
    platform_vector = attach_amiga_lvo_symbol_if_known(&platform_state, &instruction);
    immediate_vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[section_index],
      candidate, &instruction);
    wrapper_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &platform_state, section, candidate);
    direct_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
      section->section_index, candidate);
    local_helper_vector = (wrapper_vector == NULL && direct_vector == NULL)
      ? resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start, section->section_index, candidate)
      : NULL;
    vector = platform_vector != NULL ? platform_vector :
      (direct_vector != NULL ? direct_vector :
      (wrapper_vector != NULL ? wrapper_vector :
      (immediate_vector != NULL ? immediate_vector : local_helper_vector)));
    typed_flow_call_resolution_init(&nested_resolution);
    if (local_helper_vector != NULL) {
      size_t target_section_index = 0U;
      uint32_t target_offset = 0U;
      if (candidate_direct_control_target(lookup, section->section_index, candidate, &target_section_index,
          &target_offset) &&
          typed_flow_infer_local_helper_output_reg_at(lookup, decode, accepted_start, target_section_index,
            target_offset, local_helper_vector, depth + 1U, &nested_resolution.output_reg_kind,
            &nested_resolution.output_reg_index)) {
        nested_resolution.vector = local_helper_vector;
        nested_resolution.output_reg_known = 1U;
      }
    }
    if (vector != NULL &&
        generated_platform_call_summary(lookup->object->platform_backend_kind, vector,
          nested_resolution.output_reg_known, nested_resolution.output_reg_kind, nested_resolution.output_reg_index,
          &generated_platform_summary)) {
      call_summary = &generated_platform_summary;
      call_input_state = typed_state;
    }
    typed_state_update_after_instruction(&typed_state, lookup, &platform_state, section->section_index,
      &instruction, candidate, call_summary, candidate->offset, 0);
    if (call_summary != NULL)
      typed_state_apply_function_summary_results(&typed_state, &call_input_state, lookup, call_summary,
        section->section_index, candidate->offset);
    platform_state_update_data_lvo_after_instruction(&platform_state, &instruction);
    platform_state_update_after_instruction(&platform_state, lookup, &instruction);
    platform_state_note_call_result_after_instruction(&platform_state, &instruction, vector);
    if (!candidate_has_local_helper_summary_fallthrough(candidate))
      break;
    cursor += candidate->byte_count;
  }
  return 0;
}

static const AmigaOsLibraryVectorInfo *typed_flow_resolve_vector(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kRenderPlatformState *platform_state,
    M68kInstructionIR *instruction, M68kTypedFlowCallResolution *resolution) {
  const AmigaOsLibraryVectorInfo *platform_vector;
  const AmigaOsLibraryVectorInfo *immediate_vector;
  const AmigaOsLibraryVectorInfo *wrapper_call_vector;
  const AmigaOsLibraryVectorInfo *direct_wrapper_vector;
  const AmigaOsLibraryVectorInfo *helper_call_vector = NULL;
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  if (resolution != NULL) typed_flow_call_resolution_init(resolution);
  if (lookup == NULL || decode == NULL || accepted_start == NULL || section == NULL || candidate == NULL ||
      platform_state == NULL || instruction == NULL) {
    return NULL;
  }
  platform_vector = attach_amiga_lvo_symbol_if_known(platform_state, instruction);
  immediate_vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[section->section_index],
    candidate, instruction);
  wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, platform_state, section, candidate);
  direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start,
    section->section_index, candidate);
  if (platform_vector == NULL && immediate_vector == NULL && wrapper_call_vector == NULL &&
      direct_wrapper_vector == NULL) {
    helper_call_vector = resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start, section->section_index,
      candidate);
  }
  if (resolution != NULL) {
    resolution->vector = platform_vector != NULL ? platform_vector :
      (direct_wrapper_vector != NULL ? direct_wrapper_vector :
      (wrapper_call_vector != NULL ? wrapper_call_vector :
      (immediate_vector != NULL ? immediate_vector : helper_call_vector)));
    if (helper_call_vector != NULL &&
        candidate_direct_control_target(lookup, section->section_index, candidate, &target_section_index,
          &target_offset) &&
        typed_flow_infer_local_helper_output_reg_at(lookup, decode, accepted_start, target_section_index,
          target_offset, helper_call_vector, 0U, &resolution->output_reg_kind, &resolution->output_reg_index)) {
      resolution->output_reg_known = 1U;
    }
  }
  return platform_vector != NULL ? platform_vector :
    (direct_wrapper_vector != NULL ? direct_wrapper_vector :
    (wrapper_call_vector != NULL ? wrapper_call_vector :
    (immediate_vector != NULL ? immediate_vector : helper_call_vector)));
}

static void analysis_amiga_vector_resolution_init(M68kRenderAmigaVectorResolution *resolution) {
  if (resolution == NULL) return;
  memset(resolution, 0, sizeof(*resolution));
  resolution->chosen_kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_LIBRARY_VECTOR_CALL;
  resolution->chosen_note_kind = M68K_PLATFORM_CALL_NOTE_NONE;
}

void m68k_analysis_render_lookup_resolve_amiga_instruction_platform_vectors(const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *platform_state, const M68kDecodeIR *decode, uint8_t **accepted_start_all,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kDecodeCandidate *candidate,
    M68kInstructionIR *instruction, M68kRenderAmigaVectorResolution *resolution) {
  if (resolution == NULL) return;
  analysis_amiga_vector_resolution_init(resolution);
  if (lookup == NULL || lookup->object == NULL || platform_state == NULL || section == NULL ||
      candidate == NULL || instruction == NULL) {
    return;
  }
  resolution->platform_vector = attach_amiga_lvo_symbol_if_known(platform_state, instruction);
  resolution->immediate_vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start, candidate,
    instruction);
  resolution->wrapper_call_vector = resolve_amiga_indexed_wrapper_call_vector(lookup, platform_state, section,
    candidate);
  resolution->direct_wrapper_vector = resolve_amiga_direct_wrapper_call_vector(lookup, decode, accepted_start_all,
    section->section_index, candidate);
  if (resolution->platform_vector == NULL && resolution->immediate_vector == NULL &&
      resolution->wrapper_call_vector == NULL && resolution->direct_wrapper_vector == NULL) {
    resolution->helper_call_vector = resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start_all,
      section->section_index, candidate);
  }
  resolution->chosen_vector = resolution->platform_vector != NULL ? resolution->platform_vector :
    (resolution->direct_wrapper_vector != NULL ? resolution->direct_wrapper_vector :
    (resolution->wrapper_call_vector != NULL ? resolution->wrapper_call_vector :
    (resolution->immediate_vector != NULL ? resolution->immediate_vector : resolution->helper_call_vector)));
  if (resolution->wrapper_call_vector != NULL) {
    resolution->chosen_kind = PLATFORM_RESOLVED_INDIRECT_AMIGA_INDEXED_LIBRARY_DISPATCH;
    resolution->chosen_note_kind = M68K_PLATFORM_CALL_NOTE_INDEXED_VECTOR;
  } else if (resolution->direct_wrapper_vector != NULL) {
    resolution->chosen_note_kind = M68K_PLATFORM_CALL_NOTE_LOCAL_WRAPPER_SYMBOL;
  } else if (resolution->helper_call_vector != NULL) {
    resolution->chosen_note_kind = M68K_PLATFORM_CALL_NOTE_LOCAL_HELPER_SYMBOL;
  }
}

static int render_lookup_record_hardware_address_uses(M68kRenderLookup *lookup, size_t section_index,
    const M68kRenderPlatformState *state, const M68kInstructionIR *instruction, uint32_t offset) {
  const M68kSimFormMetadata *metadata = m68k_sim_metadata_for_instruction(instruction);
  size_t operand_index;
  if (metadata == NULL) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    M68kPlatformAddressUseIR use;
    M68kRenderHardwareAddressUse *entry;
    const char *symbol = NULL;
    char symbol_buf[96];
    uint32_t address = 0U;
    uint8_t base_reg = 0U;
    int16_t displacement = 0;
    uint8_t access = metadata->operand_access_kinds[operand_index];
    memset(&use, 0, sizeof(use));
    if ((access == M68K_SIM_ACCESS_MEMORY_READ || access == M68K_SIM_ACCESS_MEMORY_WRITE ||
         access == M68K_SIM_ACCESS_COMPUTE_ADDRESS) &&
        operand_is_address_displacement_local(operand, &base_reg, &displacement) && displacement >= 0 &&
        m68k_bitset_u32_has(state->address_hardware_base_known, base_reg) &&
        platform_facts_v2_hardware_base_address(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
          state->address_hardware_base_id[base_reg], &address)) {
      symbol = platform_facts_v2_hardware_base_offset_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
        state->address_hardware_base_id[base_reg], (uint32_t)(uint16_t)displacement, symbol_buf, sizeof(symbol_buf));
      address += (uint32_t)(uint16_t)displacement;
      use.use_shape = M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_ACCESS;
    } else if ((access == M68K_SIM_ACCESS_MEMORY_READ || access == M68K_SIM_ACCESS_MEMORY_WRITE) &&
        operand_is_address_displacement_local(operand, &base_reg, &displacement) && displacement >= 0 &&
        state->relative_hardware[base_reg].offsets.count != 0U) {
      const M68kHardwareRelativeBase *base = &state->relative_hardware[base_reg];
      const AmigaOsHardwareRegisterFieldInfo *origin = amiga_os_find_hardware_register_field_by_base_id_offset(
        base->base_id, (uint16_t)displacement);
      uint8_t i;
      if (origin == NULL) continue;
      for (i = 0U; i < base->offsets.count; ++i) {
        const AmigaOsHardwareRegisterFieldInfo *field = amiga_os_find_hardware_register_field_by_base_id_offset(
          base->base_id, (uint16_t)displacement + (uint32_t)base->offsets.values[i]);
        if (field == NULL || field->register_symbol_id != origin->register_symbol_id ||
            field->field_symbol_id != origin->field_symbol_id || field->field_offset != origin->field_offset ||
            field->register_offset != origin->register_offset + base->offsets.values[i]) break;
      }
      if (i != base->offsets.count) continue;
      symbol = platform_facts_v2_hardware_base_offset_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
        base->base_id, (uint16_t)displacement, symbol_buf, sizeof(symbol_buf));
      use.use_shape = M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_REGISTER_FAMILY;
      use.relative_base_id = base->base_id;
      use.relative_register_offset = (uint16_t)displacement;
      use.relative_base_offset_count = base->offsets.count;
      use.relative_requires_input_contract = base->offsets.requires_input_contract;
      memcpy(use.relative_base_offsets, base->offsets.values, sizeof(use.relative_base_offsets));
    } else if (metadata->operation_type == M68K_SIM_OP_MOVE && instruction->size_suffix == 'l' &&
        operand_index == metadata->source_operand_index && m68k_ir_operand_immediate_value(operand, &address)) {
      symbol = platform_facts_v2_hardware_base_symbol_for_address(M68K_PLATFORM_BACKEND_AMIGA_HUNK, address);
      use.use_shape = M68K_PLATFORM_ADDRESS_USE_SHAPE_HARDWARE_BASE_ADDRESS;
    }
    if (symbol == NULL || symbol[0] == '\0') continue;
    if (lookup->hardware_address_use_count == lookup->hardware_address_use_capacity) {
      size_t capacity = lookup->hardware_address_use_capacity == 0U ? 32U : lookup->hardware_address_use_capacity * 2U;
      M68kRenderHardwareAddressUse *grown = (M68kRenderHardwareAddressUse *)render_lookup_grow_array(lookup,
        lookup->hardware_address_uses, lookup->hardware_address_use_count, sizeof(*grown), capacity);
      if (grown == NULL) return -1;
      lookup->hardware_address_uses = grown;
      lookup->hardware_address_use_capacity = capacity;
    }
    use.symbol_name = arena_strdup(render_lookup_arena(lookup), symbol);
    if (use.symbol_name == NULL) return -1;
    use.offset = offset;
    use.operand_index = (uint32_t)operand_index;
    use.address = address;
    use.effective_address = address;
    use.access_width = instruction->size_suffix == 'l' ? 4U : (instruction->size_suffix == 'w' ? 2U : 1U);
    use.access_kind = access;
    use.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
    entry = &lookup->hardware_address_uses[lookup->hardware_address_use_count++];
    entry->section_index = section_index;
    entry->use = use;
  }
  return 0;
}

/* Whole runtime layout bases are a component of the ordinary typed value.
 * IDs name canonical policy declarations, never a guessed numeric address. */
static uint16_t typed_layout_base_id(const M68kRenderLookup *lookup, const char *symbol) {
  uint16_t index;
  if (symbol == NULL || symbol[0] == '\0') return 0U;
  if (strcmp(symbol, M68K_APP_BASE_SYMBOL) == 0) return 1U;
  if (lookup == NULL || lookup->policy == NULL) return 0U;
  for (index = 0U; index < lookup->policy->rsset_layout_region_count; ++index)
    if (strcmp(symbol, lookup->policy->rsset_layout_regions[index].base_symbol) == 0)
      return (uint16_t)(index + 2U);
  return 0U;
}

static const char *typed_layout_base_symbol(const M68kRenderLookup *lookup, uint16_t id) {
  if (id == 1U) return M68K_APP_BASE_SYMBOL;
  if (lookup == NULL || lookup->policy == NULL || id < 2U ||
      id - 2U >= lookup->policy->rsset_layout_region_count) return NULL;
  return lookup->policy->rsset_layout_regions[id - 2U].base_symbol;
}

static void typed_state_import_layout_roots(M68kRenderTypedState *typed, const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *platform, size_t section_index, uint32_t offset) {
  uint8_t kind, reg;
  for (kind = M68K_ANALYSIS_REGISTER_DATA; kind <= M68K_ANALYSIS_REGISTER_ADDRESS; ++kind) {
    for (reg = 0U; reg < 8U; ++reg) {
      uint32_t bit = (uint32_t)1U << reg;
      M68kRenderTypedRegValue *value = kind == M68K_ANALYSIS_REGISTER_DATA ?
        &typed->data_regs[reg] : &typed->addr_regs[reg];
      uint32_t app = kind == M68K_ANALYSIS_REGISTER_DATA ? platform->data_app_base_known :
        platform->address_app_base_known;
      uint32_t layouts = kind == M68K_ANALYSIS_REGISTER_DATA ? platform->data_layout_base_known :
        platform->address_layout_base_known;
      const char *symbol = kind == M68K_ANALYSIS_REGISTER_DATA ? platform->data_layout_base_symbol[reg] :
        platform->address_layout_base_symbol[reg];
      uint16_t id = (app & bit) != 0U ? 1U : ((layouts & bit) != 0U ? typed_layout_base_id(lookup, symbol) : 0U);
      if (id == 0U || value->type_conflicted || value->address_value_candidate_overflow) continue;
      if (value->layout_base_id != id) {
        value->layout_base_id = id;
        value->known = 1U;
        value->provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_BASE_SLOT, section_index, offset);
      }
    }
  }
}

/* Normalize exact raw address bits through the generated fixed-hardware map.
 * This transient result is not persisted as a second cursor domain. */
static int typed_raw_hardware_value(const M68kRenderTypedRegValue *value,
    M68kHardwareRelativeBase *out) {
  memset(out, 0, sizeof(*out));
  if (!value->known || !value->raw_long_value_known || value->pointer_value_known ||
      value->type_conflicted || value->address_value_candidate_overflow || value->layout_base_id ||
      value->output || value->struct_id != AMIGA_OS_STRUCT_ID_NONE || value->raw_long_candidate_count > 4U)
    return 0;
  size_t count = value->raw_long_candidate_count ? value->raw_long_candidate_count : 1U;
  for (size_t i = 0U; i < count; ++i) {
    uint16_t base; uint32_t offset;
    uint32_t raw = count == 1U ? value->raw_long_value : value->raw_long_candidates[i];
    if (!platform_facts_v2_hardware_base_offset_for_address(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
          raw, &base, &offset) || base == PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE ||
        offset > INT16_MAX || (i && base != out->base_id)) return 0;
    out->base_id = base;
    if (!hardware_word_set_add(&out->offsets, (uint16_t)offset)) return 0;
  }
  return 1;
}

static void typed_state_project_layout_roots(const M68kRenderTypedState *typed, const M68kRenderLookup *lookup,
    M68kRenderPlatformState *platform) {
  uint8_t kind, reg;
  for (kind = M68K_ANALYSIS_REGISTER_DATA; kind <= M68K_ANALYSIS_REGISTER_ADDRESS; ++kind) {
    for (reg = 0U; reg < 8U; ++reg) {
      const M68kRenderTypedRegValue *value = kind == M68K_ANALYSIS_REGISTER_DATA ?
        &typed->data_regs[reg] : &typed->addr_regs[reg];
      const char *symbol;
      /* Exact base-zero roots use the existing named-base lifecycle, whose
       * decoded register-write invalidation also covers auto-updates. Interior
       * addresses must not masquerade as an unadjusted hardware base. */
      M68kHardwareRelativeBase hardware;
      if (kind == M68K_ANALYSIS_REGISTER_ADDRESS && !typed->app_addr_regs[reg].known &&
          typed_raw_hardware_value(value, &hardware) && hardware.offsets.count == 1U &&
          hardware.offsets.values[0] == 0U) {
        m68k_bitset_u32_set(&platform->address_hardware_base_known, reg);
        platform->address_hardware_base_id[reg] = hardware.base_id;
      }
      if (!value->known || value->type_conflicted || value->address_value_candidate_overflow ||
          value->layout_base_id == 0U) continue;
      symbol = typed_layout_base_symbol(lookup, value->layout_base_id);
      if (symbol != NULL) (void)platform_state_set_named_base_value(platform, lookup->policy, kind, reg, symbol);
    }
  }
}

/* The instruction-entry contract is shared by ordinary transfer and call
 * edges. It runs before call effects, never from a post-call output state. */
static void typed_flow_instruction_input(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kRenderTypedFlowNode *node,
    M68kRenderTypedState *typed, M68kRenderPlatformState *platform) {
  *typed = node->typed_in;
  *platform = node->platform_in;
  typed_state_apply_policy_register_seeds(typed, lookup->policy, section->section_index,
    node->candidate->offset);
  typed_state_apply_function_summaries(typed, lookup, section->section_index, node->candidate->offset);
  platform_state_apply_policy_register_seeds(platform, lookup->policy, section->section_index,
    node->candidate->offset);
  typed_state_import_layout_roots(typed, lookup, platform, section->section_index,
    node->candidate->offset);
}

static int typed_flow_process_node_impl(M68kRenderLookup *lookup, const M68kDecodeIR *decode, uint8_t **accepted_start,
    const M68kDecodeSectionIR *section, const M68kRenderTypedFlowNode *node, int allow_lookup_storage,
    int record_typed_accesses, M68kRenderTypedState *out_typed_state, M68kRenderPlatformState *out_platform_state,
    int *io_changed) {
  M68kInstructionIR instruction;
  const AmigaOsLibraryVectorInfo *chosen_vector;
  M68kTypedFlowCallResolution call_resolution;
  const AmigaOsCallOutputInfo *stored_output = NULL;
  int16_t slot_displacement = 0;
  const M68kAnalysisFunctionSummary *selected_local_effects = NULL;
  const M68kAnalysisFunctionSummary *result_summary = NULL;
  M68kAnalysisFunctionSummary generated_platform_summary;
  M68kRenderTypedState call_input_state;
  M68kRenderTypedStoredValue direct_table_value;
  uint8_t direct_table_value_known = 0U;
  uint8_t local_call_target_known = 0U;
  uint8_t call_has_result_summary = 0U;
  uint8_t generated_platform_contract_selected = 0U;
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || section == NULL || node == NULL ||
      out_typed_state == NULL || out_platform_state == NULL || node->candidate == NULL) {
    return -1;
  }
  typed_flow_instruction_input(lookup, section, node, out_typed_state, out_platform_state);
  if (m68k_decode_candidate_to_instruction(node->candidate, &instruction) != 0) return -1;
  attach_known_instruction_relocations(lookup, section->section_index, node->candidate, &instruction);
  typed_stored_value_clear(&direct_table_value);
  if (instruction_has_call_flow_local(&instruction) && instruction.operand_count == 1U &&
      typed_stored_value_from_direct_pointer_table_read(&direct_table_value, lookup, node->candidate,
        &instruction.operands[0], section->section_index, node->candidate->offset)) {
    direct_table_value_known = 1U;
  }
  typed_flow_call_resolution_init(&call_resolution);
  chosen_vector = typed_flow_resolve_vector(lookup, decode, accepted_start, section, node->candidate,
    out_platform_state, &instruction, &call_resolution);
  if (instruction_has_call_flow_local(&instruction)) {
    uint8_t requested_address = 0U;
    uint8_t reg;
    if (typed_flow_local_call_target(lookup, node->candidate, &target_section_index, &target_offset)) {
      local_call_target_known = 1U;
      /* A target-declared summary is the durable callable contract.  Inferred
       * local effects remain useful only when no declared direct contract
       * exists; selecting them first silently discarded explicit stack,
       * memory, and escape facts at the very call they describe. */
      selected_local_effects = lookup_configured_direct_function_summary(lookup, target_section_index, target_offset);
      if (selected_local_effects == NULL)
        selected_local_effects = lookup_inferred_direct_function_summary(lookup, target_section_index, target_offset);
    } else {
      size_t table_section_index = 0U;
      uint32_t table_offset = 0U;
      for (reg = 0U; reg < 8U; ++reg) {
        if (out_typed_state->addr_regs[reg].known) requested_address |= (uint8_t)(1U << reg);
      }
      if (typed_flow_callback_table_identity(out_typed_state, section, node->candidate, &instruction,
            direct_table_value_known != 0U ? &direct_table_value : NULL,
            &table_section_index, &table_offset)) {
        if (render_lookup_record_observed_callback_table(lookup, table_section_index, table_offset) != 0) return -1;
        selected_local_effects = lookup_inferred_callback_table_function_summary(lookup, table_section_index,
          table_offset);
      }
      if (selected_local_effects != NULL && selected_local_effects->effects_invalid != 0U)
        selected_local_effects = NULL;
      /* The first pass records this proven table identity.  Its callable
       * summary is materialized before the second pass; no transient
       * callback-body walk is permitted as a compatibility transfer path. */
    }
  }
  if (record_typed_accesses && render_lookup_record_layout_field_uses(lookup, section->section_index,
      out_platform_state, &instruction, node->candidate->offset) != 0) return -1;
  if (record_typed_accesses && render_lookup_record_base_app_accesses(lookup, section->section_index,
      out_platform_state, &instruction, node->candidate->offset, 0) != 0) return -1;
  if (record_typed_accesses && render_lookup_record_derived_app_accesses(lookup, section->section_index,
      out_typed_state, &instruction, node->candidate->offset) != 0) return -1;
  if (record_typed_accesses && render_lookup_record_affine_address_uses(lookup, section->section_index,
      out_typed_state, &instruction, node->candidate->offset) != 0) {
    return -1;
  }
  if (record_typed_accesses && render_lookup_record_hardware_address_uses(lookup, section->section_index,
      out_platform_state, &instruction, node->candidate->offset) != 0) return -1;
  if (render_lookup_record_typed_struct_accesses(lookup, section->section_index, out_typed_state, &instruction,
      node->candidate->offset, record_typed_accesses, io_changed) != 0) {
    return -1;
  }
  typed_state_record_io_request_immediate_store(out_typed_state, &instruction, node->candidate->offset);
  if (record_typed_accesses &&
      render_lookup_record_bootblock_disk_read_call(lookup, section->section_index, node->candidate->offset,
      out_typed_state, chosen_vector) != 0) {
    return -1;
  }
  if (lookup->affine_entry_context == NULL && instruction_has_call_flow_local(&instruction) && local_call_target_known != 0U &&
      typed_flow_record_local_call_input_consumers(lookup, section->section_index, node->candidate->offset,
        target_section_index, target_offset, out_typed_state) != 0) {
    return -1;
  }
  if (lookup->affine_entry_context == NULL && instruction_has_call_flow_local(&instruction) &&
      typed_flow_record_callback_input_consumers(lookup, section->section_index, node->candidate->offset,
        section, node->candidate, &instruction, out_typed_state,
        direct_table_value_known != 0U ? &direct_table_value : NULL) != 0) {
    return -1;
  }
  if (render_lookup_record_typed_storage_store(lookup, out_typed_state, out_platform_state, section->section_index,
      &instruction, node->candidate, node->candidate->offset, allow_lookup_storage, io_changed) != 0) {
    return -1;
  }
  if (render_lookup_record_untyped_memory_writes(lookup, out_typed_state, out_platform_state, section->section_index,
      &instruction, node->candidate->offset, allow_lookup_storage, io_changed) != 0) {
    return -1;
  }
  if (allow_lookup_storage && instruction_stores_typed_reg_to_a6_slot(out_typed_state, &instruction,
      m68k_bitset_u32_has(out_platform_state->address_base_known, 6U), &slot_displacement, &stored_output) &&
      render_lookup_add_typed_slot_effect(lookup, section->section_index, node->candidate->offset,
        slot_displacement, stored_output) != 0) {
      return -1;
  }
  /* A resolved platform target augments the callable boundary with its
   * generated result contract.  Local effects remain the wrapper's exact
   * effects; direct vectors receive the generated ABI partition itself. */
  if (chosen_vector != NULL &&
      generated_platform_call_summary(lookup->object->platform_backend_kind, chosen_vector,
        call_resolution.output_reg_known, call_resolution.output_reg_kind, call_resolution.output_reg_index,
        &generated_platform_summary)) {
    if (selected_local_effects != NULL) {
      M68kAnalysisFunctionSummary platform_contract = generated_platform_summary;
      const M68kPlatformCallThunkIR *thunk = local_call_target_known != 0U ?
        lookup_platform_call_thunk(lookup, target_section_index, target_offset) : NULL;
      if (thunk == NULL && local_call_target_known != 0U) {
        M68kPlatformCallThunkIR discovered_thunk;
        const AmigaOsLibraryVectorInfo *discovered_vector;
        memset(&discovered_thunk, 0, sizeof(discovered_thunk));
        discovered_vector = discover_direct_platform_thunk_at(lookup, decode, accepted_start, target_section_index,
          target_offset, &discovered_thunk.wrapper_call_offset);
        if (discovered_vector != NULL) {
          discovered_thunk.wrapper_section_index = (uint32_t)target_section_index;
          discovered_thunk.wrapper_entry_offset = target_offset;
          discovered_thunk.platform_library_id = discovered_vector->library_id;
          discovered_thunk.platform_function_id = discovered_vector->function_id;
          discovered_thunk.relation_kind = M68K_PLATFORM_CALL_THUNK_RELATION_PLATFORM_CALL_THUNK;
          if (render_lookup_add_platform_call_thunk(lookup, &discovered_thunk) != 0) return -1;
          thunk = lookup_platform_call_thunk(lookup, target_section_index, target_offset);
        }
      }
      M68kPlatformContractCompositionState composition =
        thunk == NULL || thunk->platform_library_id != chosen_vector->library_id ||
        thunk->platform_function_id != chosen_vector->function_id ? M68K_PLATFORM_CONTRACT_COMPOSITION_IDENTITY_CONFLICT :
        function_summary_compose_platform_contract(selected_local_effects, &platform_contract, &generated_platform_summary);
      if (composition != M68K_PLATFORM_CONTRACT_COMPOSITION_COMPLETE) {
        M68kFunctionSummaryUseIR terminal_use;
        /* This is an explicit terminal state.  Do not apply the local half as
         * though it were the platform callable's complete contract. */
        generated_platform_summary.result_contract_invalid = 1U;
        generated_platform_summary.effects_invalid = 1U;
        memset(&terminal_use, 0, sizeof(terminal_use));
        snprintf(terminal_use.function_summary_id, sizeof(terminal_use.function_summary_id), "%s",
          selected_local_effects->function_summary_id);
        terminal_use.caller_section_index = (uint32_t)section->section_index;
        terminal_use.caller_offset = node->candidate->offset;
        terminal_use.kind = M68K_FUNCTION_SUMMARY_USE_CALL;
        terminal_use.terminal_reason = thunk == NULL ? M68K_FUNCTION_SUMMARY_TERMINAL_PLATFORM_THUNK_BINDING_MISSING :
          (thunk->platform_library_id != chosen_vector->library_id ||
           thunk->platform_function_id != chosen_vector->function_id) ?
          M68K_FUNCTION_SUMMARY_TERMINAL_PLATFORM_CONTRACT_IDENTITY_CONFLICT :
          composition == M68K_PLATFORM_CONTRACT_COMPOSITION_CAPACITY ?
          M68K_FUNCTION_SUMMARY_TERMINAL_PLATFORM_CONTRACT_CAPACITY :
          M68K_FUNCTION_SUMMARY_TERMINAL_PLATFORM_CONTRACT_IDENTITY_CONFLICT;
        if (terminal_use.function_summary_id[0] != '\0' &&
            render_lookup_add_function_summary_use(lookup, &terminal_use) != 0) return -1;
        selected_local_effects = NULL;
      } else {
        selected_local_effects = &generated_platform_summary;
        generated_platform_contract_selected = 1U;
      }
    } else {
      selected_local_effects = &generated_platform_summary;
      generated_platform_contract_selected = 1U;
    }
  }
  if (!record_typed_accesses && generated_platform_contract_selected != 0U &&
      typed_flow_apply_call_input_type_refs(lookup, section->section_index, node->candidate->offset,
        out_typed_state, selected_local_effects, allow_lookup_storage, io_changed) != 0) {
    return -1;
  }
  if ((instruction_has_call_flow_local(&instruction) || generated_platform_contract_selected != 0U) &&
      selected_local_effects != NULL &&
      selected_local_effects->result_contract_invalid == 0U && selected_local_effects->result_count != 0U) {
    call_input_state = *out_typed_state;
    result_summary = selected_local_effects;
    call_has_result_summary = 1U;
  }
  typed_state_update_after_instruction(out_typed_state, lookup, out_platform_state, section->section_index,
    &instruction, node->candidate, selected_local_effects, node->candidate->offset,
    lookup->affine_entry_context == NULL);
  if (call_has_result_summary != 0U)
    typed_state_apply_function_summary_results(out_typed_state, &call_input_state, lookup, result_summary,
      section->section_index, node->candidate->offset);
  /* Sequential rendering drops terminal/call contexts. CFG successors may retain
   * literal hardware identities only across unchanged or proven preserved registers. */
  {
    M68kRenderPlatformState before = *out_platform_state;
    const M68kSimFormMetadata *metadata = m68k_sim_metadata_for_instruction(&instruction);
    uint8_t reg;
    platform_state_update_data_lvo_after_instruction(out_platform_state, &instruction);
    platform_state_update_after_instruction(out_platform_state, lookup, &instruction);
    if (metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_JUMP && node->successor_count != 0U)
      *out_platform_state = before;
    for (reg = 0U; metadata != NULL && reg < 8U; ++reg) {
      uint32_t bit = (uint32_t)1U << reg;
      if (metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
          (metadata->flow_kind == M68K_SIM_FLOW_CALL &&
           function_summary_register_effect(selected_local_effects, M68K_ANALYSIS_REGISTER_ADDRESS, reg) ==
             M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED)) {
        out_platform_state->address_hardware_base_known |= before.address_hardware_base_known & bit;
        out_platform_state->address_hardware_base_id[reg] = before.address_hardware_base_id[reg];
      }
      if (metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
          (metadata->flow_kind == M68K_SIM_FLOW_CALL &&
           function_summary_register_effect(selected_local_effects, M68K_ANALYSIS_REGISTER_DATA, reg) ==
             M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED)) {
        out_platform_state->data_hardware_base_known |= before.data_hardware_base_known & bit;
        out_platform_state->data_hardware_base_id[reg] = before.data_hardware_base_id[reg];
      }
    }
    if (metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_CALL) {
      M68kLocalHardwareValues values;
      M68kRenderPlatformState hardware;
      local_hardware_pack(&values, &before);
      local_hardware_apply_call(&values, selected_local_effects);
      local_hardware_unpack(&hardware, &values);
      out_platform_state->data_hardware_base_known = hardware.data_hardware_base_known;
      out_platform_state->address_hardware_base_known = hardware.address_hardware_base_known;
      memcpy(out_platform_state->data_hardware_base_id, hardware.data_hardware_base_id,
        sizeof(hardware.data_hardware_base_id));
      memcpy(out_platform_state->address_hardware_base_id, hardware.address_hardware_base_id,
        sizeof(hardware.address_hardware_base_id));
    }
  }
  if (instruction_has_call_flow_local(&instruction)) {
    const M68kAnalysisFunctionSummary *effects = selected_local_effects;
    uint8_t index;
    int writes = effects == NULL || effects->effects_invalid ||
      effects->memory_effect_state != M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT ||
      effects->escape_effect_state != M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT || effects->escape_count != 0U;
    if (!writes) for (index = 0U; index < effects->memory_effect_count; ++index)
      if (effects->memory_effects[index].kind == M68K_FUNCTION_SUMMARY_MEMORY_WRITE) writes = 1;
    if (writes) typed_state_forget_absolute_cells(out_typed_state);
    else out_typed_state->absolute_memory_written = 1U;
  }
  platform_state_note_call_result_after_instruction(out_platform_state, &instruction, chosen_vector);
  typed_state_project_layout_roots(out_typed_state, lookup, out_platform_state);
  typed_state_import_layout_roots(out_typed_state, lookup, out_platform_state, section->section_index,
    node->candidate->offset);
  if (candidate_terminates_a6_state(node->candidate) && node->successor_count == 0U)
    typed_state_clear_all(out_typed_state);
  return 0;
}

/* Solving mutates transient states; only the converged recording walk may
 * publish address observations. Keep all register/memory transfers shared. */
static int typed_flow_process_node(M68kRenderLookup *lookup, const M68kDecodeIR *decode, uint8_t **accepted_start,
    const M68kDecodeSectionIR *section, const M68kRenderTypedFlowNode *node, int allow_lookup_storage,
    int record_typed_accesses, M68kRenderTypedState *out_typed_state, M68kRenderPlatformState *out_platform_state,
    int *io_changed) {
  uint8_t before = lookup->suppress_address_value_observations;
  int result;
  lookup->suppress_address_value_observations = before || !record_typed_accesses;
  result = typed_flow_process_node_impl(lookup, decode, accepted_start, section, node,
    allow_lookup_storage, record_typed_accesses, out_typed_state, out_platform_state, io_changed);
  lookup->suppress_address_value_observations = before;
  return result;
}

static int typed_flow_build_nodes(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    M68kRenderTypedFlowNode **out_nodes, size_t *out_node_count, size_t **out_node_by_offset,
    uint32_t *out_node_by_offset_count, Arena *arena) {
  M68kRenderTypedFlowNode *nodes = NULL;
  size_t *node_by_offset = NULL;
  size_t candidate_index;
  uint32_t render_extent;
  size_t node_count = 0U;
  if (out_nodes != NULL) *out_nodes = NULL;
  if (out_node_count != NULL) *out_node_count = 0U;
  if (out_node_by_offset != NULL) *out_node_by_offset = NULL;
  if (out_node_by_offset_count != NULL) *out_node_by_offset_count = 0U;
  if (section == NULL || accepted_start == NULL || out_nodes == NULL || out_node_count == NULL ||
      out_node_by_offset == NULL || out_node_by_offset_count == NULL) {
    return -1;
  }
  if (arena == NULL) return -1;
  render_extent = render_section_extent(section);
  if (render_extent == 0U) return 0;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    if (candidate_is_accepted_start(section, accepted_start, candidate) && candidate->offset < render_extent)
      ++node_count;
  }
  nodes = (M68kRenderTypedFlowNode *)arena_calloc(arena,
    node_count != 0U ? node_count : 1U, sizeof(*nodes));
  node_by_offset = (size_t *)arena_alloc(arena, ((size_t)render_extent + 1U) * sizeof(*node_by_offset));
  if (nodes == NULL || node_by_offset == NULL) goto oom;
  for (candidate_index = 0U; candidate_index <= (size_t)render_extent; ++candidate_index)
    node_by_offset[candidate_index] = SIZE_MAX;
  node_count = 0U;
  for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
    const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
    if (!candidate_is_accepted_start(section, accepted_start, candidate) || candidate->offset >= render_extent)
      continue;
    nodes[node_count].candidate = candidate;
    node_by_offset[candidate->offset] = node_count;
    ++node_count;
  }
  *out_nodes = nodes;
  *out_node_count = node_count;
  *out_node_by_offset = node_by_offset;
  *out_node_by_offset_count = render_extent + 1U;
  return 0;

oom:
  return -1;
}

typedef struct M68kRenderTypedFlowGraph {
  M68kRenderTypedFlowNode *nodes;
  size_t node_count;
  size_t *node_by_offset;
  uint32_t node_by_offset_count;
  size_t *predecessor_offsets;
  size_t *predecessors;
  size_t predecessor_count;
  size_t *call_predecessor_offsets;
  size_t *call_predecessors;
  uint8_t call_inputs_enabled;
  uint8_t *call_independent_entries;
} M68kRenderTypedFlowGraph;

static void typed_flow_graph_destroy(M68kRenderTypedFlowGraph *graph);

typedef struct M68kRenderTypedFlowWorkflow {
  Arena *arena;
  M68kRenderTypedFlowGraph *graphs;
  size_t section_count;
} M68kRenderTypedFlowWorkflow;

static void typed_flow_workflow_destroy(M68kRenderTypedFlowWorkflow *workflow) {
  size_t section_index;
  if (workflow == NULL) return;
  if (workflow->graphs != NULL) {
    for (section_index = 0U; section_index < workflow->section_count; ++section_index)
      typed_flow_graph_destroy(&workflow->graphs[section_index]);
  }
  arena_destroy(workflow->arena);
  memset(workflow, 0, sizeof(*workflow));
}

static void typed_flow_graph_destroy(M68kRenderTypedFlowGraph *graph) {
  if (graph == NULL) return;
  memset(graph, 0, sizeof(*graph));
}

static void typed_flow_build_successors_for_nodes(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    M68kRenderTypedFlowNode *nodes, size_t node_count, const size_t *node_by_offset,
    uint32_t node_by_offset_count) {
  size_t node_index;
  if (section == NULL || accepted_start == NULL || nodes == NULL || node_by_offset == NULL) return;
  for (node_index = 0U; node_index < node_count; ++node_index) {
    int successor_count = typed_flow_successors_for_candidate(lookup, section, accepted_start, node_by_offset,
      node_by_offset_count, nodes[node_index].candidate, nodes[node_index].successors,
      sizeof(nodes[node_index].successors) / sizeof(nodes[node_index].successors[0]));
    nodes[node_index].successor_count = (uint8_t)(successor_count > 0 ? successor_count : 0);
  }
}

static int typed_flow_offset_is_policy_entry_point(const M68kAnalysisPolicy *policy, size_t section_index,
    uint32_t offset) {
  uint16_t entry_index;
  if (policy == NULL) return 0;
  if (section_index == 0U && policy->has_entry_offset && policy->entry_offset == offset) return 1;
  for (entry_index = 0U; entry_index < policy->entry_point_count; ++entry_index) {
    const M68kAnalysisEntryPoint *entry = &policy->entry_points[entry_index];
    size_t entry_section = entry->has_section_index ? entry->section_index : 0U;
    if (entry_section == section_index && entry->offset == offset) return 1;
  }
  return 0;
}

static int typed_flow_mark_roots(const M68kAnalysisPolicy *policy, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start,
    M68kRenderTypedFlowNode *nodes, size_t node_count, const size_t *node_by_offset,
    uint32_t node_by_offset_count, Arena *arena) {
  uint16_t *incoming_counts = NULL;
  ArenaMark mark;
  size_t node_index;
  int seeded_root = 0;
  (void)accepted_start;
  (void)node_by_offset;
  (void)node_by_offset_count;
  if (node_count == 0U) return 0;
  if (arena == NULL) return -1;
  mark = arena_mark(arena);
  incoming_counts = (uint16_t *)arena_calloc(arena, node_count, sizeof(*incoming_counts));
  if (incoming_counts == NULL) {
    arena_rewind(arena, mark);
    return -1;
  }
  for (node_index = 0U; node_index < node_count; ++node_index) nodes[node_index].is_root = 0U;
  for (node_index = 0U; node_index < node_count; ++node_index) {
    uint8_t successor_index;
    for (successor_index = 0U; successor_index < nodes[node_index].successor_count; ++successor_index) {
      size_t successor = nodes[node_index].successors[successor_index];
      if (successor < node_count && incoming_counts[successor] < UINT16_MAX) ++incoming_counts[successor];
    }
  }
  for (node_index = 0U; node_index < node_count; ++node_index) {
    if (typed_flow_offset_is_policy_entry_point(policy, section != NULL ? section->section_index : 0U,
        nodes[node_index].candidate->offset)) {
      nodes[node_index].is_root = 1U;
      seeded_root = 1;
    }
  }
  for (node_index = 0U; node_index < node_count; ++node_index) {
    if (incoming_counts[node_index] != 0U) continue;
    nodes[node_index].is_root = 1U;
    seeded_root = 1;
  }
  if (!seeded_root) nodes[0].is_root = 1U;
  arena_rewind(arena, mark);
  return 0;
}

static void typed_flow_reset_roots(M68kRenderTypedFlowNode *nodes, size_t node_count) {
  size_t node_index;
  for (node_index = 0U; node_index < node_count; ++node_index) {
    typed_state_clear_all(&nodes[node_index].typed_in);
    typed_state_clear_all(&nodes[node_index].typed_out);
    memset(&nodes[node_index].platform_in, 0, sizeof(nodes[node_index].platform_in));
    memset(&nodes[node_index].platform_out, 0, sizeof(nodes[node_index].platform_out));
    nodes[node_index].has_in = 0U;
    nodes[node_index].has_out = 0U;
    if (nodes[node_index].is_root) {
      nodes[node_index].has_in = 1U;
    }
  }
}

static int typed_flow_initialize_roots(const M68kAnalysisPolicy *policy, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start,
    M68kRenderTypedFlowNode *nodes, size_t node_count, const size_t *node_by_offset,
    uint32_t node_by_offset_count, Arena *arena) {
  if (typed_flow_mark_roots(policy, section, accepted_start, nodes, node_count, node_by_offset,
      node_by_offset_count, arena) != 0) {
    return -1;
  }
  typed_flow_reset_roots(nodes, node_count);
  return 0;
}

static int typed_flow_build_predecessors(M68kRenderTypedFlowGraph *graph, Arena *arena);

static int typed_flow_graph_build(M68kRenderTypedFlowGraph *graph, const M68kRenderLookup *lookup,
    const M68kAnalysisPolicy *policy,
    const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, Arena *arena) {
  if (graph == NULL) return -1;
  memset(graph, 0, sizeof(*graph));
  if (typed_flow_build_nodes(section, accepted_start, &graph->nodes, &graph->node_count,
      &graph->node_by_offset, &graph->node_by_offset_count, arena) != 0) {
    return -1;
  }
  typed_flow_build_successors_for_nodes(lookup, section, accepted_start, graph->nodes, graph->node_count,
    graph->node_by_offset, graph->node_by_offset_count);
  if (typed_flow_build_predecessors(graph, arena) != 0) {
    typed_flow_graph_destroy(graph);
    return -1;
  }
  if (typed_flow_initialize_roots(policy, section, accepted_start, graph->nodes, graph->node_count,
      graph->node_by_offset, graph->node_by_offset_count, arena) != 0) {
    typed_flow_graph_destroy(graph);
    return -1;
  }
  return 0;
}

static void typed_flow_reinitialize_roots(M68kRenderTypedFlowNode *nodes, size_t node_count) {
  if (node_count != 0U) {
    typed_flow_reset_roots(nodes, node_count);
  }
}

static size_t typed_flow_limit_from_env(const char *name, size_t default_value) {
  const char *text = getenv(name);
  const char *cursor;
  size_t value = 0U;
  if (text == NULL || text[0] == '\0') return default_value;
  for (cursor = text; *cursor != '\0'; ++cursor) {
    size_t digit;
    if (*cursor < '0' || *cursor > '9') return default_value;
    digit = (size_t)(*cursor - '0');
    if (value > (SIZE_MAX - digit) / 10U) return default_value;
    value = value * 10U + digit;
  }
  return value != 0U ? value : default_value;
}

static size_t typed_flow_min_size(size_t left, size_t right) {
  return left < right ? left : right;
}

static size_t typed_flow_visit_limit(size_t node_count, size_t iteration_limit, size_t node_visit_limit) {
  size_t effective_iterations;
  if (node_count == 0U) return 0U;
  effective_iterations = typed_flow_min_size(node_count + 8U, iteration_limit);
  if (effective_iterations != 0U && node_count > SIZE_MAX / effective_iterations) return node_visit_limit;
  return typed_flow_min_size(node_count * effective_iterations, node_visit_limit);
}

static int typed_flow_enqueue_node(size_t *queue, uint8_t *queued, size_t capacity, size_t *io_head,
    size_t *io_count, size_t node_index) {
  size_t slot;
  if (queue == NULL || queued == NULL || io_head == NULL || io_count == NULL || node_index >= capacity) return 0;
  if (queued[node_index]) return 0;
  if (*io_count >= capacity) return -1;
  slot = (*io_head + *io_count) % capacity;
  queue[slot] = node_index;
  queued[node_index] = 1U;
  ++*io_count;
  return 0;
}

/* DBF decrements the low WORD and branches only if it is not $FFFF. Do not
 * merge the exhausted counter into the backedge, or a bounded loop becomes top. */
static int hardware_relative_refine_dbf_edge(const M68kRenderTypedFlowNode *predecessor,
    const M68kRenderTypedFlowNode *successor, M68kRenderPlatformState *state) {
  M68kInstructionIR instruction;
  M68kHardwareWordSet result = {0};
  uint8_t reg, i;
  int fallthrough;
  if (predecessor->candidate->mnemonic_id != M68K_ASM_MNEMONIC_DBF ||
      m68k_decode_candidate_to_instruction(predecessor->candidate, &instruction) != 0 ||
      !operand_is_data_register_local(&instruction.operands[0], &reg) || state->word_values[reg].count == 0U)
    return 1;
  fallthrough = successor->candidate->offset == predecessor->candidate->offset + predecessor->candidate->byte_count;
  for (i = 0U; i < state->word_values[reg].count; ++i) {
    uint16_t value = state->word_values[reg].values[i];
    if ((value == UINT16_MAX) == fallthrough) (void)hardware_word_set_add(&result, value);
  }
  if (result.count == 0U) return 0;
  result.requires_input_contract = state->word_values[reg].requires_input_contract;
  state->word_values[reg] = result;
  return 1;
}

#include "m68k_call_entry_inputs.inc"

static int typed_flow_recompute_node_input(M68kRenderTypedFlowGraph *graph, size_t node_index,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section) {
  M68kRenderTypedFlowNode *node;
  M68kRenderTypedState typed_input;
  M68kRenderPlatformState platform_input;
  int has_input;
  size_t predecessor_index;
  if (graph == NULL || node_index >= graph->node_count || graph->predecessor_offsets == NULL ||
      graph->predecessors == NULL) return 0;
  node = &graph->nodes[node_index];
  memset(&typed_input, 0, sizeof(typed_input));
  memset(&platform_input, 0, sizeof(platform_input));
  has_input = node->is_root != 0U;
  for (predecessor_index = graph->predecessor_offsets[node_index];
       predecessor_index < graph->predecessor_offsets[node_index + 1U]; ++predecessor_index) {
    const M68kRenderTypedFlowNode *predecessor = &graph->nodes[graph->predecessors[predecessor_index]];
    if (predecessor->has_out == 0U) continue;
    if (!has_input) {
      typed_input = predecessor->typed_out;
      platform_input = predecessor->platform_out;
      has_input = 1;
    } else {
      (void)typed_state_merge_into(&typed_input, &predecessor->typed_out);
      (void)platform_state_merge_into(&platform_input, &predecessor->platform_out);
    }
  }
  if (graph->call_inputs_enabled && graph->call_predecessor_offsets) {
    for (size_t p = graph->call_predecessor_offsets[node_index];
        p < graph->call_predecessor_offsets[node_index + 1U]; ++p) {
      const M68kRenderTypedFlowNode *caller = &graph->nodes[graph->call_predecessors[p]];
      M68kRenderTypedState entry;
      M68kRenderPlatformState platform;
      if (!caller->has_in) continue;
      typed_flow_call_entry_input(lookup, section, caller, &entry, &platform);
      if (!has_input) { typed_input = entry; platform_input = platform; has_input = 1; }
      else { (void)typed_state_merge_into(&typed_input, &entry);
        (void)platform_state_merge_into(&platform_input, &platform); }
    }
  }
  if ((node->has_in != 0U) == has_input && (!has_input ||
      (typed_state_equal(&node->typed_in, &typed_input) && platform_states_equal(&node->platform_in, &platform_input)))) {
    return 0;
  }
  node->typed_in = typed_input;
  node->platform_in = platform_input;
  node->has_in = has_input ? 1U : 0U;
  return 1;
}

/* Hardware bounds have a separate fixed point. Unrelated typed memory/cursor
 * churn cannot either suppress these proofs or certify an unfinished set. */
static int typed_flow_note_incomplete(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, size_t visit_limit, size_t pending);

static int hardware_relative_analyze_graph(M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    M68kRenderTypedFlowGraph *graph, Arena *arena) {
  M68kRenderPlatformState *inputs, *outputs;
  uint8_t *has_in, *has_out, *queued;
  size_t *queue, head = 0U, count = 0U, visits = 0U, index;
  size_t limit = typed_flow_limit_from_env("AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS",
    M68K_RENDER_TYPED_FLOW_DEFAULT_NODE_VISIT_LIMIT);
  ArenaMark mark;
  int result = -1;
  if (graph->node_count == 0U) return 0;
  /* Reuse existing node storage, not a second retained scalar-state array.
   * Failed/incomplete solves leave unknown values, never a stale proof. */
  for (index = 0U; index < graph->node_count; ++index)
    memset(graph->nodes[index].platform_out.word_values, 0, sizeof(graph->nodes[index].platform_out.word_values));
  mark = arena_mark(arena);
  inputs = arena_calloc(arena, graph->node_count, sizeof(*inputs));
  outputs = arena_calloc(arena, graph->node_count, sizeof(*outputs));
  has_in = arena_calloc(arena, graph->node_count, 1U);
  has_out = arena_calloc(arena, graph->node_count, 1U);
  queued = arena_calloc(arena, graph->node_count, 1U);
  queue = arena_alloc(arena, graph->node_count * sizeof(*queue));
  if (inputs == NULL || outputs == NULL || has_in == NULL || has_out == NULL || queued == NULL || queue == NULL)
    goto done;
  for (index = 0U; index < graph->node_count; ++index) if (typed_flow_hardware_root(graph, index)) {
    has_in[index] = 1U;
    if (typed_flow_enqueue_node(queue, queued, graph->node_count, &head, &count, index) != 0) goto done;
  }
  while (count != 0U && visits++ < limit) {
    const M68kRenderTypedFlowNode *node;
    M68kRenderPlatformState before, next, normalized;
    M68kInstructionIR instruction;
    uint8_t successor_index;
    index = queue[head];
    head = (head + 1U) % graph->node_count;
    --count;
    queued[index] = 0U;
    node = &graph->nodes[index];
    before = inputs[index];
    platform_state_apply_policy_register_seeds(&before, lookup->policy, section->section_index,
      node->candidate->offset);
    hardware_relative_apply_policy_inputs(&before, lookup->policy, section->section_index, node->candidate->offset);
    if (m68k_decode_candidate_to_instruction(node->candidate, &instruction) != 0) goto done;
    next = before;
    platform_state_update_after_instruction(&next, lookup, &instruction);
    /* Calls are top in this solver. Existing exact-address call proofs remain
     * separate; no new preservation assumption is made for a relative base. */
    hardware_relative_transfer(&next, &before, &instruction);
    memset(&normalized, 0, sizeof(normalized));
    normalized.data_hardware_base_known = next.data_hardware_base_known;
    normalized.address_hardware_base_known = next.address_hardware_base_known;
    memcpy(normalized.data_hardware_base_id, next.data_hardware_base_id, sizeof(next.data_hardware_base_id));
    memcpy(normalized.address_hardware_base_id, next.address_hardware_base_id, sizeof(next.address_hardware_base_id));
    memcpy(normalized.word_values, next.word_values, sizeof(next.word_values));
    memcpy(normalized.relative_hardware, next.relative_hardware, sizeof(next.relative_hardware));
    if (has_out[index] && platform_states_equal(&outputs[index], &normalized)) continue;
    outputs[index] = normalized;
    has_out[index] = 1U;
    for (successor_index = 0U; successor_index < node->successor_count; ++successor_index) {
      size_t successor = node->successors[successor_index], predecessor_index;
      M68kRenderPlatformState input;
      int found = typed_flow_hardware_root(graph, successor);
      memset(&input, 0, sizeof(input));
      for (predecessor_index = graph->predecessor_offsets[successor];
           predecessor_index < graph->predecessor_offsets[successor + 1U]; ++predecessor_index) {
        size_t predecessor = graph->predecessors[predecessor_index];
        M68kRenderPlatformState edge;
        if (!has_out[predecessor]) continue;
        edge = outputs[predecessor];
        if (!hardware_relative_refine_dbf_edge(&graph->nodes[predecessor], &graph->nodes[successor], &edge)) continue;
        if (!found) input = edge;
        else (void)platform_state_merge_into(&input, &edge);
        found = 1;
      }
      if (has_in[successor] == (uint8_t)found && platform_states_equal(&inputs[successor], &input)) continue;
      inputs[successor] = input;
      has_in[successor] = (uint8_t)found;
      if (found && typed_flow_enqueue_node(queue, queued, graph->node_count, &head, &count, successor) != 0) goto done;
    }
  }
  if (count != 0U && typed_flow_note_incomplete(lookup, section->section_index,
      graph->nodes[queue[head]].candidate->offset, limit, count) != 0) goto done;
  if (count == 0U) for (index = 0U; index < graph->node_count; ++index) if (has_in[index]) {
    /* Publish only the converged post-instruction scalar proof. Counter users
     * still reject unknown or input-contract-dependent values. */
    memcpy(graph->nodes[index].platform_out.word_values, outputs[index].word_values,
      sizeof(outputs[index].word_values));
    M68kRenderPlatformState proof = inputs[index];
    M68kInstructionIR instruction;
    uint8_t reg;
    platform_state_apply_policy_register_seeds(&proof, lookup->policy, section->section_index,
      graph->nodes[index].candidate->offset);
    hardware_relative_apply_policy_inputs(&proof, lookup->policy, section->section_index,
      graph->nodes[index].candidate->offset);
    for (reg = 0U; reg < 8U; ++reg)
      if (m68k_bitset_u32_has(proof.address_hardware_base_known, reg) &&
          proof.relative_hardware[reg].offsets.count == 1U && proof.relative_hardware[reg].offsets.values[0] == 0U)
        memset(&proof.relative_hardware[reg], 0, sizeof(proof.relative_hardware[reg]));
    proof.address_hardware_base_known = proof.data_hardware_base_known = 0U;
    if (m68k_decode_candidate_to_instruction(graph->nodes[index].candidate, &instruction) != 0 ||
        render_lookup_record_hardware_address_uses(lookup, section->section_index, &proof, &instruction,
          graph->nodes[index].candidate->offset) != 0) goto done;
  }
  result = 0;
done:
  arena_rewind(arena, mark);
  return result;
}

/* Persist a bounded, per-section warning even when optional tracing is off.
 * Any exhausted pass may already have contributed discovery facts; a later
 * pass must not erase that limitation. capacity is visits, hit_count pending. */
static int typed_flow_note_incomplete(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, size_t visit_limit, size_t pending) {
  M68kIncompleteAnalysisIR *item;
  size_t index;
  for (index = 0U; index < lookup->typed_flow_incomplete_count; ++index) {
    item = &lookup->typed_flow_incomplete[index];
    if (item->section_index == section_index) {
      if (item->hit_count < pending) item->hit_count = pending > UINT32_MAX ? UINT32_MAX : (uint32_t)pending;
      return 0;
    }
  }
  if (lookup->typed_flow_incomplete_count == lookup->typed_flow_incomplete_capacity) {
    size_t next_capacity = lookup->typed_flow_incomplete_capacity == 0U ? 4U :
      lookup->typed_flow_incomplete_capacity * 2U;
    M68kIncompleteAnalysisIR *grown = render_lookup_grow_array(lookup, lookup->typed_flow_incomplete,
      lookup->typed_flow_incomplete_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->typed_flow_incomplete = grown;
    lookup->typed_flow_incomplete_capacity = next_capacity;
  }
  item = &lookup->typed_flow_incomplete[lookup->typed_flow_incomplete_count++];
  memset(item, 0, sizeof(*item));
  item->kind = M68K_INCOMPLETE_ANALYSIS_CAPACITY_EXHAUSTED;
  item->source_kind = M68K_INCOMPLETE_ANALYSIS_SOURCE_TYPED_FLOW_WORKLIST;
  item->section_index = (uint32_t)section_index;
  item->offset = offset;
  item->capacity = visit_limit > UINT32_MAX ? UINT32_MAX : (uint32_t)visit_limit;
  item->hit_count = pending > UINT32_MAX ? UINT32_MAX : (uint32_t)pending;
  return 0;
}

/* Optional bounded worklist diagnostics; no analysis decisions depend on these. */
typedef struct TypedFlowVisitTrace {
  size_t visits, typed_changes, platform_changes;
  size_t platform_first_changed_byte, typed_first_changed_byte;
} TypedFlowVisitTrace;

static int render_lookup_analyze_amiga_typed_refs_for_section(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, const M68kDecodeSectionIR *section, M68kRenderTypedFlowGraph *graph,
    int final_pass, int *io_changed, Arena *arena) {
  size_t iteration_limit = typed_flow_limit_from_env("AMIGA_REVERSING_TYPED_FLOW_MAX_ITERATIONS",
    M68K_RENDER_TYPED_FLOW_DEFAULT_ITERATION_LIMIT);
  size_t node_visit_limit = typed_flow_limit_from_env("AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS",
    M68K_RENDER_TYPED_FLOW_DEFAULT_NODE_VISIT_LIMIT);
  size_t max_visits = 0U, node_visit_count = 0U, queue_head = 0U, queue_count = 0U, node_index;
  size_t *queue = NULL;
  uint8_t *queued = NULL;
  const char *trace_env = getenv("AMIGA_REVERSING_PROFILE_TYPED_FLOW");
  TypedFlowVisitTrace *trace_nodes = NULL;
  int trace_enabled = trace_env != NULL && strcmp(trace_env, "1") == 0;
  ArenaMark mark;
  int result = -1;
  if (graph == NULL || arena == NULL) return -1;
  typed_flow_reinitialize_roots(graph->nodes, graph->node_count);
  if (graph->node_count == 0U) return 0;
  mark = arena_mark(arena);
  queue = (size_t *)arena_alloc(arena, graph->node_count * sizeof(*queue));
  queued = (uint8_t *)arena_calloc(arena, graph->node_count, sizeof(*queued));
  if (queue == NULL || queued == NULL) goto cleanup;
  if (trace_enabled) {
    trace_nodes = arena_calloc(arena, graph->node_count, sizeof(*trace_nodes));
    if (trace_nodes == NULL) goto cleanup;
  }
  max_visits = typed_flow_visit_limit(graph->node_count, iteration_limit, node_visit_limit);
  for (node_index = 0U; node_index < graph->node_count; ++node_index) {
    if (graph->nodes[node_index].has_in != 0U &&
        typed_flow_enqueue_node(queue, queued, graph->node_count, &queue_head, &queue_count, node_index) != 0) {
      goto cleanup;
    }
  }
  while (queue_count != 0U && node_visit_count < max_visits) {
    M68kRenderTypedState next_typed_state;
    M68kRenderPlatformState next_platform_state;
    M68kRenderTypedFlowNode *node;
    uint8_t successor_index;
    node_index = queue[queue_head];
    queue_head = (queue_head + 1U) % graph->node_count;
    --queue_count;
    queued[node_index] = 0U;
    node = &graph->nodes[node_index];
    if (node->has_in == 0U) continue;
    ++node_visit_count;
    if (typed_flow_process_node(lookup, decode, accepted_start, section, node, !final_pass,
        0, &next_typed_state, &next_platform_state, io_changed) != 0) {
      goto cleanup;
    }
    if (trace_nodes != NULL) {
      TypedFlowVisitTrace *trace_node = &trace_nodes[node_index];
      ++trace_node->visits;
      if (!typed_state_equal(&node->typed_out, &next_typed_state)) {
        const unsigned char *old_bytes = (const unsigned char *)&node->typed_out;
        const unsigned char *new_bytes = (const unsigned char *)&next_typed_state;
        size_t byte_index;
        ++trace_node->typed_changes;
        for (byte_index = 0U; byte_index < sizeof(next_typed_state); ++byte_index)
          if (old_bytes[byte_index] != new_bytes[byte_index]) break;
        trace_node->typed_first_changed_byte = byte_index;
      }
      if (!platform_states_equal(&node->platform_out, &next_platform_state)) {
        const unsigned char *old_bytes = (const unsigned char *)&node->platform_out;
        const unsigned char *new_bytes = (const unsigned char *)&next_platform_state;
        size_t byte_index;
        ++trace_node->platform_changes;
        for (byte_index = 0U; byte_index < sizeof(next_platform_state); ++byte_index)
          if (old_bytes[byte_index] != new_bytes[byte_index]) break;
        trace_node->platform_first_changed_byte = byte_index;
      }
    }
    if (graph->call_inputs_enabled && node->call_target < graph->node_count &&
        typed_flow_recompute_node_input(graph, node->call_target, lookup, section) &&
        typed_flow_enqueue_node(queue, queued, graph->node_count, &queue_head, &queue_count,
          node->call_target) != 0) goto cleanup;
    if (node->has_out == 0U || !typed_state_equal(&node->typed_out, &next_typed_state) ||
        !platform_states_equal(&node->platform_out, &next_platform_state)) {
      node->typed_out = next_typed_state;
      node->platform_out = next_platform_state;
      node->has_out = 1U;
      for (successor_index = 0U; successor_index < node->successor_count; ++successor_index) {
        size_t successor = node->successors[successor_index];
        if (successor >= graph->node_count) continue;
        if (typed_flow_recompute_node_input(graph, successor, lookup, section)) {
          if (typed_flow_enqueue_node(queue, queued, graph->node_count, &queue_head, &queue_count, successor) != 0)
            goto cleanup;
        }
      }
    }
  }
  if (queue_count != 0U && typed_flow_note_incomplete(lookup, section->section_index,
      graph->nodes[queue[queue_head]].candidate->offset, max_visits, queue_count) != 0) goto cleanup;
  if (final_pass) {
    for (node_index = 0U; node_index < graph->node_count; ++node_index) {
      M68kRenderTypedState ignored_typed_state;
      M68kRenderPlatformState ignored_platform_state;
      if (graph->nodes[node_index].has_in == 0U) continue;
      if (typed_flow_process_node(lookup, decode, accepted_start, section, &graph->nodes[node_index], 0,
          1, &ignored_typed_state, &ignored_platform_state, NULL) != 0) {
        goto cleanup;
      }
    }
    if (hardware_relative_analyze_graph(lookup, section, graph, arena) != 0) goto cleanup;
  }
  result = 0;

cleanup:
  {
    const char *trace = getenv("AMIGA_REVERSING_PROFILE_TYPED_FLOW");
    if (trace != NULL && strcmp(trace, "1") == 0)
      fprintf(stderr, "typed_flow_worklist section=%zu final=%d nodes=%zu visits=%zu pending=%zu max=%zu typed_state_bytes=%zu platform_state_bytes=%zu\n",
        (size_t)section->section_index, final_pass, graph->node_count, node_visit_count, queue_count, max_visits,
        sizeof(M68kRenderTypedState), sizeof(M68kRenderPlatformState));
  }
  if (trace_nodes != NULL) {
    size_t rank;
    for (rank = 0U; rank < 12U && rank < graph->node_count; ++rank) {
      size_t hottest = 0U;
      for (node_index = 1U; node_index < graph->node_count; ++node_index)
        if (trace_nodes[node_index].visits > trace_nodes[hottest].visits) hottest = node_index;
      if (trace_nodes[hottest].visits == 0U) break;
      fprintf(stderr, "typed_flow_hot section=%zu final=%d offset=%u visits=%zu typed_changes=%zu platform_changes=%zu platform_first_changed_byte=%zu typed_first_changed_byte=%zu pending=%u\n",
        (size_t)section->section_index, final_pass, graph->nodes[hottest].candidate->offset,
        trace_nodes[hottest].visits, trace_nodes[hottest].typed_changes,
        trace_nodes[hottest].platform_changes, trace_nodes[hottest].platform_first_changed_byte,
        trace_nodes[hottest].typed_first_changed_byte, (unsigned)queued[hottest]);
      trace_nodes[hottest].visits = 0U;
    }
  }
  arena_rewind(arena, mark);
  return result;
}

static int amiga_vector_has_typed_flow_info(const AmigaOsLibraryVectorInfo *vector) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  size_t index;
  if (vector == NULL) return 0;
  if (amiga_output_has_typed_info(&vector->output)) return 1;
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  for (index = 0U; inputs != NULL && index < input_count; ++index)
    if (inputs[index].struct_id != AMIGA_OS_STRUCT_ID_NONE) return 1;
  return 0;
}

static int policy_has_typed_flow_metadata(const M68kAnalysisPolicy *policy) {
  if (policy == NULL) return 0;
  return policy->register_seed_count != 0U || policy->function_summary_count != 0U ||
    policy->rsset_layout_region_count != 0U ||
    policy->structured_data_item_count != 0U;
}

static int decode_has_library_base_operand_use(const M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderPlatformState state;
    uint32_t seen_library_base = 0U;
    size_t candidate_index;
    memset(&state, 0, sizeof(state));
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      size_t operand_index;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index,
        candidate->offset);
      for (operand_index = 0U; operand_index < instruction.operand_count; ++operand_index) {
        uint8_t base_reg = 0U;
        int16_t displacement = 0;
        if (operand_is_address_displacement_local(&instruction.operands[operand_index], &base_reg,
            &displacement) && base_reg < 8U && (m68k_bitset_u32_has(state.address_base_known, base_reg) ||
            m68k_bitset_u32_has(seen_library_base, base_reg))) {
          return 1;
        }
      }
      platform_state_update_data_lvo_after_instruction(&state, &instruction);
      platform_state_update_after_instruction(&state, lookup, &instruction);
      for (operand_index = 0U; operand_index < 8U; ++operand_index)
        if (m68k_bitset_u32_has(state.address_base_known, (uint8_t)operand_index))
          m68k_bitset_u32_set(&seen_library_base, (uint8_t)operand_index);
      if (state.data_hardware_base_known != 0U || state.address_hardware_base_known != 0U) return 1;
    }
  }
  return 0;
}

static int render_lookup_has_typed_flow_sources(const M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  size_t index;
  if (lookup == NULL) return 0;
  if (lookup->typed_app_slot_count != 0U || lookup->typed_storage_slot_count != 0U ||
      lookup->typed_slot_effect_count != 0U || lookup->base_field_slot_count != 0U ||
      lookup->indexed_vector_wrapper_count != 0U || policy_has_typed_flow_metadata(lookup->policy) ||
      (lookup->object != NULL && lookup->object->symbol_count != 0U) ||
      decode_has_library_base_operand_use(lookup, decode, accepted_start)) {
    return 1;
  }
  if (lookup->policy != NULL) {
    size_t structured_index;
    for (structured_index = 0U; structured_index < lookup->policy->structured_data_item_count;
        ++structured_index) {
      const M68kAnalysisStructuredDataItem *item = &lookup->policy->structured_data_items[structured_index];
      if (item->has_consumer && item->table_kind_id == M68K_ANALYSIS_TABLE_KIND_POINTER &&
          item->pointer_struct[0] != '\0') return 1;
    }
  }
  /* Affine source-address propagation is itself a typed-flow source.  Do not
   * make it depend on an unrelated OS/base metadata seed. */
  if (decode != NULL && accepted_start != NULL) {
    for (index = 0U; index < decode->section_count; ++index) {
      const M68kDecodeSectionIR *section = &decode->sections[index];
      size_t candidate_index;
      for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
        const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
        M68kInstructionIR instruction;
        if (accepted_start[index] == NULL || candidate->offset >= section->size ||
            accepted_start[index][candidate->offset] == 0U ||
            m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
        if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction.operand_count == 2U &&
            operand_address_register_index_local(&instruction.operands[1], NULL)) return 1;
      }
    }
  }
  for (index = 0U; index < lookup->global_base_slot_count; ++index) {
    if (lookup->global_base_slots[index].has_library_id != 0U &&
        lookup->global_base_slots[index].conflicted == 0U) return 1;
  }
  for (index = 0U; index < lookup->platform_derived_summary_count; ++index) {
    if (amiga_vector_has_typed_flow_info(lookup->platform_derived_summaries[index].vector)) return 1;
  }
  return 0;
}

static int typed_flow_workflow_prepare(M68kRenderTypedFlowWorkflow *workflow,
    const M68kRenderLookup *lookup, const M68kDecodeIR *decode, uint8_t **accepted_start) {
  size_t section_index;
  if (workflow == NULL || lookup == NULL || decode == NULL || accepted_start == NULL) return -1;
  memset(workflow, 0, sizeof(*workflow));
  if (lookup->object == NULL || lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
      !render_lookup_has_typed_flow_sources(lookup, decode, accepted_start)) {
    return 0;
  }
  workflow->arena = arena_create(4096U);
  if (workflow->arena == NULL) return -1;
  workflow->graphs = (M68kRenderTypedFlowGraph *)arena_calloc(workflow->arena,
    decode->section_count != 0U ? decode->section_count : 1U, sizeof(*workflow->graphs));
  if (workflow->graphs == NULL) goto fail;
  workflow->section_count = decode->section_count;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    if (typed_flow_graph_build(&workflow->graphs[section_index], lookup, lookup->policy,
        &decode->sections[section_index], accepted_start[section_index], workflow->arena) != 0) {
      goto fail;
    }
  }
  return 0;

fail:
  typed_flow_workflow_destroy(workflow);
  return -1;
}

static int render_lookup_analyze_amiga_typed_refs(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, M68kRenderTypedFlowWorkflow *workflow,
    int record_final_accesses) {
  int pass;
  int changed = 0;
  size_t section_index;
  int result = -1;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || workflow == NULL) return -1;
  if (workflow->graphs == NULL) return 0;
  if (workflow->section_count != decode->section_count) return -1;
  for (pass = 0; pass < (record_final_accesses ? 5 : 4); ++pass) {
    int final_pass = record_final_accesses != 0 && pass == 4;
    changed = 0;
    if (final_pass) {
      lookup->address_value_consumer_count = 0U;
      lookup->layout_field_use_count = 0U;
      lookup->typed_access_count = 0U;
      lookup->hardware_address_use_count = 0U;
      lookup->affine_address_use_count = 0U;
    }
    for (section_index = 0U; section_index < decode->section_count; ++section_index) {
      if (render_lookup_analyze_amiga_typed_refs_for_section(lookup, decode, accepted_start,
          &decode->sections[section_index], &workflow->graphs[section_index], final_pass,
          final_pass ? NULL : &changed, workflow->arena) != 0) {
        goto cleanup;
      }
    }
    if (!final_pass && !changed) {
      if (record_final_accesses) pass = 3;
      else break;
    }
  }
  result = 0;

cleanup:
  return result;
}

/* Only changed entry contexts need another solve, not discovery/policy replay.
 * There is one existing CFG worklist and one converged recording epoch. */
static int typed_flow_solve_call_inputs(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted, M68kRenderTypedFlowWorkflow *workflow) {
  if (!workflow->graphs) return 0;
  int any = 0;
  for (size_t i = 0U; i < workflow->section_count; ++i) any |= workflow->graphs[i].call_inputs_enabled;
  if (!any) return 0;
  size_t epochs = 0U;
  int exposed;
  do {
    lookup->address_value_consumer_count = lookup->typed_access_count = 0U;
    lookup->hardware_address_use_count = lookup->affine_address_use_count = 0U;
    lookup->layout_field_use_count = 0U;
    /* Earlier recording epochs cannot certify a changed entry context. Keep
     * explicit bindings and qualified fallback interpretations; re-project
     * inferred register identities from the final shared state below. */
    size_t kept = 0U;
    for (size_t i = 0U; i < lookup->app_slot_ref_count; ++i) {
      const M68kRenderAppSlotRef *ref = &lookup->app_slot_refs[i];
      if (ref->ref.base_evidence_kind != M68K_APP_SLOT_BASE_USE_SITE_BINDING &&
          (ref->ref.base_evidence_kind == M68K_APP_SLOT_BASE_REGISTER_STATE || ref->ref.has_derived_base)) continue;
      if (kept != i) lookup->app_slot_refs[kept] = *ref;
      if (lookup->app_slot_refs[kept].ref.symbol_name)
        lookup->app_slot_refs[kept].ref.symbol_name = lookup->app_slot_refs[kept].symbol_name;
      ++kept;
    }
    lookup->app_slot_ref_count = kept;
    for (size_t i = 0U; i < workflow->section_count; ++i) {
      if (render_lookup_analyze_amiga_typed_refs_for_section(lookup, decode, accepted,
          &decode->sections[i], &workflow->graphs[i], 1, NULL, workflow->arena) != 0) return -1;
    }
    ++epochs;
    exposed = typed_flow_retain_new_call_exposures(lookup, workflow);
  } while (exposed);
  const char *trace = getenv("AMIGA_REVERSING_PROFILE_CALL_INPUTS");
  if (trace && !strcmp(trace, "1")) fprintf(stderr,"call_input_epochs=%zu\n",epochs);
  return 0;
}

/* One indexed lookup per existing access, not an instruction x reference
 * scan. Qualified fallbacks remain when the base is unknown; a proved
 * hardware/library/other-layout value contradicts an app interpretation. */
static void typed_flow_filter_nonapp_fallbacks(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    const M68kRenderTypedFlowWorkflow *workflow) {
  if (!workflow->graphs) return;
  size_t kept = 0U;
  for (size_t i = 0U; i < lookup->app_slot_ref_count; ++i) {
    const M68kRenderAppSlotRef *ref = &lookup->app_slot_refs[i];
    int contradicted = 0;
    if (ref->ref.base_evidence_kind != M68K_APP_SLOT_BASE_USE_SITE_BINDING &&
        ref->section_index < workflow->section_count && ref->ref.base_reg < 8U) {
      const M68kRenderTypedFlowGraph *graph = &workflow->graphs[ref->section_index];
      if (ref->ref.offset < graph->node_by_offset_count &&
          graph->node_by_offset[ref->ref.offset] != SIZE_MAX) {
        const M68kRenderTypedFlowNode *node = &graph->nodes[graph->node_by_offset[ref->ref.offset]];
        if (node->has_in && graph->call_inputs_enabled) {
          M68kRenderTypedState typed;
          M68kRenderPlatformState platform;
          uint8_t reg = ref->ref.base_reg;
          typed_flow_instruction_input(lookup, &decode->sections[ref->section_index], node, &typed, &platform);
          M68kHardwareRelativeBase hardware;
          int raw_hardware = !typed.app_addr_regs[reg].known &&
            typed_raw_hardware_value(&typed.addr_regs[reg], &hardware);
          contradicted = !m68k_bitset_u32_has(platform.address_app_base_known, reg) &&
            (raw_hardware || platform.relative_hardware[reg].offsets.count != 0U ||
             m68k_bitset_u32_has(platform.address_hardware_base_known, reg) ||
             m68k_bitset_u32_has(platform.address_base_known, reg) ||
             m68k_bitset_u32_has(platform.address_layout_base_known, reg));
        }
      }
    }
    if (contradicted) continue;
    if (kept != i) lookup->app_slot_refs[kept] = *ref;
    if (lookup->app_slot_refs[kept].ref.symbol_name)
      lookup->app_slot_refs[kept].ref.symbol_name = lookup->app_slot_refs[kept].symbol_name;
    ++kept;
  }
  lookup->app_slot_ref_count = kept;
}

#include "m68k_counter_relative_loop.inc"

static int typed_flow_record_final_accesses(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, const M68kRenderTypedFlowWorkflow *workflow) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || workflow == NULL) return -1;
  if (workflow->graphs == NULL) return 0;
  if (workflow->section_count != decode->section_count) return -1;
  lookup->address_value_consumer_count = 0U;
  lookup->typed_access_count = 0U;
  lookup->hardware_address_use_count = 0U;
  lookup->affine_address_use_count = 0U;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderTypedFlowGraph *graph = &workflow->graphs[section_index];
    size_t node_index;
    for (node_index = 0U; node_index < graph->node_count; ++node_index) {
      M68kRenderTypedState ignored_typed_state;
      M68kRenderPlatformState ignored_platform_state;
      if (graph->nodes[node_index].has_in == 0U) continue;
      if (typed_flow_process_node(lookup, decode, accepted_start, section, &graph->nodes[node_index], 0,
          1, &ignored_typed_state, &ignored_platform_state, NULL) != 0) {
        return -1;
      }
    }
    if (hardware_relative_analyze_graph(lookup, section, graph, workflow->arena) != 0) return -1;
  }
  return 0;
}

static int candidate_lea_app_base_address_to_address_reg(const M68kDecodeCandidate *candidate, uint8_t *out_reg,
  int16_t *out_displacement);

static int render_lookup_record_typed_app_slot_pointer_accesses(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL ||
      lookup->object == NULL || lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderTypedAppAddressValue app_regs[8];
    M68kRenderPlatformState empty_platform_state;
    size_t candidate_index;
    memset(app_regs, 0, sizeof(app_regs));
    memset(&empty_platform_state, 0, sizeof(empty_platform_state));
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      size_t operand_index;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      for (operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U; ++operand_index) {
        uint8_t base_reg = 0U;
        int16_t displacement = 0;
        uint16_t struct_id;
        AmigaOsResolvedStructFieldInfo field;
        char field_expr[96];
        M68kRenderTypedProvenance provenance;
        if (!operand_is_address_displacement_local(&instruction.operands[operand_index], &base_reg,
            &displacement) || base_reg >= 8U || !app_regs[base_reg].known) {
          continue;
        }
        struct_id = lookup_typed_app_slot_struct_id(lookup, app_regs[base_reg].displacement);
        if (struct_id == AMIGA_OS_STRUCT_ID_NONE)
          struct_id = lookup_app_base_field_slot_struct_id(lookup, app_regs[base_reg].displacement);
        if (struct_id == AMIGA_OS_STRUCT_ID_NONE ||
            !amiga_os_resolve_struct_field_by_struct_id(struct_id, displacement, 0, &field) ||
            !amiga_os_resolve_struct_field_symbol_expr_by_struct_id(struct_id, displacement, 0,
              field_expr, sizeof(field_expr))) {
          continue;
        }
        provenance = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_APP_SLOT, section->section_index,
          candidate->offset);
        if (render_lookup_add_typed_access(lookup, section->section_index, candidate->offset,
            (uint8_t)operand_index, base_reg, displacement, struct_id, &field, field_expr, &provenance) != 0) {
          return -1;
        }
      }
      if (instruction_has_terminal_state_flow_local(&instruction)) {
        memset(app_regs, 0, sizeof(app_regs));
        continue;
      }
      if (instruction.operand_count >= 2U) {
        const M68kOperandIR *source = &instruction.operands[0];
        const M68kOperandIR *dest = &instruction.operands[instruction.operand_count - 1U];
        uint8_t dest_reg = 0U;
        uint8_t app_address_reg = 0U;
        int16_t app_address_displacement = 0;
        if (operand_address_register_index_local(dest, &dest_reg) && dest_reg < 8U) {
          uint8_t source_reg = 0U;
          uint8_t source_base_reg = 0U;
          int16_t source_displacement = 0;
          int32_t next_displacement = 0;
          size_t app_ref_index;
          int found_app_ref = 0;
          app_regs[dest_reg].known = 0U;
          app_regs[dest_reg].displacement = 0;
          if (candidate_lea_app_base_address_to_address_reg(candidate, &app_address_reg,
              &app_address_displacement) && app_address_reg == dest_reg) {
            app_regs[dest_reg].known = 1U;
            app_regs[dest_reg].displacement = app_address_displacement;
          } else if ((instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
              instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
              operand_address_register_index_local(source, &source_reg) && source_reg < 8U &&
              app_regs[source_reg].known) {
            app_regs[dest_reg] = app_regs[source_reg];
          } else if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_LEA) {
            for (app_ref_index = 0U; app_ref_index < lookup->app_slot_ref_count; ++app_ref_index) {
              const M68kRenderAppSlotRef *ref = &lookup->app_slot_refs[app_ref_index];
              if (ref->section_index == section->section_index && ref->ref.offset == candidate->offset &&
                  ref->ref.operand_index == 0U) {
                next_displacement = ref->ref.displacement;
                found_app_ref = 1;
                break;
              }
            }
            if (!found_app_ref && (!operand_is_address_memory_local(source, &source_base_reg,
                &source_displacement) || source_base_reg >= 8U)) {
              continue;
            }
            if (!found_app_ref && app_regs[source_base_reg].known) {
              next_displacement = (int32_t)app_regs[source_base_reg].displacement + (int32_t)source_displacement;
            } else if (!found_app_ref && render_state_operand_uses_app_base(&empty_platform_state, source_base_reg,
                source_displacement)) {
              next_displacement = source_displacement;
            } else if (!found_app_ref) {
              continue;
            }
            if (next_displacement >= INT16_MIN && next_displacement <= INT16_MAX) {
              app_regs[dest_reg].known = 1U;
              app_regs[dest_reg].displacement = (int16_t)next_displacement;
            }
          }
        }
      }
    }
  }
  return 0;
}


static int candidate_data_target_for_operand(const M68kDecodeCandidate *candidate, uint32_t operand_index,
    size_t *out_section_index, uint32_t *out_offset) {
  size_t target_index;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (candidate == NULL || out_section_index == NULL || out_offset == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind != M68K_DECODE_TARGET_DATA || target->has_section == 0U ||
        target->has_operand == 0U || target->operand_index != operand_index) {
      continue;
    }
    *out_section_index = target->section_index;
    *out_offset = target->offset;
    return 1;
  }
  return 0;
}

static int candidate_relocated_target_for_operand(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate, uint32_t operand_index,
    size_t *out_section_index, uint32_t *out_offset) {
  uint32_t relocation_offset;
  uint32_t relocation_end;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (lookup == NULL || section == NULL || candidate == NULL || out_section_index == NULL ||
      out_offset == NULL || candidate->byte_count > section->size ||
      candidate->offset > section->size - candidate->byte_count) {
    return 0;
  }
  relocation_end = candidate->offset + candidate->byte_count;
  for (relocation_offset = candidate->offset; relocation_offset < relocation_end; ++relocation_offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, relocation_offset);
    size_t relocated_operand_index = 0U;
    if (relocation == NULL || relocation->target_section_index >= lookup->section_count) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &relocated_operand_index) ||
        relocated_operand_index != operand_index) {
      continue;
    }
    *out_section_index = relocation->target_section_index;
    *out_offset = relocation->target_offset;
    return 1;
  }
  return 0;
}

static int candidate_operand_is_immediate_form(const M68kDecodeCandidate *candidate, uint32_t operand_index) {
  const M68kAsmOperandValue *operand;
  if (candidate == NULL || operand_index >= candidate->operand_count) return 0;
  if (candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_IMM) return 1;
  operand = &candidate->operands[operand_index];
  return candidate->operand_kinds[operand_index] == M68K_ASM_OPERAND_EA &&
    operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7U && operand->ea_reg == 4U;
}

static int candidate_loads_data_target_to_address_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg) {
  uint8_t dest_reg = 0U;
  if (candidate == NULL || instruction == NULL || out_section_index == NULL || out_offset == NULL ||
      out_reg == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA || instruction->operand_count != 2U ||
      !operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
    return 0;
  }
  /* Decoding owns PC-relative target resolution. LEA does not transfer
   * control, so any canonical local target on its source is its address. */
  if (candidate_local_target_for_operand(candidate, 0U, out_section_index, out_offset)) {
    *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static int candidate_moves_relocated_immediate_target_to_address_reg(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg) {
  uint8_t dest_reg = 0U;
  uint32_t relocation_offset;
  uint32_t relocation_end;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (lookup == NULL || section == NULL || candidate == NULL || instruction == NULL ||
      out_section_index == NULL || out_offset == NULL || out_reg == NULL ||
      candidate->byte_count > section->size || candidate->offset > section->size - candidate->byte_count) {
    return 0;
  }
  if ((candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
       candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA) ||
      candidate->operand_count != 2U || instruction->operand_count != 2U ||
      !candidate_operand_is_immediate_form(candidate, 0U) ||
      !operand_address_register_index_local(&instruction->operands[1], &dest_reg) || dest_reg == 7U) {
    return 0;
  }
  relocation_end = candidate->offset + candidate->byte_count;
  for (relocation_offset = candidate->offset + 2U; relocation_offset < relocation_end; ++relocation_offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, relocation_offset);
    size_t operand_index = 0U;
    if (relocation == NULL || relocation->size != 4U ||
        relocation->target_section_index >= lookup->section_count) {
      continue;
    }
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 0U) continue;
    *out_section_index = relocation->target_section_index;
    *out_offset = relocation->target_offset;
    *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static int candidate_loads_runtime_address_ref_target_to_address_reg(const M68kRenderLookup *lookup,
    size_t section_index, const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg) {
  size_t runtime_ref_index;
  uint8_t dest_reg = 0U;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (lookup == NULL || candidate == NULL || instruction == NULL ||
      out_section_index == NULL || out_offset == NULL || out_reg == NULL ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA || instruction->operand_count != 2U ||
      !operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
    return 0;
  }
  for (runtime_ref_index = lookup->runtime_address_ref_count; runtime_ref_index > 0U; --runtime_ref_index) {
    const M68kFact *fact = lookup->runtime_address_refs[runtime_ref_index - 1U].fact;
    if (fact == NULL || fact->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
        fact->section_index != section_index || fact->offset != candidate->offset ||
        fact->reason != 0U || !fact->has_runtime_address ||
        fact->target_section_index >= lookup->section_count) {
      continue;
    }
    *out_section_index = fact->target_section_index;
    *out_offset = fact->target_offset;
    *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static int append_render_lookup_platform_derived_summaries_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->platform_derived_summary_count; ++index) {
    const M68kRenderPlatformDerivedSummary *summary = &lookup->platform_derived_summaries[index];
    const AmigaOsCallOutputInfo *output;
    uint16_t existing_index;
    if (summary->section_index != section_analysis->section_index || summary->vector == NULL) continue;
    /* A local callable at this entry is the wrapper-side contract.  Its
     * platform result must be composed at the call boundary, where a
     * disagreement or capacity shortage has a caller-owned terminal; it is
     * not a second result on the wrapper summary. */
    for (existing_index = 0U; existing_index < section_analysis->function_summary_count; ++existing_index) {
      const M68kFunctionSummaryIR *existing = &section_analysis->function_summaries[existing_index];
      if (existing->callable_kind == M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT &&
          existing->entry_offset == summary->target_offset) {
        break;
      }
    }
    if (existing_index < section_analysis->function_summary_count) continue;
    if (lookup->policy != NULL) {
      for (existing_index = 0U; existing_index < lookup->policy->function_summary_count &&
           existing_index < M68K_ANALYSIS_FUNCTION_SUMMARY_LIMIT; ++existing_index) {
        const M68kAnalysisFunctionSummary *existing = &lookup->policy->function_summaries[existing_index];
        if (existing->has_section_index &&
            existing->callable_kind == M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT &&
            existing->section_index == section_analysis->section_index &&
            existing->entry_offset == summary->target_offset) {
          break;
        }
      }
      if (existing_index < lookup->policy->function_summary_count &&
          existing_index < M68K_ANALYSIS_FUNCTION_SUMMARY_LIMIT) continue;
    }
    output = &summary->vector->output;
    if (output->reg_kind == AMIGA_OS_REGISTER_NONE || output->reg_index >= 8U) continue;
    if (m68k_ir_section_analysis_append_function_summary_result(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, summary->target_offset, M68K_FUNCTION_SUMMARY_RESULT_PLATFORM_OUTPUT,
        output->reg_kind, output->reg_index, 0U, 0U, 0U, 0, NULL, NULL, NULL, NULL,
        NULL, 0U, 0, summary->vector->library_id, summary->vector->function_id,
        output->output_id) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_render_lookup_recovered_function_args_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->recovered_function_arg_count; ++index) {
    const M68kRenderRecoveredFunctionArg *arg = &lookup->recovered_function_args[index];
    const PlatformFactsV2CallInput *input = &arg->input;
    if (arg->section_index != section_analysis->section_index || arg->input_valid == 0U) continue;
    if (m68k_ir_section_analysis_append_recovered_function_arg(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, arg->function_offset, arg->stack_offset, arg->reg_kind, arg->reg_index,
        NULL, input->input_name, input->type_name, input->semantic_kind_name, input->value_domain_name,
        0U, 0, 0U, 0U, 0U, 0U, 0) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_render_lookup_typed_accesses_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->typed_access_count; ++index) {
    const M68kRenderTypedAccess *access = &lookup->typed_accesses[index];
    if (access->section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_recovered_platform_typed_access(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, access->offset, access->operand_index, access->base_reg,
        access->displacement, access->base_cursor, access->field_offset, access->struct_size, access->field_size,
        access->root_struct_name, access->owner_struct_name, access->field_name, access->field_expr,
        access->inherited, access->nested, access->provenance.kind, access->provenance.producer_operand_index, access->provenance.section_index,
        access->provenance.offset, &access->table_origin) != 0) {
      return -1;
    }
  }
  return 0;
}

typedef enum M68kRenderTableContractState {
  M68K_RENDER_TABLE_CONTRACT_NOT_TABLE_DERIVED = 0,
  M68K_RENDER_TABLE_CONTRACT_VALID = 1,
  M68K_RENDER_TABLE_CONTRACT_INVALID = 2
} M68kRenderTableContractState;

static int source_analysis_has_exact_table_expression(const M68kSourceAnalysisIR *source_analysis,
    const M68kAddressValueIR *value) {
  size_t section_index, expression_index;
  if (source_analysis == NULL || value == NULL || value->table_origin.has_origin == 0U ||
      value->table_origin.address_expression_id == 0U) return 0;
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    if (section->section_index != value->table_origin.consumer_section_index) continue;
    for (expression_index = 0U; expression_index < section->address_expression_count; ++expression_index) {
      const M68kAddressExpressionIR *expression = &section->address_expressions[expression_index];
      if (expression->id == value->table_origin.address_expression_id &&
          expression->consumer_section_index == value->table_origin.consumer_section_index &&
          expression->consumer_offset == value->table_origin.consumer_offset &&
          expression->base_section_index == value->table_origin.table_section_index &&
          expression->base_offset == value->table_origin.table_start_offset) return 1;
    }
  }
  return 0;
}

static M68kRenderTableContractState source_analysis_table_contract_state(
    const M68kSourceAnalysisIR *source_analysis, const M68kRenderTypedProvenance *provenance,
    const M68kAddressValueTableOriginIR *access_origin) {
  size_t section_index, value_index;
  const M68kAddressValueIR *match = NULL;
  if (source_analysis == NULL || provenance == NULL) {
    return M68K_RENDER_TABLE_CONTRACT_NOT_TABLE_DERIVED;
  }
  for (section_index = 0U; section_index < source_analysis->section_count; ++section_index) {
    const M68kSectionAnalysisIR *section = &source_analysis->sections[section_index];
    for (value_index = 0U; value_index < section->address_value_count; ++value_index) {
      const M68kAddressValueIR *value = &section->address_values[value_index];
      if (value->table_origin.has_origin == 0U) continue;
      if (provenance->kind == M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA) {
        if (value->origin_kind != M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA ||
            value->producer_section_index != provenance->section_index ||
            value->producer_offset != provenance->offset ||
            value->producer_operand_index != provenance->producer_operand_index) continue;
      } else if (access_origin == NULL || access_origin->has_origin == 0U) continue;
      /* Terminal state is produced by the canonical binder, so it is not a
       * producer identity.  Match the persisted table/consumer/expression
       * coordinates and selection domain, then gate on the canonical state
       * below. */
      if (access_origin != NULL && access_origin->has_origin != 0U &&
          (value->table_origin.has_origin == 0U ||
           value->table_origin.selection_kind != access_origin->selection_kind ||
           value->table_origin.table_section_index != access_origin->table_section_index ||
           value->table_origin.table_start_offset != access_origin->table_start_offset ||
           value->table_origin.consumer_section_index != access_origin->consumer_section_index ||
           value->table_origin.consumer_offset != access_origin->consumer_offset ||
           (access_origin->address_expression_id != 0U &&
            value->table_origin.address_expression_id != access_origin->address_expression_id) ||
           value->table_origin.entry_index != access_origin->entry_index ||
           value->table_origin.index_min != access_origin->index_min ||
           value->table_origin.index_max != access_origin->index_max))
        return M68K_RENDER_TABLE_CONTRACT_INVALID;
      if (match != NULL) return M68K_RENDER_TABLE_CONTRACT_INVALID;
      match = value;
    }
  }
  if (match == NULL) return M68K_RENDER_TABLE_CONTRACT_NOT_TABLE_DERIVED;
  if (match->table_origin.selection_kind == M68K_ADDRESS_VALUE_TABLE_SELECTION_TERMINAL ||
      match->render_outcome != M68K_ADDRESS_VALUE_RENDER_SYMBOLIC ||
      match->has_source_expression == 0U ||
      match->table_origin.consumer_section_index != match->producer_section_index ||
      match->table_origin.consumer_offset != match->producer_offset ||
      !source_analysis_has_exact_table_expression(source_analysis, match)) {
    return M68K_RENDER_TABLE_CONTRACT_INVALID;
  }
  return M68K_RENDER_TABLE_CONTRACT_VALID;
}

void m68k_analysis_render_lookup_reconcile_typed_table_contracts(M68kRenderLookup *lookup,
    M68kSourceAnalysisIR *source_analysis) {
  size_t index, retained;
  if (lookup == NULL || source_analysis == NULL) return;
  retained = 0U;
  for (index = 0U; index < lookup->typed_access_count; ++index) {
    M68kRenderTypedAccess *access = &lookup->typed_accesses[index];
    if (source_analysis_table_contract_state(source_analysis, &access->provenance, &access->table_origin) ==
        M68K_RENDER_TABLE_CONTRACT_INVALID) continue;
    if (retained != index) lookup->typed_accesses[retained] = *access;
    ++retained;
  }
  lookup->typed_access_count = retained;
  for (index = 0U; index < lookup->typed_storage_slot_count; ++index) {
    M68kRenderTypedStorageSlot *slot = &lookup->typed_storage_slots[index];
    if (source_analysis_table_contract_state(source_analysis, &slot->value.provenance, &slot->value.table_origin) !=
        M68K_RENDER_TABLE_CONTRACT_INVALID) continue;
    slot->conflicted = 1U;
    typed_stored_value_clear(&slot->value);
  }
  for (index = 0U; index < lookup->address_value_consumer_count; ++index) {
    M68kRenderTypedAddressConsumer *consumer = &lookup->address_value_consumers[index];
    if (source_analysis_table_contract_state(source_analysis, &consumer->provenance, &consumer->value.table_origin) !=
        M68K_RENDER_TABLE_CONTRACT_INVALID) continue;
    typed_stored_value_clear(&consumer->value);
  }
  for (index = 0U; index < source_analysis->section_count; ++index) {
    M68kSectionAnalysisIR *section = &source_analysis->sections[index];
    size_t access_index;
    retained = 0U;
    for (access_index = 0U; access_index < section->recovered_platform_typed_access_count; ++access_index) {
      M68kRecoveredPlatformTypedAccessIR *access = &section->recovered_platform_typed_accesses[access_index];
      M68kRenderTypedProvenance provenance;
      memset(&provenance, 0, sizeof(provenance));
      provenance.kind = access->type_provenance_kind;
      provenance.producer_operand_index = access->type_provenance_operand_index;
      provenance.section_index = access->type_provenance_section_index;
      provenance.offset = access->type_provenance_offset;
      {
        M68kAddressValueTableOriginIR table_origin;
        memset(&table_origin, 0, sizeof(table_origin));
        if (access->has_table_origin != 0U) {
          table_origin.has_origin = 1U;
          table_origin.selection_kind = access->table_selection_kind;
          table_origin.terminal_kind = access->table_terminal_kind;
          table_origin.table_section_index = access->table_section_index;
          table_origin.table_start_offset = access->table_start_offset;
          table_origin.consumer_section_index = access->table_consumer_section_index;
          table_origin.consumer_offset = access->table_consumer_offset;
          table_origin.address_expression_id = access->table_address_expression_id;
          table_origin.entry_index = access->table_entry_index;
          table_origin.index_min = access->table_index_min;
          table_origin.index_max = access->table_index_max;
        }
      if (source_analysis_table_contract_state(source_analysis, &provenance, &table_origin) ==
          M68K_RENDER_TABLE_CONTRACT_INVALID) continue;
      }
      if (retained != access_index) section->recovered_platform_typed_accesses[retained] = *access;
      ++retained;
    }
    section->recovered_platform_typed_access_count = retained;
  }
}

/* Policy config is only an analysis input.  Export its canonical summary once
 * at the callable/table owner so call-input consumers can link to a durable
 * source-analysis fact without reconstructing interface context from policy. */
static int append_render_lookup_function_summaries_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  uint16_t index;
  if (lookup == NULL || lookup->policy == NULL || section_analysis == NULL) return 0;
  for (index = 0U; index < lookup->policy->function_summary_count &&
       index < M68K_ANALYSIS_FUNCTION_SUMMARY_LIMIT; ++index) {
    const M68kAnalysisFunctionSummary *configured = &lookup->policy->function_summaries[index];
    M68kFunctionSummaryIR summary;
    if (!configured->has_section_index || configured->function_summary_id[0] == '\0' ||
        configured->section_index != section_analysis->section_index) continue;
    memset(&summary, 0, sizeof(summary));
    snprintf(summary.function_summary_id, sizeof(summary.function_summary_id), "%s",
      configured->function_summary_id);
    summary.callable_section_index = configured->section_index;
    summary.entry_offset = configured->entry_offset;
    summary.table_offset = configured->table_offset;
    summary.entry_count = configured->entry_count;
    summary.callable_kind = configured->callable_kind;
    summary.input_count = configured->input_count;
    summary.register_effect_state = configured->register_effect_state;
    summary.memory_effect_state = configured->memory_effect_state;
    summary.escape_effect_state = configured->escape_effect_state;
    summary.memory_effect_count = configured->memory_effect_count;
    summary.escape_count = configured->escape_count;
    summary.effects_invalid = configured->effects_invalid;
    summary.location_effect_count = configured->location_effect_count;
    memcpy(summary.inputs, configured->inputs, sizeof(summary.inputs));
    for (uint8_t result_index = 0U; result_index < configured->result_count; ++result_index) {
      const M68kAnalysisFunctionSummaryResult *configured_result = &configured->results[result_index];
      M68kFunctionSummaryResultIR *result = &summary.results[summary.result_count++];
      result->kind = M68K_FUNCTION_SUMMARY_RESULT_IDENTITY_INPUT;
      result->location = configured_result->location;
      result->identity_input_index = configured_result->input_index;
    }
    summary.result_count = configured->result_count;
    summary.result_contract_invalid = configured->result_contract_invalid;
    memcpy(summary.location_effects, configured->location_effects, sizeof(summary.location_effects));
    memcpy(summary.memory_effects, configured->memory_effects, sizeof(summary.memory_effects));
    memcpy(summary.escapes, configured->escapes, sizeof(summary.escapes));
    if (m68k_ir_section_analysis_append_function_summary(section_analysis, &summary) != 0) return -1;
    {
      size_t use_index;
      for (use_index = 0U; use_index < lookup->function_summary_use_count; ++use_index) {
        const M68kFunctionSummaryUseIR *use = &lookup->function_summary_uses[use_index];
        if (strcmp(use->function_summary_id, configured->function_summary_id) != 0) continue;
        if (m68k_ir_section_analysis_append_function_summary_use(section_analysis, use) != 0) return -1;
      }
    }
  }
  for (index = 0U; index < lookup->inferred_function_summary_count; ++index) {
    const M68kAnalysisFunctionSummary *inferred = &lookup->inferred_function_summaries[index].summary;
    M68kFunctionSummaryIR summary;
    size_t use_index;
    if (!inferred->has_section_index || inferred->section_index != section_analysis->section_index) continue;
    memset(&summary, 0, sizeof(summary));
    snprintf(summary.function_summary_id, sizeof(summary.function_summary_id), "%s", inferred->function_summary_id);
    summary.callable_section_index = inferred->section_index;
    summary.entry_offset = inferred->entry_offset;
    summary.table_offset = inferred->table_offset;
    summary.entry_count = inferred->entry_count;
    summary.callable_kind = inferred->callable_kind;
    summary.input_count = inferred->input_count;
    summary.register_effect_state = inferred->register_effect_state;
    summary.memory_effect_state = inferred->memory_effect_state;
    summary.escape_effect_state = inferred->escape_effect_state;
    summary.memory_effect_count = inferred->memory_effect_count;
    summary.escape_count = inferred->escape_count;
    summary.effects_invalid = inferred->effects_invalid;
    summary.location_effect_count = inferred->location_effect_count;
    summary.terminal_reason = lookup->inferred_function_summaries[index].terminal_reason;
    summary.direct_scc_anchor_section_index =
      lookup->inferred_function_summaries[index].direct_scc_anchor_section_index;
    summary.direct_scc_anchor_entry_offset =
      lookup->inferred_function_summaries[index].direct_scc_anchor_entry_offset;
    summary.direct_scc_size = lookup->inferred_function_summaries[index].direct_scc_size;
    summary.direct_scc_ordinal = lookup->inferred_function_summaries[index].direct_scc_ordinal;
    memcpy(summary.inputs, inferred->inputs, sizeof(summary.inputs));
    for (uint8_t result_index = 0U; result_index < inferred->result_count; ++result_index) {
      const M68kAnalysisFunctionSummaryResult *inferred_result = &inferred->results[result_index];
      M68kFunctionSummaryResultIR *result = &summary.results[summary.result_count++];
      result->kind = inferred_result->kind == M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_HARDWARE_BASE ?
        M68K_FUNCTION_SUMMARY_RESULT_HARDWARE_BASE : M68K_FUNCTION_SUMMARY_RESULT_IDENTITY_INPUT;
      result->hardware_base_id = inferred_result->hardware_base_id;
      result->location = inferred_result->location;
      result->identity_input_index = inferred_result->input_index;
    }
    summary.result_count = inferred->result_count;
    summary.result_contract_invalid = inferred->result_contract_invalid;
    memcpy(summary.location_effects, inferred->location_effects, sizeof(summary.location_effects));
    memcpy(summary.memory_effects, inferred->memory_effects, sizeof(summary.memory_effects));
    memcpy(summary.escapes, inferred->escapes, sizeof(summary.escapes));
    if (m68k_ir_section_analysis_append_function_summary(section_analysis, &summary) != 0) return -1;
    for (use_index = 0U; use_index < lookup->function_summary_use_count; ++use_index) {
      const M68kFunctionSummaryUseIR *use = &lookup->function_summary_uses[use_index];
      if (strcmp(use->function_summary_id, inferred->function_summary_id) != 0) continue;
      if (m68k_ir_section_analysis_append_function_summary_use(section_analysis, use) != 0) return -1;
    }
  }
  for (size_t thunk_index = 0U; thunk_index < lookup->platform_call_thunk_count; ++thunk_index) {
    const M68kPlatformCallThunkIR *thunk = &lookup->platform_call_thunks[thunk_index];
    if (thunk->wrapper_section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_platform_call_thunk(section_analysis, thunk) != 0) return -1;
  }
  /* Graph-capacity terminals have no callable summary by definition.  Export
   * their stable caller edge directly so the omitted node is visible rather
   * than becoming an unrecorded unknown call. */
  for (size_t use_index = 0U; use_index < lookup->function_summary_use_count; ++use_index) {
    const M68kFunctionSummaryUseIR *use = &lookup->function_summary_uses[use_index];
    if (use->terminal_reason != M68K_FUNCTION_SUMMARY_TERMINAL_DIRECT_GRAPH_CAPACITY ||
        use->caller_section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_function_summary_use(section_analysis, use) != 0) return -1;
  }
  return 0;
}

static int append_render_lookup_affine_address_evidence_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL) return -1;
  for (index = 0U; index < lookup->affine_address_use_count; ++index) {
    const M68kRenderAffineAddressUse *use = &lookup->affine_address_uses[index];
    M68kAffineAddressEvidenceIR evidence;
    if (use->section_index != section_analysis->section_index) continue;
    memset(&evidence, 0, sizeof(evidence));
    evidence.consumer_section_index = (uint32_t)use->section_index;
    evidence.consumer_offset = use->offset;
    evidence.operand_index = use->operand_index;
    evidence.base_register = use->base_register;
    evidence.origin_section_index = (uint32_t)use->origin_section_index;
    evidence.origin_offset = use->origin_offset;
    evidence.target_section_index = (uint32_t)use->target_section_index;
    evidence.target_offset = use->target_offset;
    evidence.signed_addend = use->signed_addend;
    if (m68k_ir_section_analysis_append_affine_address_evidence(section_analysis, &evidence) != 0) return -1;
  }
  return 0;
}

static int append_render_lookup_unresolved_typed_accesses_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->unresolved_typed_access_count; ++index) {
    const M68kRenderUnresolvedTypedAccess *access = &lookup->unresolved_typed_accesses[index];
    if (access->section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_recovered_platform_unresolved_typed_access(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, access->offset, access->operand_index, access->base_reg,
        access->displacement, access->struct_size, access->access_size, access->root_struct_name, access->classification,
        access->container_candidate_count, access->container_struct_name, access->container_field_expr,
        access->refinement_applied, access->refined_struct_name, access->provenance.kind,
        access->provenance.section_index, access->provenance.offset) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_render_lookup_bootblock_disk_reads_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->bootblock_disk_read_count; ++index) {
    const M68kRenderBootblockDiskRead *read = &lookup->bootblock_disk_reads[index];
    if (read->section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_recovered_platform_disk_read(section_analysis,
        read->offset, read->command_value, read->command_name, read->disk_offset,
        read->byte_length, read->destination_addr, read->source_kind) != 0) {
      return -1;
    }
  }
  return 0;
}

static int append_render_lookup_bootblock_runtime_copies_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->bootblock_runtime_copy_count; ++index) {
    const M68kRenderBootblockRuntimeCopy *copy = &lookup->bootblock_runtime_copies[index];
    if (copy->section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_recovered_platform_runtime_copy(section_analysis,
        copy->offset, copy->source_addr, copy->destination_addr, copy->byte_length,
        copy->handoff_addr, copy->source_kind) != 0) {
      return -1;
    }
  }
  return 0;
}

static int global_base_observation_add(M68kRenderGlobalBaseObservation **observations, size_t *count,
    size_t *capacity, size_t section_index, uint32_t offset, uint8_t index_reg, int16_t lvo,
    Arena *arena) {
  size_t index;
  if (observations == NULL || count == NULL || capacity == NULL || arena == NULL) return -1;
  for (index = 0U; index < *count; ++index) {
    M68kRenderGlobalBaseObservation *observation = &(*observations)[index];
    size_t lvo_index;
    if (observation->section_index != section_index || observation->offset != offset ||
        observation->index_reg != index_reg) {
      continue;
    }
    for (lvo_index = 0U; lvo_index < observation->lvo_count; ++lvo_index)
      if (observation->lvos[lvo_index] == lvo) return 0;
    if (observation->lvo_count < sizeof(observation->lvos) / sizeof(observation->lvos[0]))
      observation->lvos[observation->lvo_count++] = lvo;
    return 0;
  }
  if (*count == *capacity) {
    size_t next_capacity = *capacity == 0U ? 16U : *capacity * 2U;
    M68kRenderGlobalBaseObservation *grown =
      (M68kRenderGlobalBaseObservation *)arena_realloc_copy(arena, *observations,
        *capacity * sizeof(*grown), next_capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    *observations = grown;
    *capacity = next_capacity;
  }
  memset(&(*observations)[*count], 0, sizeof((*observations)[*count]));
  (*observations)[*count].section_index = section_index;
  (*observations)[*count].offset = offset;
  (*observations)[*count].index_reg = index_reg;
  (*observations)[*count].lvos[0] = lvo;
  (*observations)[*count].lvo_count = 1U;
  ++(*count);
  return 0;
}

static int library_has_all_observed_lvos(const char *base_name, const M68kRenderGlobalBaseObservation *observation) {
  size_t index;
  if (base_name == NULL || observation == NULL || observation->lvo_count == 0U) return 0;
  for (index = 0U; index < observation->lvo_count; ++index) {
    if (amiga_os_find_library_vector(base_name, observation->lvos[index]) == NULL) return 0;
  }
  return 1;
}

static int library_id_seen_local(const uint16_t *ids, size_t count, uint16_t id) {
  size_t index;
  for (index = 0U; index < count; ++index)
    if (ids[index] == id) return 1;
  return 0;
}

static const char *unique_library_for_observed_lvos(const M68kRenderGlobalBaseObservation *observation) {
  uint16_t seen_ids[AMIGA_OS_LIBRARY_VECTOR_COUNT];
  size_t seen_count = 0U;
  uint16_t matched_library_id = 0U;
  size_t index;
  if (observation == NULL || observation->lvo_count == 0U) return NULL;
  for (index = 0U; index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++index) {
    const AmigaOsLibraryVectorInfo *vector = amiga_os_library_vector_at(index);
    const char *library_name;
    const char *base_name;
    if (vector == NULL) continue;
    if (library_id_seen_local(seen_ids, seen_count, vector->library_id)) continue;
    if (seen_count < sizeof(seen_ids) / sizeof(seen_ids[0])) seen_ids[seen_count++] = vector->library_id;
    library_name = platform_facts_v2_library_name_for_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, vector->library_id);
    base_name = render_lookup_amiga_library_base_name_for_library_name(library_name);
    if (library_name == NULL || base_name == NULL) continue;
    if (!library_has_all_observed_lvos(base_name, observation)) continue;
    if (matched_library_id != 0U && matched_library_id != vector->library_id) return NULL;
    matched_library_id = vector->library_id;
  }
  return platform_facts_v2_library_name_for_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, matched_library_id);
}

static M68kAddressValueIR *section_analysis_find_equivalent_address_value(
    M68kSectionAnalysisIR *section_analysis, const M68kAddressValueIR *candidate) {
  size_t index;
  if (section_analysis == NULL || candidate == NULL) return NULL;
  for (index = 0U; index < section_analysis->address_value_count; ++index) {
    M68kAddressValueIR *existing = &section_analysis->address_values[index];
    if (existing->source_value != candidate->source_value ||
        existing->producer_section_index != candidate->producer_section_index ||
        existing->producer_offset != candidate->producer_offset ||
        existing->producer_operand_index != candidate->producer_operand_index ||
        existing->origin_kind != candidate->origin_kind || existing->pointer_width != candidate->pointer_width ||
        existing->resolution != candidate->resolution || existing->terminal_kind != candidate->terminal_kind ||
        existing->render_outcome != candidate->render_outcome || existing->has_target != candidate->has_target ||
        existing->target_section_index != candidate->target_section_index ||
        existing->target_offset != candidate->target_offset || existing->transfer_count != candidate->transfer_count ||
        existing->candidate_target_count != candidate->candidate_target_count ||
        memcmp(&existing->table_origin, &candidate->table_origin, sizeof(existing->table_origin)) != 0 ||
        strcmp(existing->pointee_struct_name, candidate->pointee_struct_name) != 0 ||
        memcmp(existing->transfers, candidate->transfers,
          candidate->transfer_count * sizeof(candidate->transfers[0])) != 0 ||
        memcmp(existing->candidate_source_values, candidate->candidate_source_values,
          candidate->candidate_target_count * sizeof(candidate->candidate_source_values[0])) != 0 ||
        memcmp(existing->candidate_target_section_indices, candidate->candidate_target_section_indices,
          candidate->candidate_target_count * sizeof(candidate->candidate_target_section_indices[0])) != 0 ||
        memcmp(existing->candidate_target_offsets, candidate->candidate_target_offsets,
          candidate->candidate_target_count * sizeof(candidate->candidate_target_offsets[0])) != 0) {
      continue;
    }
    return existing;
  }
  return NULL;
}

static int append_render_lookup_address_value_consumers_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL) return 0;
  for (index = 0U; index < lookup->address_value_consumer_count; ++index) {
    const M68kRenderTypedAddressConsumer *observed = &lookup->address_value_consumers[index];
    M68kAddressValueConsumerIR consumer;
    M68kAddressValueIR address_value;
    M68kAddressValueIR *existing_address_value;
    if (observed->section_index != section_analysis->section_index) continue;
    consumer = observed->fact;
    consumer.id = (uint32_t)section_analysis->address_value_consumer_count + 1U;
    consumer.address_value_id = (uint32_t)section_analysis->address_value_count + 1U;
    memset(&address_value, 0, sizeof(address_value));
    address_value.id = consumer.address_value_id;
    address_value.source_value = observed->source_value;
    address_value.producer_section_index = (uint32_t)observed->provenance.section_index;
    address_value.producer_offset = observed->provenance.offset;
    address_value.producer_operand_index = observed->provenance.producer_operand_index;
    address_value.origin_kind = observed->provenance.kind;
    address_value.pointer_width = 4U;
    address_value.table_origin = observed->value.table_origin;
    if (address_value.table_origin.has_origin == 0U &&
        consumer.kind == M68K_ADDRESS_VALUE_CONSUMER_CALLBACK_INPUT &&
        consumer.contract_section_index != UINT32_MAX) {
      address_value.table_origin.has_origin = 1U;
      address_value.table_origin.table_section_index = consumer.contract_section_index;
      address_value.table_origin.table_start_offset = consumer.contract_offset;
      address_value.table_origin.consumer_section_index = (uint32_t)section_analysis->section_index;
      address_value.table_origin.consumer_offset = consumer.offset;
      address_value.table_origin.entry_index = UINT32_MAX;
      address_value.table_origin.selection_kind = M68K_ADDRESS_VALUE_TABLE_SELECTION_NONE;
    }
    address_value.resolution = observed->resolution;
    address_value.has_target = observed->has_target;
    address_value.target_section_index = (uint32_t)observed->target_section_index;
    address_value.target_offset = observed->target_offset;
    address_value.candidate_target_count = observed->candidate_target_count;
    memcpy(address_value.candidate_source_values, observed->candidate_source_values,
      sizeof(address_value.candidate_source_values));
    /* Native lookup indices are size_t; the public IR stores uint32_t.
     * Copy elements, not the first half of a 64-bit index array. */
    for (size_t i = 0U; i < observed->candidate_target_count; ++i) {
      address_value.candidate_target_section_indices[i] = observed->candidate_target_section_indices[i] >= UINT32_MAX
        ? UINT32_MAX : (uint32_t)observed->candidate_target_section_indices[i];
      address_value.candidate_target_offsets[i] = observed->candidate_target_offsets[i];
    }
    memcpy(address_value.transfers, observed->provenance.transfers, sizeof(address_value.transfers));
    address_value.transfer_count = observed->provenance.transfer_count;
    address_value.transfer_truncated = observed->provenance.transfer_truncated;
    address_value.propagation_depth = observed->provenance.transfer_count;
    snprintf(address_value.pointee_struct_name, sizeof(address_value.pointee_struct_name), "%s",
      consumer.pointee_struct_name);
    if (observed->resolution == M68K_ADDRESS_VALUE_RESOLUTION_RESOLVED) {
      address_value.terminal_kind = M68K_ADDRESS_VALUE_TERMINAL_RESOLVED;
      address_value.has_source_expression = observed->provenance.kind == M68K_PLATFORM_TYPE_PROVENANCE_IMMEDIATE;
      address_value.render_outcome = address_value.has_source_expression != 0U ?
        M68K_ADDRESS_VALUE_RENDER_SYMBOLIC : M68K_ADDRESS_VALUE_RENDER_NON_SOURCE;
      address_value.review_class = address_value.has_source_expression != 0U ?
        M68K_ADDRESS_VALUE_REVIEW_FIXTURE_POSITIVE : M68K_ADDRESS_VALUE_REVIEW_OPPORTUNITY;
      snprintf(address_value.terminal_reason, sizeof(address_value.terminal_reason), "%s",
        address_value.has_source_expression != 0U ? "mapped source producer" : "no renderable source producer");
    } else if (observed->resolution == M68K_ADDRESS_VALUE_RESOLUTION_FINITE_CANDIDATE_TARGETS ||
        observed->resolution == M68K_ADDRESS_VALUE_RESOLUTION_AMBIGUOUS_TARGET ||
        observed->resolution == M68K_ADDRESS_VALUE_RESOLUTION_TYPE_CONFLICT) {
      address_value.terminal_kind = M68K_ADDRESS_VALUE_TERMINAL_AMBIGUOUS;
      address_value.render_outcome = M68K_ADDRESS_VALUE_RENDER_NON_SOURCE;
      address_value.review_class = M68K_ADDRESS_VALUE_REVIEW_OPPORTUNITY;
      snprintf(address_value.terminal_reason, sizeof(address_value.terminal_reason), "ambiguous target identity");
    } else if (observed->resolution == M68K_ADDRESS_VALUE_RESOLUTION_OUTSIDE_KNOWN_ADDRESS_SPACE) {
      address_value.terminal_kind = M68K_ADDRESS_VALUE_TERMINAL_EXTERNAL;
      address_value.render_outcome = M68K_ADDRESS_VALUE_RENDER_NON_SOURCE;
      address_value.review_class = M68K_ADDRESS_VALUE_REVIEW_OPPORTUNITY;
      snprintf(address_value.terminal_reason, sizeof(address_value.terminal_reason), "target outside source address space");
    } else if (observed->resolution == M68K_ADDRESS_VALUE_RESOLUTION_INVALID_TARGET) {
      address_value.terminal_kind = M68K_ADDRESS_VALUE_TERMINAL_INVALID;
      address_value.render_outcome = M68K_ADDRESS_VALUE_RENDER_INVALID;
      address_value.has_source_expression = observed->provenance.kind == M68K_PLATFORM_TYPE_PROVENANCE_IMMEDIATE;
      address_value.review_class = M68K_ADDRESS_VALUE_REVIEW_INVALID;
      snprintf(address_value.terminal_reason, sizeof(address_value.terminal_reason),
        "mapped target is not representable source storage");
    } else if (observed->resolution == M68K_ADDRESS_VALUE_RESOLUTION_CANDIDATE_OVERFLOW) {
      address_value.terminal_kind = M68K_ADDRESS_VALUE_TERMINAL_CANDIDATE_OVERFLOW;
      address_value.render_outcome = M68K_ADDRESS_VALUE_RENDER_NON_SOURCE;
      address_value.review_class = M68K_ADDRESS_VALUE_REVIEW_OPPORTUNITY;
      snprintf(address_value.terminal_reason, sizeof(address_value.terminal_reason),
        "candidate merge exceeded exact analysis capacity");
    } else {
      address_value.terminal_kind = M68K_ADDRESS_VALUE_TERMINAL_NO_PROVEN_TRANSFER_CONTRACT;
      address_value.render_outcome = M68K_ADDRESS_VALUE_RENDER_NON_SOURCE;
      address_value.review_class = M68K_ADDRESS_VALUE_REVIEW_OPPORTUNITY;
      snprintf(address_value.terminal_reason, sizeof(address_value.terminal_reason), "no proven transfer contract");
    }
    existing_address_value = section_analysis_find_equivalent_address_value(section_analysis, &address_value);
    if (existing_address_value != NULL) {
      consumer.address_value_id = existing_address_value->id;
      if (observed->has_storage != 0U) {
        M68kPointerStoreIR storage = observed->storage;
        storage.address_value_id = existing_address_value->id;
        if (m68k_ir_section_analysis_append_pointer_store(section_analysis, &storage) != 0) return -1;
      }
      if (m68k_ir_section_analysis_append_address_value_consumer(section_analysis, &consumer) != 0) return -1;
      continue;
    }
    if (observed->has_storage != 0U) {
      M68kPointerStoreIR storage = observed->storage;
      storage.address_value_id = address_value.id;
      if (m68k_ir_section_analysis_append_pointer_store(section_analysis, &storage) != 0) return -1;
    }
    if (m68k_ir_section_analysis_append_address_value_consumer(section_analysis, &consumer) != 0 ||
        m68k_ir_section_analysis_append_address_value(section_analysis, &address_value) != 0) return -1;
  }
  return 0;
}

static int render_lookup_add_global_base_slot(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    const char *library_name, size_t source_section_index, uint32_t source_offset) {
  size_t index;
  M68kRenderGlobalBaseSlot *grown;
  size_t next_capacity;
  uint16_t library_id;
  const char *canonical_library_name;
  uint8_t has_source = source_section_index != SIZE_MAX && source_offset != UINT32_MAX;
  if (lookup == NULL || library_name == NULL || library_name[0] == '\0') return 0;
  if (!platform_facts_v2_library_id_for_library_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, library_name, &library_id))
    return 0;
  canonical_library_name = platform_facts_v2_library_name_for_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, library_id);
  if (canonical_library_name == NULL || canonical_library_name[0] == '\0' ||
      render_lookup_amiga_library_base_name_for_library_name(canonical_library_name) == NULL) {
    return 0;
  }
  for (index = 0U; index < lookup->global_base_slot_count; ++index) {
    M68kRenderGlobalBaseSlot *slot = &lookup->global_base_slots[index];
    if (slot->section_index == section_index && slot->offset == offset) {
      if (slot->has_library_id != 0U && slot->library_id != library_id) {
        slot->has_library_id = 0U;
        slot->library_id = 0U;
        slot->library_name[0] = '\0';
        slot->conflicted = 1U;
        return 0;
      }
      if (slot->conflicted != 0U) return 0;
      slot->has_library_id = 1U;
      slot->library_id = library_id;
      snprintf(slot->library_name, sizeof(slot->library_name), "%s", canonical_library_name);
      if (has_source && slot->has_source == 0U) {
        slot->source_section_index = source_section_index;
        slot->source_offset = source_offset;
        slot->has_source = 1U;
      }
      return 0;
    }
  }
  if (lookup->global_base_slot_count == lookup->global_base_slot_capacity) {
    next_capacity = lookup->global_base_slot_capacity == 0U ? 8U : lookup->global_base_slot_capacity * 2U;
    grown = (M68kRenderGlobalBaseSlot *)render_lookup_grow_array(lookup, lookup->global_base_slots,
      lookup->global_base_slot_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->global_base_slots = grown;
    lookup->global_base_slot_capacity = next_capacity;
  }
  memset(&lookup->global_base_slots[lookup->global_base_slot_count], 0,
    sizeof(lookup->global_base_slots[lookup->global_base_slot_count]));
  lookup->global_base_slots[lookup->global_base_slot_count].section_index = section_index;
  lookup->global_base_slots[lookup->global_base_slot_count].offset = offset;
  lookup->global_base_slots[lookup->global_base_slot_count].source_section_index = source_section_index;
  lookup->global_base_slots[lookup->global_base_slot_count].source_offset = source_offset;
  lookup->global_base_slots[lookup->global_base_slot_count].has_source = has_source;
  lookup->global_base_slots[lookup->global_base_slot_count].has_library_id = 1U;
  lookup->global_base_slots[lookup->global_base_slot_count].library_id = library_id;
  snprintf(lookup->global_base_slots[lookup->global_base_slot_count].library_name,
    sizeof(lookup->global_base_slots[lookup->global_base_slot_count].library_name), "%s", canonical_library_name);
  ++lookup->global_base_slot_count;
  return 0;
}

static uint8_t render_lookup_normalized_app_slot_access_size(uint8_t access_size) {
  return access_size == 1U || access_size == 2U || access_size == 4U ? access_size : 0U;
}

static uint8_t render_lookup_base_field_slot_owner_kind(const char *owner_name) {
  return platform_state_name_is_app_base(owner_name) ? M68K_RENDER_BASE_FIELD_SLOT_OWNER_APP_BASE :
    M68K_RENDER_BASE_FIELD_SLOT_OWNER_NAMED;
}

static int render_lookup_base_field_slot_owner_matches(const M68kRenderBaseFieldSlot *slot,
    uint8_t owner_kind, const char *owner_name) {
  if (slot == NULL || owner_name == NULL || owner_name[0] == '\0') return 0;
  if (slot->owner_kind != owner_kind) return 0;
  if (owner_kind == M68K_RENDER_BASE_FIELD_SLOT_OWNER_APP_BASE) return 1;
  return strcmp(slot->owner_name, owner_name) == 0;
}

static int render_lookup_add_base_field_slot_with_symbol(M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, const char *library_name, const char *symbol_name, uint8_t value_kind,
    uint8_t observed_access_size, size_t source_section_index, uint32_t source_offset) {
  size_t index;
  M68kRenderBaseFieldSlot *grown;
  size_t next_capacity;
  uint8_t owner_kind = render_lookup_base_field_slot_owner_kind(owner_name);
  uint8_t has_source = source_section_index != SIZE_MAX && source_offset != UINT32_MAX;
  const char *slot_library_name = library_name != NULL ? library_name : "";
  uint8_t has_slot_library_id = 0U;
  uint16_t slot_library_id = 0U;
  uint8_t normalized_access_size = render_lookup_normalized_app_slot_access_size(observed_access_size);
  if (lookup == NULL || owner_name == NULL || owner_name[0] == '\0') return 0;
  if (value_kind == M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE ||
      value_kind == M68K_RENDER_BASE_FIELD_SLOT_DEVICE_BASE) {
    if (slot_library_name[0] == '\0' ||
        render_lookup_amiga_library_base_name_for_library_name(slot_library_name) == NULL) return 0;
    if (!platform_facts_v2_library_id_for_library_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot_library_name,
        &slot_library_id)) {
      return 0;
    }
    has_slot_library_id = 1U;
  } else if (value_kind == M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS) {
    if (owner_kind != M68K_RENDER_BASE_FIELD_SLOT_OWNER_APP_BASE) return 0;
  } else if (symbol_name == NULL || symbol_name[0] == '\0') {
    return 0;
  }
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    if (!render_lookup_base_field_slot_owner_matches(slot, owner_kind, owner_name) ||
        slot->displacement != displacement)
      continue;
    if (slot->conflicted) return 0;
    if (slot->value_kind == M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS && value_kind != M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS) {
      slot->value_kind = value_kind;
      if (slot_library_name[0] != '\0') {
        slot->has_library_id = has_slot_library_id;
        slot->library_id = slot_library_id;
        snprintf(slot->library_name, sizeof(slot->library_name), "%s", slot_library_name);
      }
      if (symbol_name != NULL && symbol_name[0] != '\0') {
        snprintf(slot->symbol_name, sizeof(slot->symbol_name), "%s", symbol_name);
      }
    } else if (value_kind == M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS) {
      /* The generic app-state access confirms the slot exists but must not erase a better name. */
    } else if (slot->value_kind != value_kind ||
        (slot->has_library_id && (!has_slot_library_id || slot->library_id != slot_library_id)) ||
        (slot->symbol_name[0] != '\0' && (symbol_name == NULL || strcmp(slot->symbol_name, symbol_name) != 0)) ||
        (slot->symbol_name[0] == '\0' && symbol_name != NULL && symbol_name[0] != '\0')) {
      slot->has_library_id = 0U;
      slot->library_name[0] = '\0';
      slot->symbol_name[0] = '\0';
      slot->conflicted = 1U;
    } else if (slot->library_name[0] == '\0' && slot_library_name[0] != '\0') {
      slot->has_library_id = has_slot_library_id;
      slot->library_id = slot_library_id;
      snprintf(slot->library_name, sizeof(slot->library_name), "%s", slot_library_name);
    }
    if (normalized_access_size > slot->observed_access_size) slot->observed_access_size = normalized_access_size;
    if (has_source && slot->has_source == 0U) {
      slot->source_section_index = source_section_index;
      slot->source_offset = source_offset;
      slot->has_source = 1U;
    }
    return 0;
  }
  if (lookup->base_field_slot_count == lookup->base_field_slot_capacity) {
    next_capacity = lookup->base_field_slot_capacity == 0U ? 8U : lookup->base_field_slot_capacity * 2U;
    grown = (M68kRenderBaseFieldSlot *)render_lookup_grow_array(lookup, lookup->base_field_slots,
      lookup->base_field_slot_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->base_field_slots = grown;
    lookup->base_field_slot_capacity = next_capacity;
  }
  memset(&lookup->base_field_slots[lookup->base_field_slot_count], 0,
    sizeof(lookup->base_field_slots[lookup->base_field_slot_count]));
  snprintf(lookup->base_field_slots[lookup->base_field_slot_count].owner_name,
    sizeof(lookup->base_field_slots[lookup->base_field_slot_count].owner_name), "%s", owner_name);
  lookup->base_field_slots[lookup->base_field_slot_count].displacement = displacement;
  lookup->base_field_slots[lookup->base_field_slot_count].source_section_index = source_section_index;
  lookup->base_field_slots[lookup->base_field_slot_count].source_offset = source_offset;
  lookup->base_field_slots[lookup->base_field_slot_count].has_source = has_source;
  if (slot_library_name[0] != '\0') {
    lookup->base_field_slots[lookup->base_field_slot_count].has_library_id = has_slot_library_id;
    lookup->base_field_slots[lookup->base_field_slot_count].library_id = slot_library_id;
    snprintf(lookup->base_field_slots[lookup->base_field_slot_count].library_name,
      sizeof(lookup->base_field_slots[lookup->base_field_slot_count].library_name), "%s", slot_library_name);
  }
  if (symbol_name != NULL && symbol_name[0] != '\0') {
    snprintf(lookup->base_field_slots[lookup->base_field_slot_count].symbol_name,
      sizeof(lookup->base_field_slots[lookup->base_field_slot_count].symbol_name), "%s", symbol_name);
  }
  lookup->base_field_slots[lookup->base_field_slot_count].value_kind = value_kind;
  lookup->base_field_slots[lookup->base_field_slot_count].owner_kind = owner_kind;
  lookup->base_field_slots[lookup->base_field_slot_count].observed_access_size = normalized_access_size;
  ++lookup->base_field_slot_count;
  return 0;
}

static int render_lookup_add_base_field_slot(M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, const char *library_name, size_t source_section_index, uint32_t source_offset) {
  return render_lookup_add_base_field_slot_with_symbol(lookup, owner_name, displacement, library_name, NULL,
    M68K_RENDER_BASE_FIELD_SLOT_LIBRARY_BASE, 4U, source_section_index, source_offset);
}

static int render_lookup_add_device_base_field_slot(M68kRenderLookup *lookup, const char *owner_name,
    int16_t displacement, const char *library_name, size_t source_section_index, uint32_t source_offset) {
  return render_lookup_add_base_field_slot_with_symbol(lookup, owner_name, displacement, library_name, NULL,
    M68K_RENDER_BASE_FIELD_SLOT_DEVICE_BASE, 4U, source_section_index, source_offset);
}

static int render_lookup_add_named_layout_field_slot(M68kRenderLookup *lookup, const char *base_symbol,
    int16_t displacement, const char *symbol_name, size_t source_section_index, uint32_t source_offset) {
  return render_lookup_add_base_field_slot_with_symbol(lookup, base_symbol, displacement, "", symbol_name,
    M68K_RENDER_BASE_FIELD_SLOT_NAMED_VALUE, 0U, source_section_index, source_offset);
}

static int render_lookup_add_app_access_slot(M68kRenderLookup *lookup, int16_t displacement,
    uint8_t observed_access_size, size_t source_section_index, uint32_t source_offset) {
  return render_lookup_add_base_field_slot_with_symbol(lookup, M68K_APP_BASE_SYMBOL, displacement, "", NULL,
    M68K_RENDER_BASE_FIELD_SLOT_APP_ACCESS, observed_access_size, source_section_index, source_offset);
}

static int render_lookup_seed_policy_rsset_layout_regions(M68kRenderLookup *lookup) {
  uint16_t index;
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (lookup == NULL || policy == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < policy->rsset_layout_region_count && index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++index) {
    const M68kAnalysisRssetLayoutRegion *slot = &policy->rsset_layout_regions[index];
    const char *base_symbol = slot->base_symbol[0] != '\0' ? slot->base_symbol : M68K_APP_BASE_SYMBOL;
    uint16_t pointer_struct_id = AMIGA_OS_STRUCT_ID_NONE;
    if (slot->symbol[0] == '\0' || slot->offset > 0x7FFFU) continue;
    if (render_lookup_add_named_layout_field_slot(lookup, base_symbol, (int16_t)slot->offset, slot->symbol, SIZE_MAX,
        UINT32_MAX) != 0) {
      return -1;
    }
    if (slot->storage_kind_id == M68K_ANALYSIS_RSSET_LAYOUT_STORAGE_STRUCT_POINTER &&
        slot->pointer_struct[0] != '\0') {
      pointer_struct_id = lookup_policy_struct_id_by_name(policy, slot->pointer_struct);
      if (pointer_struct_id == AMIGA_OS_STRUCT_ID_NONE ||
          render_lookup_add_typed_app_slot(lookup, (int16_t)slot->offset, pointer_struct_id,
            (size_t)-1, 0U, NULL) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int render_lookup_add_device_instance(M68kRenderLookup *lookup, int16_t iorequest_displacement,
    const char *device_name) {
  size_t index;
  M68kRenderDeviceInstance *grown;
  size_t next_capacity;
  if (lookup == NULL || device_name == NULL || device_name[0] == '\0') return 0;
  for (index = 0U; index < lookup->device_instance_count; ++index) {
    M68kRenderDeviceInstance *instance = &lookup->device_instances[index];
    if (instance->iorequest_displacement != iorequest_displacement) continue;
    if (strcmp(instance->device_name, device_name) != 0) {
      instance->device_name[0] = '\0';
      instance->conflicted = 1U;
    }
    return 0;
  }
  if (lookup->device_instance_count == lookup->device_instance_capacity) {
    next_capacity = lookup->device_instance_capacity == 0U ? 8U : lookup->device_instance_capacity * 2U;
    grown = (M68kRenderDeviceInstance *)render_lookup_grow_array(lookup, lookup->device_instances,
      lookup->device_instance_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->device_instances = grown;
    lookup->device_instance_capacity = next_capacity;
  }
  memset(&lookup->device_instances[lookup->device_instance_count], 0,
    sizeof(lookup->device_instances[lookup->device_instance_count]));
  lookup->device_instances[lookup->device_instance_count].iorequest_displacement = iorequest_displacement;
  snprintf(lookup->device_instances[lookup->device_instance_count].device_name,
    sizeof(lookup->device_instances[lookup->device_instance_count].device_name), "%s", device_name);
  ++lookup->device_instance_count;
  return 0;
}

static const char *render_lookup_device_name_for_iorequest(const M68kRenderLookup *lookup,
    int16_t iorequest_displacement) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->device_instance_count; ++index) {
    const M68kRenderDeviceInstance *instance = &lookup->device_instances[index];
    if (instance->iorequest_displacement == iorequest_displacement && instance->conflicted == 0U &&
        instance->device_name[0] != '\0') {
      return instance->device_name;
    }
  }
  return NULL;
}

static int render_lookup_add_device_call(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    const char *device_name) {
  size_t index;
  M68kRenderDeviceCall *grown;
  size_t next_capacity;
  if (lookup == NULL || device_name == NULL || device_name[0] == '\0') return 0;
  for (index = 0U; index < lookup->device_call_count; ++index) {
    M68kRenderDeviceCall *call = &lookup->device_calls[index];
    if (call->section_index != section_index || call->offset != offset) continue;
    return strcmp(call->device_name, device_name) == 0 ? 0 : -1;
  }
  if (lookup->device_call_count == lookup->device_call_capacity) {
    next_capacity = lookup->device_call_capacity == 0U ? 8U : lookup->device_call_capacity * 2U;
    grown = (M68kRenderDeviceCall *)render_lookup_grow_array(lookup, lookup->device_calls,
      lookup->device_call_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->device_calls = grown;
    lookup->device_call_capacity = next_capacity;
  }
  memset(&lookup->device_calls[lookup->device_call_count], 0, sizeof(lookup->device_calls[lookup->device_call_count]));
  lookup->device_calls[lookup->device_call_count].section_index = section_index;
  lookup->device_calls[lookup->device_call_count].offset = offset;
  snprintf(lookup->device_calls[lookup->device_call_count].device_name,
    sizeof(lookup->device_calls[lookup->device_call_count].device_name), "%s", device_name);
  ++lookup->device_call_count;
  return 0;
}

const char *render_lookup_device_name_for_call(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  size_t index;
  if (lookup == NULL) return NULL;
  for (index = 0U; index < lookup->device_call_count; ++index) {
    const M68kRenderDeviceCall *call = &lookup->device_calls[index];
    if (call->section_index == section_index && call->offset == offset && call->device_name[0] != '\0')
      return call->device_name;
  }
  return NULL;
}

static int format_generated_app_slot_ref_symbol_name(int16_t displacement, char *symbol_name,
    size_t symbol_name_size) {
  int written;
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  written = snprintf(symbol_name, symbol_name_size, "app_%04X", (unsigned)(uint16_t)displacement);
  return written > 0 && (size_t)written < symbol_name_size;
}

static int render_lookup_add_app_access_ref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t base_reg, int16_t displacement, uint8_t operand_index, uint8_t access_kind,
    uint8_t observed_access_size, int add_renderable_slot, uint8_t base_evidence_kind) {
  size_t index;
  M68kRenderAppSlotRef *grown;
  size_t next_capacity;
  if (lookup == NULL || base_reg >= 8U || operand_index >= 4U ||
      access_kind == M68K_APP_SLOT_ACCESS_NONE) {
    return 0;
  }
  if (add_renderable_slot &&
      render_lookup_add_app_access_slot(lookup, displacement, observed_access_size, section_index, offset) != 0)
    return -1;
  for (index = 0U; index < lookup->app_slot_ref_count; ++index) {
    M68kRenderAppSlotRef *existing = &lookup->app_slot_refs[index];
    if (existing->section_index == section_index && existing->ref.offset == offset &&
        existing->ref.displacement == displacement && existing->ref.base_reg == base_reg &&
        existing->ref.operand_index == operand_index && existing->ref.access_kind == access_kind) {
      if (existing->ref.base_evidence_kind == M68K_APP_SLOT_BASE_UNSPECIFIED ||
          base_evidence_kind == M68K_APP_SLOT_BASE_USE_SITE_BINDING ||
          (base_evidence_kind == M68K_APP_SLOT_BASE_REGISTER_STATE &&
           (existing->ref.base_evidence_kind == M68K_APP_SLOT_BASE_A6_FALLBACK ||
            existing->ref.base_evidence_kind == M68K_APP_SLOT_BASE_DECLARED_LAYOUT_A6_FALLBACK)))
        existing->ref.base_evidence_kind = base_evidence_kind;
      return 0;
    }
  }
  if (lookup->app_slot_ref_count == lookup->app_slot_ref_capacity) {
    next_capacity = lookup->app_slot_ref_capacity == 0U ? 32U : lookup->app_slot_ref_capacity * 2U;
    grown = (M68kRenderAppSlotRef *)render_lookup_grow_array(lookup, lookup->app_slot_refs,
      lookup->app_slot_ref_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->app_slot_refs = grown;
    lookup->app_slot_ref_capacity = next_capacity;
  }
  memset(&lookup->app_slot_refs[lookup->app_slot_ref_count], 0,
    sizeof(lookup->app_slot_refs[lookup->app_slot_ref_count]));
  lookup->app_slot_refs[lookup->app_slot_ref_count].section_index = section_index;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.offset = offset;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.displacement = displacement;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.base_reg = base_reg;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.operand_index = operand_index;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.access_kind = access_kind;
  lookup->app_slot_refs[lookup->app_slot_ref_count].ref.base_evidence_kind = base_evidence_kind;
  if (format_generated_app_slot_ref_symbol_name(displacement,
      lookup->app_slot_refs[lookup->app_slot_ref_count].symbol_name,
      sizeof(lookup->app_slot_refs[lookup->app_slot_ref_count].symbol_name))) {
    lookup->app_slot_refs[lookup->app_slot_ref_count].ref.symbol_name =
      lookup->app_slot_refs[lookup->app_slot_ref_count].symbol_name;
  }
  ++lookup->app_slot_ref_count;
  return 0;
}

int render_lookup_add_runtime_address_ref(M68kRenderLookup *lookup, const M68kFact *fact) {
  M68kRenderRuntimeAddressRef *grown;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL || fact == NULL || fact->kind != M68K_FACT_RUNTIME_ADDRESS_REF ||
      !fact->has_runtime_address) {
    return 0;
  }
  for (index = 0U; index < lookup->runtime_address_ref_count; ++index) {
    const M68kFact *existing = lookup->runtime_address_refs[index].fact;
    if (existing == NULL) continue;
    if (existing->section_index == fact->section_index && existing->offset == fact->offset &&
        existing->reason == fact->reason && existing->target_section_index == fact->target_section_index &&
        existing->target_offset == fact->target_offset && existing->has_runtime_address &&
        existing->runtime_address == fact->runtime_address) {
      return 0;
    }
  }
  if (lookup->runtime_address_ref_count == lookup->runtime_address_ref_capacity) {
    next_capacity = lookup->runtime_address_ref_capacity == 0U ? 32U :
      lookup->runtime_address_ref_capacity * 2U;
    grown = (M68kRenderRuntimeAddressRef *)render_lookup_grow_array(lookup, lookup->runtime_address_refs,
      lookup->runtime_address_ref_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->runtime_address_refs = grown;
    lookup->runtime_address_ref_capacity = next_capacity;
  }
  lookup->runtime_address_refs[lookup->runtime_address_ref_count].fact = fact;
  ++lookup->runtime_address_ref_count;
  if (fact->section_index < lookup->section_count && lookup->runtime_address_ref_indices != NULL &&
      lookup->runtime_address_ref_index_extents != NULL &&
      fact->offset < lookup->runtime_address_ref_index_extents[fact->section_index] &&
      lookup->runtime_address_ref_indices[fact->section_index] != NULL) {
    M68kRenderRuntimeAddressRefIndex *entry =
      &lookup->runtime_address_ref_indices[fact->section_index][fact->offset];
    if (fact->reason < M68K_DECODE_IR_MAX_OPERANDS) {
      entry->operand_refs[fact->reason] = fact;
    }
    if (fact->target_section_index >= lookup->section_count) {
      entry->external_ref = fact;
    }
  }
  return 0;
}

int render_lookup_add_runtime_address_range(M68kRenderLookup *lookup, const M68kFact *fact) {
  M68kRenderRuntimeAddressRange *grown;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL || fact == NULL || fact->kind != M68K_FACT_RUNTIME_ADDRESS_RANGE ||
      !fact->has_runtime_address || fact->size == 0U) {
    return 0;
  }
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *existing = lookup->runtime_address_ranges[index].fact;
    if (existing == NULL) continue;
    if (existing->section_index == fact->section_index && existing->offset == fact->offset &&
        existing->runtime_address == fact->runtime_address && existing->size == fact->size) {
      return 0;
    }
  }
  if (lookup->runtime_address_range_count == lookup->runtime_address_range_capacity) {
    next_capacity = lookup->runtime_address_range_capacity == 0U ? 16U :
      lookup->runtime_address_range_capacity * 2U;
    grown = (M68kRenderRuntimeAddressRange *)render_lookup_grow_array(lookup, lookup->runtime_address_ranges,
      lookup->runtime_address_range_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->runtime_address_ranges = grown;
    lookup->runtime_address_range_capacity = next_capacity;
  }
  memset(&lookup->runtime_address_ranges[lookup->runtime_address_range_count], 0,
    sizeof(lookup->runtime_address_ranges[lookup->runtime_address_range_count]));
  lookup->runtime_address_ranges[lookup->runtime_address_range_count].fact = fact;
  ++lookup->runtime_address_range_count;
  return 0;
}

static int policy_declared_app_extent_covers(const M68kAnalysisPolicy *policy, int16_t displacement,
    uint32_t access_size) {
  uint16_t index;
  uint32_t field_offset, width = access_size != 0U ? access_size : 1U;
  if (policy == NULL || displacement < 0) return 0;
  field_offset = (uint32_t)(uint16_t)displacement;
  for (index = 0U; index < policy->rsset_layout_region_count &&
       index < M68K_ANALYSIS_RSSET_LAYOUT_REGION_LIMIT; ++index) {
    const M68kAnalysisRssetLayoutRegion *region = &policy->rsset_layout_regions[index];
    if ((region->layout_name[0] != '\0' && strcmp(region->layout_name, "app") != 0) ||
        (region->base_symbol[0] != '\0' && strcmp(region->base_symbol, M68K_APP_BASE_SYMBOL) != 0) ||
        region->size == 0U || field_offset < region->offset) continue;
    if (field_offset - region->offset <= region->size &&
        width <= region->size - (field_offset - region->offset)) return 1;
  }
  return 0;
}

/* One exact instruction footprint, never a loop-trip or cursor-range proof.
 * Predecrement/striped/indexed and shared update bases remain refused. */
static int typed_app_memory_span(const M68kRenderLookup *lookup, const M68kRenderTypedState *state,
    const M68kInstructionIR *instruction, size_t operand_index, uint8_t *out_reg,
    int16_t *out_displacement, uint8_t *out_access, uint8_t *out_width,
    uint8_t *out_element_width, uint8_t *out_count) {
  const M68kSimFormMetadata *metadata = m68k_sim_metadata_for_instruction(instruction);
  const M68kOperandIR *operand;
  uint8_t reg, access, width, count = 1U, shape;
  int16_t displacement = 0;
  int32_t target;
  size_t index;
  if (lookup == NULL || state == NULL || metadata == NULL || operand_index >= instruction->operand_count ||
      operand_index >= 4U || metadata->striped_direction != M68K_SIM_STRIPED_NONE) return 0;
  operand = &instruction->operands[operand_index];
  shape = m68k_instruction_operand_decoded_ea_shape(operand);
  if (shape == M68K_SIM_EA_SHAPE_POSTINCREMENT && operand->kind == M68K_ASM_OPERAND_EA) {
    reg = operand->value.ea_reg;
  } else if (!operand_is_address_memory_local(operand, &reg, &displacement)) return 0;
  if (reg >= 7U || !state->app_addr_regs[reg].known ||
      state->app_addr_regs[reg].base_evidence_kind == M68K_APP_SLOT_BASE_UNSPECIFIED) return 0;
  if (metadata->multi_transfer_direction != M68K_SIM_MULTI_NONE) {
    uint8_t reglist_index = metadata->reglist_operand_index;
    uint16_t mask;
    if (metadata->operation_type != M68K_SIM_OP_MOVE_MULTIPLE ||
        metadata->address_operand_index != operand_index || reglist_index >= instruction->operand_count ||
        instruction->operands[reglist_index].kind != M68K_ASM_OPERAND_REGLIST ||
        (shape != M68K_SIM_EA_SHAPE_INDIRECT && shape != M68K_SIM_EA_SHAPE_DISPLACEMENT &&
         shape != M68K_SIM_EA_SHAPE_POSTINCREMENT)) return 0;
    mask = (uint16_t)instruction->operands[reglist_index].value.value;
    /* Loading the EA register changes its value independently of memory
     * cursor motion. Do not resurrect its old app identity afterwards. */
    if ((mask & (1U << (8U + reg))) != 0U) return 0;
    if (!platform_operand_memory_span(instruction, operand_index, &width, &count, NULL)) return 0;
    access = metadata->multi_transfer_direction == M68K_SIM_MULTI_MEMORY_TO_REGISTER
      ? M68K_APP_SLOT_ACCESS_READ : M68K_APP_SLOT_ACCESS_WRITE;
  } else {
    access = app_slot_access_kind_from_instruction(instruction, operand_index);
    if (access == M68K_APP_SLOT_ACCESS_NONE) return 0;
    width = 0U;
    if (access != M68K_APP_SLOT_ACCESS_ADDRESS &&
        !platform_operand_memory_span(instruction, operand_index, &width, &count, NULL)) return 0;
    if (access != M68K_APP_SLOT_ACCESS_ADDRESS && width != 1U && width != 2U && width != 4U) return 0;
    if (access == M68K_APP_SLOT_ACCESS_ADDRESS && shape == M68K_SIM_EA_SHAPE_POSTINCREMENT) return 0;
    for (index = 0U; index < instruction->operand_count; ++index) {
      uint8_t other_reg, other_shape;
      const M68kOperandIR *other = &instruction->operands[index];
      if (index == operand_index) continue;
      if (operand_address_register_index_local(other, &other_reg) && other_reg == reg) return 0;
      other_shape = m68k_instruction_operand_decoded_ea_shape(other);
      if (other_shape == M68K_SIM_EA_SHAPE_POSTINCREMENT || other_shape == M68K_SIM_EA_SHAPE_PREDECREMENT)
        return 0;
      if ((other->kind == M68K_ASM_OPERAND_EA || other->kind == M68K_ASM_OPERAND_BF_EA) &&
          other->value.ea_reg == reg &&
          (other_shape == M68K_SIM_EA_SHAPE_INDIRECT || other_shape == M68K_SIM_EA_SHAPE_DISPLACEMENT ||
           other_shape == M68K_SIM_EA_SHAPE_INDEX)) return 0;
      if (other_shape == M68K_SIM_EA_SHAPE_INDEX && other->value.index_is_address &&
          other->value.index_reg == reg) return 0;
    }
  }
  target = (int32_t)state->app_addr_regs[reg].displacement + displacement;
  if (target < INT16_MIN || target > INT16_MAX ||
      !policy_declared_app_extent_covers(lookup->policy, (int16_t)target, (uint8_t)(width * count))) return 0;
  *out_reg = reg; *out_displacement = displacement; *out_access = access;
  *out_width = (uint8_t)(width * count); *out_element_width = width;
  *out_count = access == M68K_APP_SLOT_ACCESS_ADDRESS ? 0U : count;
  return 1;
}

/* Reuse the converged app-address domain; a pointee type is not required.
 * This is catalogue projection, not a new preservation or runtime proof. */
static int render_lookup_record_derived_app_operand(M68kRenderLookup *lookup, size_t section_index,
    const M68kRenderTypedState *state, const M68kInstructionIR *instruction, uint32_t offset, size_t operand_index) {
  size_t index;
  if (lookup == NULL || state == NULL || instruction == NULL || lookup->typed_flow_incomplete_count != 0U)
    return 0;
    uint8_t base_reg, access, width, element_width, count;
    int16_t operand_displacement;
    int32_t target;
    const M68kRenderTypedAppAddressValue *base;
    if (!typed_app_memory_span(lookup, state, instruction, operand_index, &base_reg,
        &operand_displacement, &access, &width, &element_width, &count)) return 0;
    base = &state->app_addr_regs[base_reg];
    target = (int32_t)base->displacement + operand_displacement;
    if (target < INT16_MIN || target > INT16_MAX ||
        !policy_declared_app_extent_covers(lookup->policy, (int16_t)target, width)) return 0;
    if (render_lookup_add_app_access_ref(lookup, section_index, offset, base_reg, (int16_t)target,
        (uint8_t)operand_index, access, width, 0, base->base_evidence_kind) != 0) return -1;
    for (index = 0U; index < lookup->app_slot_ref_count; ++index) {
      M68kRenderAppSlotRef *ref = &lookup->app_slot_refs[index];
      if (ref->section_index == section_index && ref->ref.offset == offset &&
          ref->ref.base_reg == base_reg && ref->ref.operand_index == operand_index &&
          ref->ref.displacement == target && ref->ref.access_kind == access) {
        ref->ref.base_displacement = base->displacement;
        ref->ref.operand_displacement = operand_displacement;
        ref->ref.has_derived_base = 1U;
        ref->ref.access_size = access == M68K_APP_SLOT_ACCESS_ADDRESS ? 0U : width;
        ref->ref.element_width = element_width;
        ref->ref.transfer_count = count;
        break;
      }
    }
  return 0;
}

static int render_lookup_record_derived_app_accesses(M68kRenderLookup *lookup, size_t section_index,
    const M68kRenderTypedState *state, const M68kInstructionIR *instruction, uint32_t offset) {
  if (!instruction) return 0;
  for (size_t operand = 0U; operand < instruction->operand_count && operand < 4U; ++operand)
    if (render_lookup_record_derived_app_operand(lookup, section_index, state, instruction, offset, operand) != 0)
      return -1;
  return 0;
}

static uint8_t code_start_ref_evidence_priority(uint32_t evidence_kind) {
  switch (evidence_kind) {
    case M68K_CODE_ORIGIN_EVIDENCE_MANUAL_ACTION_LOG_ENTRY_POINT:
    case M68K_CODE_ORIGIN_EVIDENCE_DECISION_JOURNAL_ENTRY_POINT:
      return 3U;
    case M68K_CODE_ORIGIN_EVIDENCE_UNKNOWN:
      return 0U;
    default:
      return 2U;
  }
}

int render_lookup_add_code_start_ref(M68kRenderLookup *lookup, const M68kFact *fact) {
  M68kRenderCodeStartRef *grown;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL || fact == NULL ||
      (fact->kind != M68K_FACT_CODE_ACCEPTED && fact->kind != M68K_FACT_CODE_START) ||
      fact->reason == M68K_FACT_CODE_START_REASON_FALLTHROUGH) {
    return 0;
  }
  for (index = 0U; index < lookup->code_start_ref_count; ++index) {
    const M68kFact *existing = lookup->code_start_refs[index].fact;
    if (existing == NULL) continue;
    if (existing->section_index == fact->section_index && existing->offset == fact->offset &&
        existing->reason == fact->reason && existing->source_section_index == fact->source_section_index &&
        existing->source_offset == fact->source_offset && existing->has_runtime_address == fact->has_runtime_address &&
        existing->runtime_address == fact->runtime_address) {
      uint8_t fact_priority = code_start_ref_evidence_priority(fact->code_start_evidence_kind);
      uint8_t existing_priority = code_start_ref_evidence_priority(existing->code_start_evidence_kind);
      if (fact_priority > existing_priority ||
          (fact_priority == existing_priority && existing->size == 0U && fact->size != 0U)) {
        lookup->code_start_refs[index].fact = fact;
      }
      return 0;
    }
  }
  if (lookup->code_start_ref_count == lookup->code_start_ref_capacity) {
    next_capacity = lookup->code_start_ref_capacity == 0U ? 32U : lookup->code_start_ref_capacity * 2U;
    grown = (M68kRenderCodeStartRef *)render_lookup_grow_array(lookup, lookup->code_start_refs,
      lookup->code_start_ref_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->code_start_refs = grown;
    lookup->code_start_ref_capacity = next_capacity;
  }
  lookup->code_start_refs[lookup->code_start_ref_count].fact = fact;
  ++lookup->code_start_ref_count;
  return 0;
}

int render_lookup_add_violation_ref(M68kRenderLookup *lookup, const M68kFact *fact) {
  M68kRenderViolationRef *grown;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL || fact == NULL || fact->kind != M68K_FACT_VIOLATION) return 0;
  for (index = 0U; index < lookup->violation_ref_count; ++index) {
    const M68kFact *existing = lookup->violation_refs[index].fact;
    if (existing == NULL) continue;
    if (existing->section_index == fact->section_index && existing->offset == fact->offset &&
        existing->target_section_index == fact->target_section_index &&
        existing->target_offset == fact->target_offset && existing->reason == fact->reason) {
      return 0;
    }
  }
  if (lookup->violation_ref_count == lookup->violation_ref_capacity) {
    next_capacity = lookup->violation_ref_capacity == 0U ? 16U : lookup->violation_ref_capacity * 2U;
    grown = (M68kRenderViolationRef *)render_lookup_grow_array(lookup, lookup->violation_refs,
      lookup->violation_ref_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->violation_refs = grown;
    lookup->violation_ref_capacity = next_capacity;
  }
  lookup->violation_refs[lookup->violation_ref_count].fact = fact;
  ++lookup->violation_ref_count;
  return 0;
}

static int structured_data_item_is_untyped_bytes_placeholder_local(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_BYTES &&
    item->semantic_role_flags == 0U && item->source_pattern_id == 0U && item->size != 0U;
}

static int structured_data_item_is_weak_generic_text_local(const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL || item->kind != M68K_ANALYSIS_STRUCTURED_DATA_STRING ||
      (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING) == 0U) {
    return 0;
  }
  return item->source_pattern_id == M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_TERMINATED_TEXT ||
    item->source_pattern_id == M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_BOUNDED_TEXT ||
    item->source_pattern_id == M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_CONTROL_STRING_STREAM;
}

static int structured_data_item_supersedes_weak_generic_text_local(const M68kAnalysisStructuredDataItem *item) {
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_STRING &&
    (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING) != 0U &&
    !structured_data_item_is_weak_generic_text_local(item);
}

static int structured_data_item_contains_range_local(const M68kAnalysisStructuredDataItem *owner,
    const M68kAnalysisStructuredDataItem *contained) {
  uint32_t owner_end;
  uint32_t contained_end;
  if (owner == NULL || contained == NULL || !owner->has_section_index || !contained->has_section_index ||
      owner->section_index != contained->section_index || owner->size == 0U || contained->size == 0U ||
      owner->offset > UINT32_MAX - owner->size || contained->offset > UINT32_MAX - contained->size) {
    return 0;
  }
  owner_end = owner->offset + owner->size;
  contained_end = contained->offset + contained->size;
  return contained->offset >= owner->offset && contained_end <= owner_end;
}

static int structured_data_item_ranges_overlap_local(const M68kAnalysisStructuredDataItem *left,
    const M68kAnalysisStructuredDataItem *right) {
  uint32_t left_end;
  uint32_t right_end;
  if (left == NULL || right == NULL || !left->has_section_index || !right->has_section_index ||
      left->section_index != right->section_index || left->size == 0U || right->size == 0U ||
      left->offset > UINT32_MAX - left->size || right->offset > UINT32_MAX - right->size) {
    return 0;
  }
  left_end = left->offset + left->size;
  right_end = right->offset + right->size;
  return left->offset < right_end && right->offset < left_end;
}

static void render_lookup_clear_auto_structured_data_item_index(M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *item, size_t auto_item_index) {
  size_t section_index;
  if (lookup == NULL || item == NULL || !item->has_section_index) return;
  section_index = item->section_index;
  if (section_index < lookup->section_count && lookup->auto_structured_data_item_indices != NULL &&
      lookup->auto_structured_data_item_index_extents != NULL &&
      item->offset <= lookup->auto_structured_data_item_index_extents[section_index] &&
      lookup->auto_structured_data_item_indices[section_index] != NULL &&
      lookup->auto_structured_data_item_indices[section_index][item->offset] == auto_item_index + 1U) {
    lookup->auto_structured_data_item_indices[section_index][item->offset] = 0U;
  }
}

static void render_lookup_disable_contained_weak_text_items(M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *source_item) {
  size_t index;
  if (lookup == NULL || !structured_data_item_supersedes_weak_generic_text_local(source_item)) return;
  for (index = 0U; index < lookup->range_ownership_count; ++index) {
    M68kRenderRangeOwnershipView *stored = &lookup->range_ownerships[index];
    M68kRenderRangeOwnershipView existing_range;
    M68kAnalysisStructuredDataItem *existing_item;
    if (!lookup_range_ownership_at_index(lookup, index, &existing_range)) continue;
    if (existing_range.structured_item_source != M68K_RENDER_RANGE_STRUCTURED_ITEM_AUTO &&
        existing_range.structured_item_source != M68K_RENDER_RANGE_STRUCTURED_ITEM_POLICY) {
      continue;
    }
    if (existing_range.structured_item_source == M68K_RENDER_RANGE_STRUCTURED_ITEM_AUTO &&
        existing_range.structured_item_index >= lookup->auto_structured_data_item_count) {
      continue;
    }
    if (!structured_data_item_is_weak_generic_text_local(existing_range.structured_item) ||
        !structured_data_item_contains_range_local(source_item, existing_range.structured_item)) {
      continue;
    }
    if (existing_range.structured_item_source == M68K_RENDER_RANGE_STRUCTURED_ITEM_AUTO) {
      existing_item = &lookup->auto_structured_data_items[existing_range.structured_item_index];
      render_lookup_clear_auto_structured_data_item_index(lookup, existing_item,
        existing_range.structured_item_index);
      existing_item->size = 0U;
    }
    stored->end_offset = stored->start_offset;
    stored->structured_item_source = M68K_RENDER_RANGE_STRUCTURED_ITEM_NONE;
    stored->structured_item = NULL;
  }
}

static int render_lookup_import_source_analysis_structured_data_item(M68kRenderLookup *lookup,
    const M68kAnalysisStructuredDataItem *source_item) {
  M68kAnalysisStructuredDataItem *grown;
  M68kAnalysisStructuredDataItem *item;
  size_t next_capacity;
  size_t index;
  size_t section_index;
  if (lookup == NULL || source_item == NULL || !source_item->has_section_index || source_item->size == 0U ||
      source_item->offset > UINT32_MAX - source_item->size || source_item->section_index >= lookup->section_count) {
    return 0;
  }
  section_index = source_item->section_index;
  for (index = 0U; index < lookup->range_ownership_count; ++index) {
    M68kRenderRangeOwnershipView *stored = &lookup->range_ownerships[index];
    M68kRenderRangeOwnershipView existing_range;
    if (stored->section_index != section_index) continue;
    if (!lookup_range_ownership_at_index(lookup, index, &existing_range)) continue;
    if (structured_data_item_is_untyped_bytes_placeholder_local(existing_range.structured_item)) continue;
    if (existing_range.structured_item_source == M68K_RENDER_RANGE_STRUCTURED_ITEM_POLICY &&
        structured_data_item_ranges_overlap_local(source_item, existing_range.structured_item) &&
        !(structured_data_item_supersedes_weak_generic_text_local(source_item) &&
          structured_data_item_is_weak_generic_text_local(existing_range.structured_item) &&
          structured_data_item_contains_range_local(source_item, existing_range.structured_item))) {
      return 0;
    }
  }
  render_lookup_disable_contained_weak_text_items(lookup, source_item);
  for (index = 0U; index < lookup->range_ownership_count; ++index) {
    M68kRenderRangeOwnershipView *stored = &lookup->range_ownerships[index];
    M68kRenderRangeOwnershipView existing_range;
    M68kAnalysisStructuredDataItem *existing_item;
    if (stored->section_index != section_index || stored->start_offset != source_item->offset) continue;
    if (!lookup_range_ownership_at_index(lookup, index, &existing_range)) continue;
    if (structured_data_item_is_untyped_bytes_placeholder_local(existing_range.structured_item)) continue;
    if (existing_range.structured_item_source != M68K_RENDER_RANGE_STRUCTURED_ITEM_AUTO ||
        existing_range.structured_item_index >= lookup->auto_structured_data_item_count) {
      return 0;
    }
    existing_item = &lookup->auto_structured_data_items[existing_range.structured_item_index];
    if (existing_item->size > source_item->size) return 0;
    *existing_item = *source_item;
    stored->section_index = section_index;
    stored->start_offset = source_item->offset;
    stored->end_offset = source_item->offset + source_item->size;
    render_lookup_mark_boundary_flag(lookup, section_index, source_item->offset, M68K_RENDER_BOUNDARY_STRUCTURED_DATA);
    if (lookup->auto_structured_data_item_indices != NULL &&
        lookup->auto_structured_data_item_index_extents != NULL &&
        source_item->offset <= lookup->auto_structured_data_item_index_extents[section_index] &&
        lookup->auto_structured_data_item_indices[section_index] != NULL) {
      lookup->auto_structured_data_item_indices[section_index][source_item->offset] =
        existing_range.structured_item_index + 1U;
    }
    if (source_item->has_consumer) {
      (void)render_lookup_mark_label(lookup, section_index, source_item->offset);
      render_lookup_mark_label_target_ref(lookup, section_index, source_item->offset);
    }
    return 0;
  }
  for (index = 0U; index < lookup->auto_structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *existing = &lookup->auto_structured_data_items[index];
    if (existing->has_section_index == source_item->has_section_index &&
        existing->section_index == source_item->section_index &&
        existing->offset == source_item->offset &&
        existing->size == source_item->size &&
        existing->kind == source_item->kind &&
        existing->source_pattern_id == source_item->source_pattern_id &&
        existing->table_kind_id == source_item->table_kind_id) {
      return 0;
    }
  }
  if (lookup->auto_structured_data_item_count == lookup->auto_structured_data_item_capacity) {
    next_capacity = lookup->auto_structured_data_item_capacity == 0U ? 16U :
      lookup->auto_structured_data_item_capacity * 2U;
    grown = (M68kAnalysisStructuredDataItem *)render_lookup_grow_array(lookup,
      lookup->auto_structured_data_items, lookup->auto_structured_data_item_count, sizeof(*grown),
      next_capacity);
    if (grown == NULL) return -1;
    lookup->auto_structured_data_items = grown;
    lookup->auto_structured_data_item_capacity = next_capacity;
  }
  item = &lookup->auto_structured_data_items[lookup->auto_structured_data_item_count];
  *item = *source_item;
  ++lookup->auto_structured_data_item_count;
  if (render_lookup_add_range_ownership_for_structured_item(lookup, section_index,
      M68K_RENDER_RANGE_STRUCTURED_ITEM_AUTO, lookup->auto_structured_data_item_count - 1U, item) != 0) {
    return -1;
  }
  render_lookup_mark_boundary_flag(lookup, section_index, item->offset, M68K_RENDER_BOUNDARY_STRUCTURED_DATA);
  if (lookup->auto_structured_data_item_indices != NULL &&
      lookup->auto_structured_data_item_index_extents != NULL &&
      item->offset <= lookup->auto_structured_data_item_index_extents[section_index] &&
      lookup->auto_structured_data_item_indices[section_index] != NULL) {
    lookup->auto_structured_data_item_indices[section_index][item->offset] =
      lookup->auto_structured_data_item_count;
  }
  if (item->has_consumer) {
    (void)render_lookup_mark_label(lookup, section_index, item->offset);
    render_lookup_mark_label_target_ref(lookup, section_index, item->offset);
  }
  return 0;
}

int m68k_analysis_render_lookup_import_source_analysis_structured_data(M68kRenderLookup *lookup,
    const M68kSourceAnalysisIR *source_analysis) {
  size_t index;
  if (lookup == NULL || source_analysis == NULL) return 0;
  for (index = 0U; index < source_analysis->structured_data_item_count; ++index) {
    if (render_lookup_import_source_analysis_structured_data_item(lookup,
        &source_analysis->structured_data_items[index]) != 0) {
      return -1;
    }
  }
  return 0;
}

void render_lookup_mark_label_target_ref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->label_target_refs == NULL ||
      lookup->label_target_ref_extents == NULL || offset > lookup->label_target_ref_extents[section_index] ||
      lookup->label_target_refs[section_index] == NULL) {
    return;
  }
  lookup->label_target_refs[section_index][offset] = 1U;
}

void render_lookup_mark_label_statement_ref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->label_statement_refs == NULL ||
      lookup->label_statement_ref_extents == NULL || offset > lookup->label_statement_ref_extents[section_index] ||
      lookup->label_statement_refs[section_index] == NULL) {
    return;
  }
  lookup->label_statement_refs[section_index][offset] = 1U;
}

void render_lookup_mark_storage_label_target_ref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->storage_label_target_refs == NULL ||
      lookup->storage_label_target_ref_extents == NULL ||
      offset > lookup->storage_label_target_ref_extents[section_index] ||
      lookup->storage_label_target_refs[section_index] == NULL) {
    return;
  }
  lookup->storage_label_target_refs[section_index][offset] = 1U;
}

static uint32_t render_lookup_label_definition_offset_for_xref(const M68kRenderLookup *lookup,
    size_t target_section_index, uint32_t target_offset) {
  size_t index;
  if (lookup == NULL || target_section_index >= lookup->section_count) return target_offset;
  if (lookup->label_extents != NULL && target_offset <= lookup->label_extents[target_section_index])
    return target_offset;
  if (lookup->runtime_address_ranges == NULL) return target_offset;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *range = lookup->runtime_address_ranges[index].fact;
    uint32_t delta;
    uint32_t source_offset;
    if (range == NULL || range->section_index != target_section_index || !range->has_runtime_address ||
        target_offset < range->runtime_address) {
      continue;
    }
    delta = target_offset - range->runtime_address;
    if (delta >= range->size || range->offset > UINT32_MAX - delta) continue;
    source_offset = range->offset + delta;
    if (lookup->label_extents != NULL && source_offset <= lookup->label_extents[target_section_index])
      return source_offset;
  }
  return target_offset;
}

int render_lookup_add_storage_xref(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    size_t target_section_index, uint32_t target_offset) {
  M68kRenderXref *grown;
  size_t next_capacity;
  size_t index;
  uint32_t label_offset;
  if (lookup == NULL) return 0;
  label_offset = render_lookup_label_definition_offset_for_xref(lookup, target_section_index, target_offset);
  for (index = 0U; index < lookup->xref_count; ++index) {
    const M68kRenderXref *xref = &lookup->xrefs[index];
    if (xref->section_index == section_index && xref->offset == offset &&
        xref->target_section_index == target_section_index && xref->target_offset == target_offset) {
      return 0;
    }
  }
  if (lookup->xref_count == lookup->xref_capacity) {
    next_capacity = lookup->xref_capacity == 0U ? 64U : lookup->xref_capacity * 2U;
    grown = (M68kRenderXref *)render_lookup_grow_array(lookup, lookup->xrefs, lookup->xref_count,
      sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->xrefs = grown;
    lookup->xref_capacity = next_capacity;
  }
  lookup->xrefs[lookup->xref_count].section_index = section_index;
  lookup->xrefs[lookup->xref_count].offset = offset;
  lookup->xrefs[lookup->xref_count].target_section_index = target_section_index;
  lookup->xrefs[lookup->xref_count].target_offset = target_offset;
  ++lookup->xref_count;
  render_lookup_mark_label(lookup, target_section_index, label_offset);
  render_lookup_mark_label_target_ref(lookup, target_section_index, label_offset);
  render_lookup_mark_label_statement_ref(lookup, target_section_index, label_offset);
  return 0;
}

int render_lookup_add_pc_relative_xrefs(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return 0;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    if (accepted_start[section_index] == NULL) continue;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      size_t target_index;
      int decoded = 0;
      if (!accepted_start_at(section, accepted_start[section_index], candidate->offset)) continue;
      memset(&instruction, 0, sizeof(instruction));
      for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
        const M68kDecodeTarget *target = &candidate->targets[target_index];
        if (!target->has_section || !target->has_operand || target->section_index >= decode->section_count)
          continue;
        if (!decoded) {
          if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
          decoded = 1;
        }
        if (target->operand_index >= instruction.operand_count) continue;
        if (symbol_ref_kind_for_operand(&instruction.operands[target->operand_index]) != M68K_IR_SYMBOL_REF_PC_REL)
          continue;
        if (render_lookup_add_storage_xref(lookup, section->section_index, candidate->offset,
            target->section_index, target->offset) != 0)
          return -1;
      }
    }
  }
  return 0;
}

int render_lookup_add_indexed_vector_wrapper(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t index_reg, const char *library_name) {
  size_t index;
  M68kRenderIndexedVectorWrapper *grown;
  size_t next_capacity;
  uint16_t library_id;
  if (lookup == NULL || index_reg >= 8U || library_name == NULL || library_name[0] == '\0') return 0;
  if (render_lookup_amiga_library_base_name_for_library_name(library_name) == NULL) return 0;
  if (!platform_facts_v2_library_id_for_library_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, library_name, &library_id))
    return 0;
  for (index = 0U; index < lookup->indexed_vector_wrapper_count; ++index) {
    M68kRenderIndexedVectorWrapper *wrapper = &lookup->indexed_vector_wrappers[index];
    if (wrapper->section_index != section_index || wrapper->offset != offset) continue;
    if (wrapper->index_reg != index_reg) {
      wrapper->has_library_id = 0U;
      wrapper->library_name[0] = '\0';
      return 0;
    }
    if (!wrapper->has_library_id || wrapper->library_id != library_id) {
      wrapper->has_library_id = 0U;
      wrapper->library_name[0] = '\0';
    }
    return 0;
  }
  if (lookup->indexed_vector_wrapper_count == lookup->indexed_vector_wrapper_capacity) {
    next_capacity = lookup->indexed_vector_wrapper_capacity == 0U ? 8U :
      lookup->indexed_vector_wrapper_capacity * 2U;
    grown = (M68kRenderIndexedVectorWrapper *)render_lookup_grow_array(lookup,
      lookup->indexed_vector_wrappers, lookup->indexed_vector_wrapper_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->indexed_vector_wrappers = grown;
    lookup->indexed_vector_wrapper_capacity = next_capacity;
  }
  memset(&lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count], 0,
    sizeof(lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count]));
  lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].section_index = section_index;
  lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].offset = offset;
  lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].index_reg = index_reg;
  lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].has_library_id = 1U;
  lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].library_id = library_id;
  snprintf(lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].library_name,
    sizeof(lookup->indexed_vector_wrappers[lookup->indexed_vector_wrapper_count].library_name), "%s", library_name);
  ++lookup->indexed_vector_wrapper_count;
  return 0;
}

static int comment_contains_part(const char *comment, const char *part) {
  if (comment == NULL || part == NULL || part[0] == '\0') return 1;
  return strstr(comment, part) != NULL;
}

int append_comment_part_local(char *comment, size_t comment_size, const char *part) {
  size_t used;
  size_t needed;
  if (comment == NULL || comment_size == 0U || part == NULL || part[0] == '\0') return 1;
  if (comment_contains_part(comment, part)) return 1;
  used = strlen(comment);
  needed = strlen(part) + (used != 0U ? 3U : 0U) + 1U;
  if (needed > comment_size - used) return 0;
  if (used != 0U) strcat(comment, " | ");
  strcat(comment, part);
  return 1;
}

static size_t *lookup_instruction_comment_index_slot(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->instruction_comment_indices == NULL ||
      lookup->instruction_comment_extents == NULL || offset >= lookup->instruction_comment_extents[section_index] ||
      lookup->instruction_comment_indices[section_index] == NULL) {
    return NULL;
  }
  return &lookup->instruction_comment_indices[section_index][offset];
}

static const size_t *lookup_instruction_comment_index_slot_const(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->instruction_comment_indices == NULL ||
      lookup->instruction_comment_extents == NULL || offset >= lookup->instruction_comment_extents[section_index] ||
      lookup->instruction_comment_indices[section_index] == NULL) {
    return NULL;
  }
  return &lookup->instruction_comment_indices[section_index][offset];
}

int render_lookup_add_instruction_comment(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    const char *comment) {
  size_t index;
  size_t *index_slot;
  M68kRenderInstructionComment *grown;
  size_t next_capacity;
  if (lookup == NULL || comment == NULL || comment[0] == '\0') return 0;
  index_slot = lookup_instruction_comment_index_slot(lookup, section_index, offset);
  if (index_slot != NULL && *index_slot != 0U && *index_slot <= lookup->instruction_comment_count) {
    M68kRenderInstructionComment *entry = &lookup->instruction_comments[*index_slot - 1U];
    if (entry->section_index == section_index && entry->offset == offset) {
      (void)append_comment_part_local(entry->comment, sizeof(entry->comment), comment);
      render_lookup_mark_boundary_flag(lookup, section_index, offset, M68K_RENDER_BOUNDARY_COMMENT);
      return 0;
    }
    *index_slot = 0U;
  }
  for (index = 0U; index < lookup->instruction_comment_count; ++index) {
    M68kRenderInstructionComment *entry = &lookup->instruction_comments[index];
    if (entry->section_index != section_index || entry->offset != offset) continue;
    if (index_slot != NULL) *index_slot = index + 1U;
    (void)append_comment_part_local(entry->comment, sizeof(entry->comment), comment);
    render_lookup_mark_boundary_flag(lookup, section_index, offset, M68K_RENDER_BOUNDARY_COMMENT);
    return 0;
  }
  if (lookup->instruction_comment_count == lookup->instruction_comment_capacity) {
    next_capacity = lookup->instruction_comment_capacity == 0U ? 32U : lookup->instruction_comment_capacity * 2U;
    grown = (M68kRenderInstructionComment *)render_lookup_grow_array(lookup, lookup->instruction_comments,
      lookup->instruction_comment_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->instruction_comments = grown;
    lookup->instruction_comment_capacity = next_capacity;
  }
  memset(&lookup->instruction_comments[lookup->instruction_comment_count], 0,
    sizeof(lookup->instruction_comments[lookup->instruction_comment_count]));
  lookup->instruction_comments[lookup->instruction_comment_count].section_index = section_index;
  lookup->instruction_comments[lookup->instruction_comment_count].offset = offset;
  snprintf(lookup->instruction_comments[lookup->instruction_comment_count].comment,
    sizeof(lookup->instruction_comments[lookup->instruction_comment_count].comment), "%s", comment);
  if (index_slot != NULL) *index_slot = lookup->instruction_comment_count + 1U;
  ++lookup->instruction_comment_count;
  render_lookup_mark_boundary_flag(lookup, section_index, offset, M68K_RENDER_BOUNDARY_COMMENT);
  return 0;
}

int render_lookup_add_recovered_function_arg(M68kRenderLookup *lookup, size_t section_index,
    uint32_t function_offset, uint16_t stack_offset, uint8_t reg_kind, uint8_t reg_index,
    const PlatformFactsV2CallInput *input) {
  size_t index;
  M68kRenderRecoveredFunctionArg *grown;
  size_t next_capacity;
  if (lookup == NULL || input == NULL || stack_offset == 0U || reg_kind == 0U || reg_index >= 8U) return 0;
  for (index = 0U; index < lookup->recovered_function_arg_count; ++index) {
    M68kRenderRecoveredFunctionArg *entry = &lookup->recovered_function_args[index];
    if (entry->section_index == section_index && entry->function_offset == function_offset &&
        entry->stack_offset == stack_offset && entry->reg_kind == reg_kind && entry->reg_index == reg_index) {
      if (entry->input_valid == 0U || !platform_call_input_equal(&entry->input, input)) {
        entry->input_valid = 0U;
        platform_facts_v2_call_input_init(&entry->input);
      }
      return 0;
    }
  }
  if (lookup->recovered_function_arg_count == lookup->recovered_function_arg_capacity) {
    next_capacity = lookup->recovered_function_arg_capacity == 0U ? 16U :
      lookup->recovered_function_arg_capacity * 2U;
    grown = (M68kRenderRecoveredFunctionArg *)render_lookup_grow_array(lookup,
      lookup->recovered_function_args, lookup->recovered_function_arg_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->recovered_function_args = grown;
    lookup->recovered_function_arg_capacity = next_capacity;
  }
  memset(&lookup->recovered_function_args[lookup->recovered_function_arg_count], 0,
    sizeof(lookup->recovered_function_args[lookup->recovered_function_arg_count]));
  lookup->recovered_function_args[lookup->recovered_function_arg_count].section_index = section_index;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].function_offset = function_offset;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].stack_offset = stack_offset;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].reg_kind = reg_kind;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].reg_index = reg_index;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].input_valid = 1U;
  lookup->recovered_function_args[lookup->recovered_function_arg_count].input = *input;
  ++lookup->recovered_function_arg_count;
  return 0;
}

int render_lookup_add_platform_derived_summary(M68kRenderLookup *lookup, size_t section_index,
    uint32_t target_offset, const AmigaOsLibraryVectorInfo *vector) {
  size_t index;
  M68kRenderPlatformDerivedSummary *grown;
  size_t next_capacity;
  if (lookup == NULL || vector == NULL) return 0;
  for (index = 0U; index < lookup->platform_derived_summary_count; ++index) {
    M68kRenderPlatformDerivedSummary *entry = &lookup->platform_derived_summaries[index];
    if (entry->section_index == section_index && entry->target_offset == target_offset) {
      if (entry->vector != vector) entry->vector = NULL;
      return 0;
    }
  }
  if (lookup->platform_derived_summary_count == lookup->platform_derived_summary_capacity) {
    next_capacity = lookup->platform_derived_summary_capacity == 0U ? 16U :
      lookup->platform_derived_summary_capacity * 2U;
    grown = (M68kRenderPlatformDerivedSummary *)render_lookup_grow_array(lookup,
      lookup->platform_derived_summaries, lookup->platform_derived_summary_count, sizeof(*grown),
      next_capacity);
    if (grown == NULL) return -1;
    lookup->platform_derived_summaries = grown;
    lookup->platform_derived_summary_capacity = next_capacity;
  }
  memset(&lookup->platform_derived_summaries[lookup->platform_derived_summary_count], 0,
    sizeof(lookup->platform_derived_summaries[lookup->platform_derived_summary_count]));
  lookup->platform_derived_summaries[lookup->platform_derived_summary_count].section_index = section_index;
  lookup->platform_derived_summaries[lookup->platform_derived_summary_count].target_offset = target_offset;
  lookup->platform_derived_summaries[lookup->platform_derived_summary_count].vector = vector;
  ++lookup->platform_derived_summary_count;
  return 0;
}

int render_lookup_add_typed_slot_effect(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    int16_t displacement, const AmigaOsCallOutputInfo *output) {
  size_t index;
  M68kRenderTypedSlotEffect *grown;
  size_t next_capacity;
  if (lookup == NULL || output == NULL || output->reg_kind == AMIGA_OS_REGISTER_NONE ||
      output->reg_index >= 8U) {
    return 0;
  }
  for (index = 0U; index < lookup->typed_slot_effect_count; ++index) {
    M68kRenderTypedSlotEffect *entry = &lookup->typed_slot_effects[index];
    if (entry->section_index == section_index && entry->offset == offset &&
        entry->displacement == displacement) {
      if (entry->output != output) entry->output = NULL;
      return 0;
    }
  }
  if (lookup->typed_slot_effect_count == lookup->typed_slot_effect_capacity) {
    next_capacity = lookup->typed_slot_effect_capacity == 0U ? 16U : lookup->typed_slot_effect_capacity * 2U;
    grown = (M68kRenderTypedSlotEffect *)render_lookup_grow_array(lookup, lookup->typed_slot_effects,
      lookup->typed_slot_effect_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->typed_slot_effects = grown;
    lookup->typed_slot_effect_capacity = next_capacity;
  }
  memset(&lookup->typed_slot_effects[lookup->typed_slot_effect_count], 0,
    sizeof(lookup->typed_slot_effects[lookup->typed_slot_effect_count]));
  lookup->typed_slot_effects[lookup->typed_slot_effect_count].section_index = section_index;
  lookup->typed_slot_effects[lookup->typed_slot_effect_count].offset = offset;
  lookup->typed_slot_effects[lookup->typed_slot_effect_count].displacement = displacement;
  lookup->typed_slot_effects[lookup->typed_slot_effect_count].output = output;
  ++lookup->typed_slot_effect_count;
  return 0;
}

static int typed_storage_keys_match(const M68kRenderTypedStorageSlot *slot, uint8_t kind, size_t section_index,
    int32_t displacement, uint32_t address) {
  if (slot == NULL || slot->kind != kind) return 0;
  if (kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT) return slot->displacement == displacement;
  if (kind == M68K_RENDER_TYPED_STORAGE_ABSOLUTE)
    return slot->section_index == section_index && slot->address == address;
  if (kind == M68K_RENDER_TYPED_STORAGE_BASE_SLOT)
    return slot->section_index == section_index && slot->address == address && slot->displacement == displacement;
  return 0;
}

static int typed_storage_merge_value(M68kRenderTypedStorageSlot *slot,
    const M68kRenderTypedStoredValue *value) {
  int changed = 0;
  if (slot == NULL || value == NULL || slot->conflicted != 0U || !typed_stored_value_has_useful_info(value))
    return 0;
  {
    int conflict = 0;
    uint16_t merged_struct_id = typed_struct_id_refined_merge(slot->value.struct_id, value->struct_id, &conflict);
    if (conflict) {
      slot->conflicted = 1U;
      slot->value.known = 0U;
      slot->value.output = NULL;
      changed = 1;
    } else if (slot->value.struct_id != merged_struct_id) {
      slot->value.struct_id = merged_struct_id;
      slot->value.output = NULL;
      slot->value.array_element_count = 0U;
      slot->value.array_element_index = 0U;
      slot->value.byte_cursor = 0;
      changed = 1;
    }
  }
  if (slot->conflicted != 0U) {
    slot->conflicted = 1U;
    slot->value.known = 0U;
    slot->value.output = NULL;
    changed = 1;
  } else {
    if (slot->value.array_element_count != value->array_element_count ||
        slot->value.array_element_index != value->array_element_index ||
        slot->value.byte_cursor != value->byte_cursor) {
      slot->value.array_element_count = 0U;
      slot->value.array_element_index = 0U;
      slot->value.byte_cursor = 0;
      changed = 1;
    }
    if (slot->value.output == NULL && value->output != NULL &&
        (slot->value.struct_id == AMIGA_OS_STRUCT_ID_NONE ||
          value->output->struct_id == AMIGA_OS_STRUCT_ID_NONE ||
          value->output->struct_id == slot->value.struct_id)) {
      slot->value.output = value->output;
      changed = 1;
    } else if (slot->value.output != NULL && value->output != NULL && slot->value.output != value->output) {
      slot->value.output = NULL;
      changed = 1;
    }
    if (slot->value.layout_base_id != value->layout_base_id) {
      slot->conflicted = 1U;
      slot->value.known = 0U;
      slot->value.layout_base_id = 0U;
      changed = 1;
    }
    if (value->app_address_known) {
      if (!slot->value.app_address_known) {
        slot->value.app_address_known = 1U;
        slot->value.app_displacement = value->app_displacement;
        slot->value.app_base_evidence_kind = value->app_base_evidence_kind;
        changed = 1;
      } else if (slot->value.app_displacement == value->app_displacement &&
          slot->value.app_base_evidence_kind != M68K_APP_SLOT_BASE_UNSPECIFIED &&
          slot->value.app_base_evidence_kind != value->app_base_evidence_kind) {
        slot->value.app_base_evidence_kind = M68K_APP_SLOT_BASE_UNSPECIFIED;
        changed = 1;
      } else if (slot->value.app_displacement != value->app_displacement) {
        slot->conflicted = 1U;
        slot->value.known = 0U;
        slot->value.output = NULL;
        changed = 1;
      }
    }
    if (value->pointer_value_known) {
      if (!slot->value.pointer_value_known) {
        slot->value.pointer_value_known = 1U;
        slot->value.pointer_value = value->pointer_value;
        changed = 1;
      } else if (slot->value.pointer_value != value->pointer_value) {
        slot->conflicted = 1U;
        slot->value.known = 0U;
        slot->value.output = NULL;
        changed = 1;
      }
    }
    if (slot->value.output != NULL && slot->value.struct_id != AMIGA_OS_STRUCT_ID_NONE &&
        slot->value.output->struct_id != AMIGA_OS_STRUCT_ID_NONE &&
        slot->value.output->struct_id != slot->value.struct_id) {
      slot->value.output = NULL;
      changed = 1;
    }
    {
      M68kRenderTypedProvenance old_provenance = slot->value.provenance;
      typed_provenance_merge(&slot->value.provenance, &value->provenance);
      if (!typed_provenances_equal(&slot->value.provenance, &old_provenance)) changed = 1;
    }
    if (slot->conflicted == 0U && typed_stored_value_has_payload(&slot->value)) slot->value.known = 1U;
  }
  return changed;
}

int render_lookup_add_typed_storage_slot(M68kRenderLookup *lookup, uint8_t kind, size_t section_index,
    int32_t displacement, uint32_t address, const M68kRenderTypedStoredValue *value,
    size_t source_section_index, uint32_t source_offset, int *out_added) {
  size_t index;
  M68kRenderTypedStorageSlot *grown;
  size_t next_capacity;
  if (out_added != NULL) *out_added = 0;
  if (lookup == NULL || !typed_stored_value_has_useful_info(value)) return 0;
  if (kind != M68K_RENDER_TYPED_STORAGE_APP_SLOT && kind != M68K_RENDER_TYPED_STORAGE_ABSOLUTE &&
      kind != M68K_RENDER_TYPED_STORAGE_BASE_SLOT) {
    return 0;
  }
  for (index = 0U; index < lookup->typed_storage_slot_count; ++index) {
    M68kRenderTypedStorageSlot *slot = &lookup->typed_storage_slots[index];
    int changed;
    if (!typed_storage_keys_match(slot, kind, section_index, displacement, address)) continue;
    changed = typed_storage_merge_value(slot, value);
    if (changed) {
      slot->source_section_index = source_section_index;
      slot->source_offset = source_offset;
      if (out_added != NULL) *out_added = 1;
    }
    return 0;
  }
  if (lookup->typed_storage_slot_count == lookup->typed_storage_slot_capacity) {
    next_capacity = lookup->typed_storage_slot_capacity == 0U ? 16U : lookup->typed_storage_slot_capacity * 2U;
    grown = (M68kRenderTypedStorageSlot *)render_lookup_grow_array(lookup, lookup->typed_storage_slots,
      lookup->typed_storage_slot_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->typed_storage_slots = grown;
    lookup->typed_storage_slot_capacity = next_capacity;
  }
  memset(&lookup->typed_storage_slots[lookup->typed_storage_slot_count], 0,
    sizeof(lookup->typed_storage_slots[lookup->typed_storage_slot_count]));
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].kind = kind;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].section_index = section_index;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].displacement = displacement;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].address = address;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].source_section_index = source_section_index;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].source_offset = source_offset;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].value = *value;
  lookup->typed_storage_slots[lookup->typed_storage_slot_count].value.known = 1U;
  ++lookup->typed_storage_slot_count;
  if (out_added != NULL) *out_added = 1;
  return 0;
}

int render_lookup_conflict_typed_storage_slot(M68kRenderLookup *lookup, uint8_t kind, size_t section_index,
    int32_t displacement, uint32_t address, size_t source_section_index, uint32_t source_offset, int *out_added) {
  size_t index;
  if (out_added != NULL) *out_added = 0;
  if (lookup == NULL) return 0;
  if (kind != M68K_RENDER_TYPED_STORAGE_APP_SLOT && kind != M68K_RENDER_TYPED_STORAGE_ABSOLUTE &&
      kind != M68K_RENDER_TYPED_STORAGE_BASE_SLOT) {
    return 0;
  }
  for (index = 0U; index < lookup->typed_storage_slot_count; ++index) {
    M68kRenderTypedStorageSlot *slot = &lookup->typed_storage_slots[index];
    if (!typed_storage_keys_match(slot, kind, section_index, displacement, address)) continue;
    if (slot->conflicted == 0U) {
      slot->conflicted = 1U;
      slot->value.known = 0U;
      slot->value.output = NULL;
      if (out_added != NULL) *out_added = 1;
    }
    return 0;
  }
  (void)source_section_index;
  (void)source_offset;
  return 0;
}

static int render_lookup_add_typed_app_slot_internal(M68kRenderLookup *lookup, int16_t displacement,
    uint16_t struct_id, uint8_t inline_region, size_t source_section_index, uint32_t source_offset,
    int *out_added) {
  size_t index;
  M68kRenderTypedAppSlot *grown;
  size_t next_capacity;
  M68kRenderTypedStoredValue value;
  int storage_added = 0;
  if (out_added != NULL) *out_added = 0;
  if (lookup == NULL || struct_id == AMIGA_OS_STRUCT_ID_NONE) return 0;
  typed_stored_value_clear(&value);
  value.known = 1U;
  value.struct_id = struct_id;
  if (render_lookup_add_typed_storage_slot(lookup, M68K_RENDER_TYPED_STORAGE_APP_SLOT, (size_t)-1, displacement,
      0U, &value, source_section_index, source_offset, &storage_added) != 0) {
    return -1;
  }
  if (storage_added && out_added != NULL) *out_added = 1;
  for (index = 0U; index < lookup->typed_app_slot_count; ++index) {
    M68kRenderTypedAppSlot *entry = &lookup->typed_app_slots[index];
    if (entry->displacement != displacement) continue;
    if (entry->struct_id != struct_id && entry->conflicted == 0U) {
      int conflict = 0;
      uint16_t merged_struct_id = typed_struct_id_refined_merge(entry->struct_id, struct_id, &conflict);
      if (conflict) {
        entry->conflicted = 1U;
        if (out_added != NULL) *out_added = 1;
      } else if (merged_struct_id != entry->struct_id) {
        entry->struct_id = merged_struct_id;
        entry->source_section_index = source_section_index;
        entry->source_offset = source_offset;
        if (out_added != NULL) *out_added = 1;
      }
    }
    if (inline_region != 0U && entry->inline_region == 0U && entry->conflicted == 0U) {
      entry->inline_region = 1U;
      entry->source_section_index = source_section_index;
      entry->source_offset = source_offset;
      if (out_added != NULL) *out_added = 1;
    }
    return 0;
  }
  if (lookup->typed_app_slot_count == lookup->typed_app_slot_capacity) {
    next_capacity = lookup->typed_app_slot_capacity == 0U ? 16U : lookup->typed_app_slot_capacity * 2U;
    grown = (M68kRenderTypedAppSlot *)render_lookup_grow_array(lookup, lookup->typed_app_slots,
      lookup->typed_app_slot_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->typed_app_slots = grown;
    lookup->typed_app_slot_capacity = next_capacity;
  }
  lookup->typed_app_slots[lookup->typed_app_slot_count].displacement = displacement;
  lookup->typed_app_slots[lookup->typed_app_slot_count].struct_id = struct_id;
  lookup->typed_app_slots[lookup->typed_app_slot_count].conflicted = 0U;
  lookup->typed_app_slots[lookup->typed_app_slot_count].inline_region = inline_region != 0U ? 1U : 0U;
  lookup->typed_app_slots[lookup->typed_app_slot_count].source_section_index = source_section_index;
  lookup->typed_app_slots[lookup->typed_app_slot_count].source_offset = source_offset;
  ++lookup->typed_app_slot_count;
  if (out_added != NULL) *out_added = 1;
  return 0;
}

int render_lookup_add_typed_app_slot(M68kRenderLookup *lookup, int16_t displacement, uint16_t struct_id,
    size_t source_section_index, uint32_t source_offset, int *out_added) {
  return render_lookup_add_typed_app_slot_internal(lookup, displacement, struct_id, 0U,
    source_section_index, source_offset, out_added);
}

int render_lookup_add_typed_app_slot_region(M68kRenderLookup *lookup, int16_t displacement, uint16_t struct_id,
    size_t source_section_index, uint32_t source_offset, int *out_added) {
  return render_lookup_add_typed_app_slot_internal(lookup, displacement, struct_id, 1U,
    source_section_index, source_offset, out_added);
}

static int render_lookup_add_typed_access_by_names(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t operand_index, uint8_t base_reg, int16_t displacement, uint16_t struct_size,
    int16_t array_element_addend, int32_t base_cursor, uint16_t field_byte_offset,
    const M68kRenderResolvedStructField *field,
    const M68kRenderTypedProvenance *provenance, const M68kAddressValueTableOriginIR *table_origin) {
  size_t index;
  M68kRenderTypedAccess *grown;
  size_t next_capacity;
  if (lookup == NULL || field == NULL || field->field_expr[0] == '\0' || field->root_struct_name[0] == '\0' ||
      field->owner_struct_name[0] == '\0' || field->field_name[0] == '\0' || operand_index >= 4U || base_reg >= 8U) {
    return 0;
  }
  for (index = 0U; index < lookup->typed_access_count; ++index) {
    const M68kRenderTypedAccess *entry = &lookup->typed_accesses[index];
    if (entry->section_index == section_index && entry->offset == offset &&
        entry->operand_index == operand_index) {
      return 0;
    }
  }
  if (lookup->typed_access_count == lookup->typed_access_capacity) {
    next_capacity = lookup->typed_access_capacity == 0U ? 32U : lookup->typed_access_capacity * 2U;
    grown = (M68kRenderTypedAccess *)render_lookup_grow_array(lookup, lookup->typed_accesses,
      lookup->typed_access_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->typed_accesses = grown;
    lookup->typed_access_capacity = next_capacity;
  }
  memset(&lookup->typed_accesses[lookup->typed_access_count], 0,
    sizeof(lookup->typed_accesses[lookup->typed_access_count]));
  lookup->typed_accesses[lookup->typed_access_count].section_index = section_index;
  lookup->typed_accesses[lookup->typed_access_count].offset = offset;
  lookup->typed_accesses[lookup->typed_access_count].operand_index = operand_index;
  lookup->typed_accesses[lookup->typed_access_count].base_reg = base_reg;
  lookup->typed_accesses[lookup->typed_access_count].displacement = displacement;
  lookup->typed_accesses[lookup->typed_access_count].field_offset = field->offset;
  lookup->typed_accesses[lookup->typed_access_count].struct_size = struct_size;
  lookup->typed_accesses[lookup->typed_access_count].field_size = field->size;
  lookup->typed_accesses[lookup->typed_access_count].field_byte_offset = field_byte_offset;
  lookup->typed_accesses[lookup->typed_access_count].array_element_addend = array_element_addend;
  lookup->typed_accesses[lookup->typed_access_count].base_cursor = base_cursor;
  lookup->typed_accesses[lookup->typed_access_count].inherited = field->inherited;
  lookup->typed_accesses[lookup->typed_access_count].nested = field->nested;
  if (provenance != NULL) {
    lookup->typed_accesses[lookup->typed_access_count].provenance = *provenance;
  }
  if (table_origin != NULL) lookup->typed_accesses[lookup->typed_access_count].table_origin = *table_origin;
  snprintf(lookup->typed_accesses[lookup->typed_access_count].root_struct_name,
    sizeof(lookup->typed_accesses[lookup->typed_access_count].root_struct_name), "%s", field->root_struct_name);
  snprintf(lookup->typed_accesses[lookup->typed_access_count].owner_struct_name,
    sizeof(lookup->typed_accesses[lookup->typed_access_count].owner_struct_name), "%s", field->owner_struct_name);
  snprintf(lookup->typed_accesses[lookup->typed_access_count].field_name,
    sizeof(lookup->typed_accesses[lookup->typed_access_count].field_name), "%s", field->field_name);
  snprintf(lookup->typed_accesses[lookup->typed_access_count].field_expr,
    sizeof(lookup->typed_accesses[lookup->typed_access_count].field_expr), "%s", field->field_expr);
  ++lookup->typed_access_count;
  return 0;
}

int render_lookup_add_typed_access(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t operand_index, uint8_t base_reg, int16_t displacement, uint16_t root_struct_id,
    const AmigaOsResolvedStructFieldInfo *field, const char *field_expr,
    const M68kRenderTypedProvenance *provenance) {
  M68kRenderResolvedStructField resolved;
  const char *root_struct_name;
  const char *owner_struct_name;
  const char *field_name;
  if (lookup == NULL || field == NULL || field_expr == NULL || field_expr[0] == '\0' ||
      root_struct_id == AMIGA_OS_STRUCT_ID_NONE) {
    return 0;
  }
  root_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, root_struct_id);
  owner_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, field->owner_struct_id);
  field_name = amiga_os_name(M68K_PLATFORM_NAME_FIELD, field->field_id);
  if (root_struct_name == NULL || owner_struct_name == NULL || field_name == NULL) return 0;
  memset(&resolved, 0, sizeof(resolved));
  resolved.offset = field->offset;
  resolved.size = field->size;
  resolved.inherited = field->inherited;
  resolved.nested = field->nested;
  snprintf(resolved.root_struct_name, sizeof(resolved.root_struct_name), "%s", root_struct_name);
  snprintf(resolved.owner_struct_name, sizeof(resolved.owner_struct_name), "%s", owner_struct_name);
  snprintf(resolved.field_name, sizeof(resolved.field_name), "%s", field_name);
  snprintf(resolved.field_expr, sizeof(resolved.field_expr), "%s", field_expr);
  return render_lookup_add_typed_access_by_names(lookup, section_index, offset, operand_index, base_reg,
    displacement, amiga_struct_size_for_struct_id(root_struct_id), 0U, 0, 0U, &resolved, provenance, NULL);
}

static int render_lookup_add_unresolved_typed_access_by_names(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint8_t operand_index, uint8_t base_reg, int32_t displacement, const char *root_struct_name,
    uint16_t struct_size, uint8_t access_size, uint8_t classification, uint16_t container_candidate_count,
    const char *container_struct_name, const char *container_field_expr, uint8_t refinement_applied,
    const char *refined_struct_name, const M68kRenderTypedProvenance *provenance) {
  size_t index;
  M68kRenderUnresolvedTypedAccess *grown;
  size_t next_capacity;
  if (lookup == NULL || root_struct_name == NULL || root_struct_name[0] == '\0' ||
      operand_index >= 4U || base_reg >= 8U) return 0;
  for (index = 0U; index < lookup->unresolved_typed_access_count; ++index) {
    const M68kRenderUnresolvedTypedAccess *entry = &lookup->unresolved_typed_accesses[index];
    if (entry->section_index == section_index && entry->offset == offset &&
        entry->operand_index == operand_index) {
      return 0;
    }
  }
  if (lookup->unresolved_typed_access_count == lookup->unresolved_typed_access_capacity) {
    next_capacity = lookup->unresolved_typed_access_capacity == 0U
      ? 16U
      : lookup->unresolved_typed_access_capacity * 2U;
    grown = (M68kRenderUnresolvedTypedAccess *)render_lookup_grow_array(lookup,
      lookup->unresolved_typed_accesses, lookup->unresolved_typed_access_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->unresolved_typed_accesses = grown;
    lookup->unresolved_typed_access_capacity = next_capacity;
  }
  memset(&lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count], 0,
    sizeof(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count]));
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].section_index = section_index;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].offset = offset;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].operand_index = operand_index;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].base_reg = base_reg;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].displacement = displacement;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].struct_size = struct_size;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].access_size = access_size;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].classification = classification;
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_candidate_count =
    container_candidate_count;
  if (container_struct_name != NULL && container_struct_name[0] != '\0')
    snprintf(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_struct_name,
      sizeof(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_struct_name),
      "%s", container_struct_name);
  if (container_field_expr != NULL && container_field_expr[0] != '\0')
    snprintf(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_field_expr,
      sizeof(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].container_field_expr),
      "%s", container_field_expr);
  lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].refinement_applied =
    refinement_applied != 0U ? 1U : 0U;
  if (provenance != NULL)
    lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].provenance = *provenance;
  snprintf(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].root_struct_name,
    sizeof(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].root_struct_name),
    "%s", root_struct_name);
  if (refinement_applied != 0U && refined_struct_name != NULL && refined_struct_name[0] != '\0') {
    snprintf(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].refined_struct_name,
      sizeof(lookup->unresolved_typed_accesses[lookup->unresolved_typed_access_count].refined_struct_name),
      "%s", refined_struct_name);
  }
  ++lookup->unresolved_typed_access_count;
  return 0;
}

int render_lookup_add_unresolved_typed_access(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint8_t operand_index, uint8_t base_reg, int32_t displacement, uint16_t root_struct_id,
    uint16_t struct_size, uint8_t access_size, uint8_t refinement_applied, uint16_t refined_struct_id,
    const M68kRenderTypedProvenance *provenance) {
  const char *root_struct_name;
  const char *refined_struct_name = NULL;
  uint8_t classification = M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_FIELD_GAP;
  uint16_t container_candidate_count = 0U;
  char container_struct_name[64];
  char container_field_expr[96];
  if (lookup == NULL || root_struct_id == AMIGA_OS_STRUCT_ID_NONE || operand_index >= 4U || base_reg >= 8U)
    return 0;
  root_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, root_struct_id);
  if (root_struct_name == NULL || root_struct_name[0] == '\0') return 0;
  container_struct_name[0] = '\0';
  container_field_expr[0] = '\0';
  if (displacement >= INT16_MIN && displacement <= INT16_MAX) {
    classify_unresolved_typed_access(root_struct_id, (int16_t)displacement, struct_size, access_size,
      &classification, &container_candidate_count, container_struct_name, sizeof(container_struct_name),
      container_field_expr, sizeof(container_field_expr), NULL);
  }
  if (refinement_applied != 0U && refined_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    refined_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, refined_struct_id);
    if (refined_struct_name == NULL || refined_struct_name[0] == '\0') {
      refinement_applied = 0U;
      refined_struct_id = AMIGA_OS_STRUCT_ID_NONE;
    } else {
      classification = M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION;
      snprintf(container_struct_name, sizeof(container_struct_name), "%s", refined_struct_name);
      (void)amiga_os_resolve_struct_field_symbol_expr_by_struct_id(refined_struct_id, (int16_t)displacement, 0,
        container_field_expr, sizeof(container_field_expr));
    }
  }
  return render_lookup_add_unresolved_typed_access_by_names(lookup, section_index, offset, operand_index, base_reg,
    displacement, root_struct_name, struct_size, access_size, classification, container_candidate_count,
    container_struct_name,
    container_field_expr, refinement_applied, refined_struct_name, provenance);
}

int render_lookup_add_string_span(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint32_t size) {
  size_t index;
  M68kRenderStringSpan *grown;
  size_t next_capacity;
  if (lookup == NULL || size == 0U) return 0;
  for (index = 0U; index < lookup->string_span_count; ++index) {
    M68kRenderStringSpan *entry = &lookup->string_spans[index];
    if (entry->section_index == section_index && entry->offset == offset) {
      if (entry->size != size) entry->size = 0U;
      return 0;
    }
  }
  if (lookup->string_span_count == lookup->string_span_capacity) {
    next_capacity = lookup->string_span_capacity == 0U ? 16U : lookup->string_span_capacity * 2U;
    grown = (M68kRenderStringSpan *)render_lookup_grow_array(lookup, lookup->string_spans,
      lookup->string_span_count, sizeof(*grown), next_capacity);
    if (grown == NULL) return -1;
    lookup->string_spans = grown;
    lookup->string_span_capacity = next_capacity;
  }
  lookup->string_spans[lookup->string_span_count].section_index = section_index;
  lookup->string_spans[lookup->string_span_count].offset = offset;
  lookup->string_spans[lookup->string_span_count].size = size;
  ++lookup->string_span_count;
  render_lookup_mark_boundary_flag(lookup, section_index, offset, M68K_RENDER_BOUNDARY_STRING_SPAN);
  if (section_index < lookup->section_count && lookup->string_span_indices != NULL &&
      lookup->string_span_index_extents != NULL && offset <= lookup->string_span_index_extents[section_index] &&
      lookup->string_span_indices[section_index] != NULL) {
    lookup->string_span_indices[section_index][offset] = lookup->string_span_count;
  }
  return 0;
}

const char *lookup_instruction_comment(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  size_t index;
  const size_t *index_slot;
  if (lookup == NULL) return NULL;
  if ((render_lookup_boundary_flags(lookup, section_index, offset) & M68K_RENDER_BOUNDARY_COMMENT) == 0U)
    return NULL;
  index_slot = lookup_instruction_comment_index_slot_const(lookup, section_index, offset);
  if (index_slot != NULL && *index_slot != 0U && *index_slot <= lookup->instruction_comment_count) {
    const M68kRenderInstructionComment *entry = &lookup->instruction_comments[*index_slot - 1U];
    if (entry->section_index == section_index && entry->offset == offset && entry->comment[0] != '\0')
      return entry->comment;
  }
  for (index = 0U; index < lookup->instruction_comment_count; ++index) {
    const M68kRenderInstructionComment *entry = &lookup->instruction_comments[index];
    if (entry->section_index == section_index && entry->offset == offset && entry->comment[0] != '\0')
      return entry->comment;
  }
  return NULL;
}

const M68kRenderStringSpan *lookup_string_span_at_offset(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  if (lookup == NULL) return NULL;
  if ((render_lookup_boundary_flags(lookup, section_index, offset) & M68K_RENDER_BOUNDARY_STRING_SPAN) == 0U)
    return NULL;
  if (section_index < lookup->section_count && lookup->string_span_indices != NULL &&
      lookup->string_span_index_extents != NULL && offset <= lookup->string_span_index_extents[section_index] &&
      lookup->string_span_indices[section_index] != NULL) {
    size_t index = lookup->string_span_indices[section_index][offset];
    if (index != 0U && index <= lookup->string_span_count) {
      const M68kRenderStringSpan *entry = &lookup->string_spans[index - 1U];
      if (entry->section_index == section_index && entry->offset == offset && entry->size != 0U) return entry;
    }
  }
  return NULL;
}

static const char *amiga_library_base_name_for_render_effect(const char *library_name) {
  const char *base_name;
  if (library_name == NULL || library_name[0] == '\0') return NULL;
  base_name = render_lookup_amiga_library_base_name_for_library_name(library_name);
  return base_name != NULL && base_name[0] != '\0' ? base_name : NULL;
}

static const char *amiga_library_base_name_for_render_effect_id(uint16_t library_id) {
  const char *library_name = platform_facts_v2_library_name_for_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, library_id);
  return amiga_library_base_name_for_render_effect(library_name);
}

static int append_render_lookup_platform_effects_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->global_base_slot_count; ++index) {
    const M68kRenderGlobalBaseSlot *slot = &lookup->global_base_slots[index];
    const char *base_name = amiga_library_base_name_for_render_effect_id(slot->library_id);
    if (slot->has_source == 0U || slot->source_section_index != section_analysis->section_index ||
        slot->has_library_id == 0U || slot->conflicted != 0U || base_name == NULL) {
      continue;
    }
    if (m68k_ir_section_analysis_append_recovered_platform_global_base_slot_effect(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->source_offset, slot->section_index, slot->offset,
        base_name) != 0) {
      return -1;
    }
  }
  for (index = 0U; index < lookup->base_field_slot_count; ++index) {
    const M68kRenderBaseFieldSlot *slot = &lookup->base_field_slots[index];
    const char *base_name = amiga_library_base_name_for_render_effect_id(slot->library_id);
    if (slot->has_source == 0U || slot->source_section_index != section_analysis->section_index ||
        slot->has_library_id == 0U || slot->conflicted != 0U || !base_field_slot_is_base_pointer(slot) ||
        base_name == NULL) {
      continue;
    }
    if (!render_base_field_slot_owner_is_app_base(slot)) continue;
    if (m68k_ir_section_analysis_append_recovered_platform_base_slot(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->displacement, base_name) != 0 ||
        m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->source_offset, M68K_PLATFORM_EFFECT_WRITE_BASE_SLOT,
        0U, 0U, slot->displacement, INT16_MIN, base_name, NULL, NULL, NULL, NULL, 0U, 0) != 0) {
      return -1;
    }
  }
  for (index = 0U; index < lookup->typed_slot_effect_count; ++index) {
    const M68kRenderTypedSlotEffect *effect = &lookup->typed_slot_effects[index];
    const AmigaOsCallOutputInfo *output = effect->output;
    const char *symbol_name;
    const char *type_name;
    const char *semantic_kind;
    const char *value_domain_name;
    if (effect->section_index != section_analysis->section_index || output == NULL) continue;
    symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id);
    type_name = amiga_output_type_or_struct_name(output);
    semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id);
    value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id);
    if ((symbol_name == NULL || symbol_name[0] == '\0') &&
        (type_name == NULL || type_name[0] == '\0') &&
        (semantic_kind == NULL || semantic_kind[0] == '\0') &&
        (value_domain_name == NULL || value_domain_name[0] == '\0')) {
      continue;
    }
    if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, effect->offset, M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT,
        0U, 0U, effect->displacement, INT16_MIN, NULL, symbol_name, type_name, semantic_kind,
        value_domain_name, 0U, 0) != 0) {
      return -1;
    }
  }
  for (index = 0U; index < lookup->typed_storage_slot_count; ++index) {
    const M68kRenderTypedStorageSlot *slot = &lookup->typed_storage_slots[index];
    const char *symbol_name;
    const char *type_name;
    const char *semantic_kind;
    const char *value_domain_name;
    if (slot->conflicted != 0U || slot->source_section_index != section_analysis->section_index ||
        !typed_stored_value_has_useful_info(&slot->value)) {
      continue;
    }
    typed_stored_value_platform_names(&slot->value, &symbol_name, &type_name, &semantic_kind,
      &value_domain_name);
    if ((symbol_name == NULL || symbol_name[0] == '\0') &&
        (type_name == NULL || type_name[0] == '\0') &&
        (semantic_kind == NULL || semantic_kind[0] == '\0') &&
        (value_domain_name == NULL || value_domain_name[0] == '\0')) {
      continue;
    }
    if (slot->kind == M68K_RENDER_TYPED_STORAGE_APP_SLOT) {
      int has_direct_slot_effect = 0;
      size_t effect_index;
      if (slot->displacement < INT16_MIN || slot->displacement > INT16_MAX) continue;
      for (effect_index = 0U; effect_index < lookup->typed_slot_effect_count; ++effect_index) {
        const M68kRenderTypedSlotEffect *effect = &lookup->typed_slot_effects[effect_index];
        if (effect->section_index == slot->source_section_index && effect->offset == slot->source_offset &&
            effect->displacement == (int16_t)slot->displacement) {
          has_direct_slot_effect = 1;
          break;
        }
      }
      if (has_direct_slot_effect) continue;
      if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis,
          M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->source_offset, M68K_PLATFORM_EFFECT_WRITE_TYPED_SLOT,
          0U, 0U, (int16_t)slot->displacement, INT16_MIN, NULL, symbol_name, type_name, semantic_kind,
          value_domain_name, 0U, 0) != 0) {
        return -1;
      }
    } else if (slot->kind == M68K_RENDER_TYPED_STORAGE_ABSOLUTE) {
      if (m68k_ir_section_analysis_append_recovered_platform_typed_global_slot_effect(section_analysis,
          M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->source_offset, slot->section_index, slot->address,
          symbol_name, type_name, semantic_kind, value_domain_name) != 0) {
        return -1;
      }
    } else if (slot->kind == M68K_RENDER_TYPED_STORAGE_BASE_SLOT) {
      uint32_t target_offset = 0U;
      if (!typed_memory_base_offset_add(slot->address, slot->displacement, &target_offset)) continue;
      if (m68k_ir_section_analysis_append_recovered_platform_typed_global_slot_effect(section_analysis,
          M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->source_offset, slot->section_index, target_offset,
          symbol_name, type_name, semantic_kind, value_domain_name) != 0) {
        return -1;
      }
    }
  }
  return 0;
}

static int append_render_lookup_app_slot_refs_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->app_slot_ref_count; ++index) {
    const M68kRenderAppSlotRef *ref = &lookup->app_slot_refs[index];
    if (ref->section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_app_slot_ref(section_analysis, &ref->ref) != 0) return -1;
  }
  return 0;
}

static int append_render_lookup_runtime_views_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_ranges[index].fact;
    M68kRuntimeViewIR view;
    if (fact == NULL || fact->section_index != section_analysis->section_index ||
        fact->size == 0U || !fact->has_runtime_address) {
      continue;
    }
    memset(&view, 0, sizeof(view));
    view.runtime_view_id = (uint32_t)index;
    view.storage_offset = fact->offset;
    view.size = fact->size;
    view.runtime_address = fact->runtime_address;
    view.kind = fact->runtime_kind;
    view.confidence = fact->confidence;
    if (lookup_runtime_range_materialization(lookup, fact, &view.materialized,
        &view.materialization_reason, &view.relationship) != 0) {
      return -1;
    }
    {
      size_t ref_index;
      uint32_t view_end = view.size <= UINT32_MAX - view.storage_offset
        ? view.storage_offset + view.size
        : UINT32_MAX;
      for (ref_index = 0U; ref_index < lookup->code_start_ref_count; ++ref_index) {
        const M68kFact *code_start = lookup->code_start_refs[ref_index].fact;
        int strong_entry_reason = 0;
        if (code_start == NULL || code_start->section_index != section_analysis->section_index ||
            code_start->offset < view.storage_offset || code_start->offset >= view_end) {
          continue;
        }
        switch (code_start->reason) {
        case M68K_FACT_CODE_START_REASON_SECTION_ENTRY:
        case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_OFFSET:
        case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT:
        case M68K_FACT_CODE_START_REASON_RUNTIME_VIEW_ENTRY:
        case M68K_FACT_CODE_START_REASON_PLATFORM_LOADSEG_ENTRY:
          strong_entry_reason = 1;
          break;
        default:
          strong_entry_reason = 0;
          break;
        }
        if (!strong_entry_reason || code_start->confidence < M68K_FACT_CONFIDENCE_TOOL_INFERRED ||
            !code_start->has_runtime_address) {
          continue;
        }
        if (code_start->offset - view.storage_offset > UINT32_MAX - view.runtime_address) continue;
        if (code_start->runtime_address != view.runtime_address + (code_start->offset - view.storage_offset))
          continue;
        if (view.entry_point_count != UINT16_MAX) ++view.entry_point_count;
        if (!view.has_entry_point ||
            code_start->confidence > view.entry_confidence ||
            (code_start->confidence == view.entry_confidence &&
             code_start->reason == M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT)) {
          view.has_entry_point = 1U;
          view.entry_confidence = code_start->confidence;
          view.entry_source_offset = code_start->offset;
          view.entry_runtime_address = code_start->runtime_address;
          view.entry_reason = code_start->reason;
        }
      }
    }
    if (m68k_ir_section_analysis_append_runtime_view(section_analysis, &view) != 0) return -1;
  }
  return 0;
}

static uint32_t runtime_address_ref_data_class_flags(const M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    const M68kFact *fact);

static int append_render_lookup_runtime_address_refs_for_section(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL) return 0;
  for (index = 0U; index < lookup->runtime_address_ref_count; ++index) {
    const M68kFact *fact = lookup->runtime_address_refs[index].fact;
    M68kRuntimeAddressRefIR ref;
    if (fact == NULL || fact->section_index != section_analysis->section_index) continue;
    memset(&ref, 0, sizeof(ref));
    ref.offset = fact->offset;
    ref.operand_index = fact->reason;
    ref.has_target = fact->target_section_index < lookup->section_count;
    ref.target_section_index = fact->target_section_index;
    ref.target_offset = fact->target_offset;
    if (fact->has_sink_address) {
      ref.has_sink_address = 1U;
      ref.sink_address = fact->sink_address;
    }
    ref.has_runtime_address = fact->has_runtime_address;
    ref.runtime_address = fact->runtime_address;
    ref.confidence = fact->confidence;
    ref.data_class_flags = runtime_address_ref_data_class_flags(lookup, decode, fact);
    ref.data_class = (char *)m68k_analysis_structured_data_role_name_for_flags(ref.data_class_flags);
    if (m68k_ir_section_analysis_append_runtime_address_ref(section_analysis, &ref) != 0) return -1;
  }
  for (index = 0U; index < lookup->inferred_runtime_address_ref_count; ++index) {
    const M68kRenderInferredRuntimeAddressRef *entry = &lookup->inferred_runtime_address_refs[index];
    if (entry->section_index != section_analysis->section_index) continue;
    if (m68k_ir_section_analysis_append_runtime_address_ref(section_analysis, &entry->ref) != 0) return -1;
  }
  if (lookup->policy != NULL) {
    uint16_t ref_index;
    for (ref_index = 0U; ref_index < lookup->policy->manual_runtime_address_ref_count &&
         ref_index < M68K_ANALYSIS_MANUAL_RUNTIME_ADDRESS_REF_LIMIT; ++ref_index) {
      const M68kAnalysisManualRuntimeAddressRef *manual_ref = &lookup->policy->manual_runtime_address_refs[ref_index];
      M68kRuntimeAddressRefIR ref;
      if (!manual_ref->has_section_index || manual_ref->section_index != section_analysis->section_index) continue;
      memset(&ref, 0, sizeof(ref));
      ref.offset = manual_ref->offset;
      ref.source_size = manual_ref->size;
      ref.operand_index = UINT32_MAX;
      ref.size = manual_ref->size;
      ref.has_target = manual_ref->has_target;
      ref.target_section_index = manual_ref->target_section_index;
      ref.target_offset = manual_ref->target_offset;
      ref.has_runtime_address = manual_ref->has_runtime_address;
      ref.runtime_address = manual_ref->runtime_address;
      ref.confidence = manual_ref->confidence;
      ref.owner_kind = (char *)manual_ref->owner_kind;
      ref.owner_id = (char *)manual_ref->owner_id;
      ref.owner_layout_id = (char *)manual_ref->owner_layout_id;
      ref.owner_element_offset = manual_ref->owner_element_offset;
      ref.xref_generation_mode = (char *)manual_ref->xref_generation_mode;
      if (m68k_ir_section_analysis_append_runtime_address_ref(section_analysis, &ref) != 0) return -1;
    }
  }
  return 0;
}

static int append_render_lookup_code_start_refs_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL) return 0;
  for (index = 0U; index < lookup->code_start_ref_count; ++index) {
    const M68kFact *fact = lookup->code_start_refs[index].fact;
    M68kCodeStartRefIR ref;
    if (fact == NULL || fact->section_index != section_analysis->section_index) continue;
    memset(&ref, 0, sizeof(ref));
    ref.offset = fact->offset;
    ref.reason = fact->reason;
    ref.evidence_kind = fact->code_start_evidence_kind;
    ref.confidence = fact->confidence;
    ref.has_runtime_address = fact->has_runtime_address;
    ref.source_section_index = fact->source_section_index;
    ref.source_offset = fact->source_offset;
    ref.runtime_address = fact->runtime_address;
    ref.size = fact->size;
    if (m68k_ir_section_analysis_append_code_start_ref(section_analysis, &ref) != 0) return -1;
  }
  return 0;
}

static const char *render_lookup_code_start_reason_name(uint32_t reason) {
  switch (reason) {
  case M68K_FACT_CODE_START_REASON_SECTION_ENTRY:
    return "section_entry";
  case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_OFFSET:
    return "policy_entry_offset";
  case M68K_FACT_CODE_START_REASON_POLICY_ENTRY_POINT:
    return "policy_entry_point";
  case M68K_FACT_CODE_START_REASON_CONTROL_TARGET:
    return "control_target";
  case M68K_FACT_CODE_START_REASON_FALLTHROUGH:
    return "fallthrough";
  case M68K_FACT_CODE_START_REASON_INLINE_RESUME:
    return "inline_resume";
  case M68K_FACT_CODE_START_REASON_RUNTIME_VIEW_ENTRY:
    return "runtime_view_entry";
  case M68K_FACT_CODE_START_REASON_LINKAGE_API_ENTRY:
    return "linkage_api_entry";
  case M68K_FACT_CODE_START_REASON_PLATFORM_LOADSEG_ENTRY:
    return "platform_loadseg_entry";
  case M68K_FACT_CODE_START_REASON_STACK_CONTINUATION:
    return "stack_continuation";
  case M68K_FACT_CODE_START_REASON_BOUNDARY_API_ENTRY:
    return "boundary_api_entry";
  default:
    return "unknown";
  }
}

static int append_render_lookup_violations_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL) return 0;
  for (index = 0U; index < lookup->violation_ref_count; ++index) {
    const M68kFact *fact = lookup->violation_refs[index].fact;
    uint8_t kind;
    char message[192];
    if (fact == NULL || fact->section_index != section_analysis->section_index) continue;
    if (fact->target_section_index == fact->section_index && fact->target_offset == fact->offset) {
      kind = M68K_VIOLATION_DECODE_FAILED_REACHABLE;
      snprintf(message, sizeof(message),
        "%s code candidate at $%04X rejected after source $%04X; emitted as data",
        render_lookup_code_start_reason_name(fact->reason), (unsigned)fact->offset,
        (unsigned)fact->source_offset);
    } else {
      kind = M68K_VIOLATION_INVALID_INTERIOR_REFERENCE;
      snprintf(message, sizeof(message),
        "code/data boundary conflict at $%04X references $%04X; emitted as data",
        (unsigned)fact->offset, (unsigned)fact->target_offset);
    }
    if (m68k_ir_section_analysis_add_violation(section_analysis, fact->offset, kind, message) != 0) return -1;
  }
  return 0;
}

static int asm_candidate_operand_absolute_value(const M68kDecodeCandidate *candidate, size_t operand_index,
    uint32_t *out_value) {
  const M68kAsmOperandValue *operand;
  uint8_t kind;
  if (out_value != NULL) *out_value = 0U;
  if (candidate == NULL || operand_index >= candidate->operand_count || out_value == NULL) return 0;
  operand = &candidate->operands[operand_index];
  kind = candidate->operand_kinds[operand_index];
  if (kind == M68K_ASM_OPERAND_ABSL ||
      (operand->kind == M68K_ASM_OPERAND_EA && operand->ea_mode == 7U &&
        (operand->ea_reg == 0U || operand->ea_reg == 1U))) {
    *out_value = operand->value;
    return 1;
  }
  return 0;
}

static uint32_t runtime_address_ref_data_class_flags(const M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    const M68kFact *fact) {
  const M68kDecodeSectionIR *section;
  const M68kDecodeCandidate *candidate;
  uint32_t sink_address = 0U;
  if (lookup == NULL || lookup->object == NULL || decode == NULL || fact == NULL ||
      fact->kind != M68K_FACT_RUNTIME_ADDRESS_REF || fact->section_index >= decode->section_count) {
    return 0U;
  }
  if (fact->has_sink_address && fact->sink_address != 0U) {
    return platform_facts_v2_runtime_address_sink_data_class_flags(lookup->object->platform_backend_kind,
      fact->sink_address);
  }
  if (fact->source_section_index < lookup->object->section_count) {
    const M68kSection *source_section = &lookup->object->sections[fact->source_section_index];
    uint32_t flags = platform_facts_v2_runtime_address_storage_sink_data_class_flags(
      lookup->object->platform_backend_kind, source_section->data, source_section->data_size, fact->source_offset);
    if (flags != 0U) return flags;
  }
  section = &decode->sections[fact->section_index];
  candidate = find_candidate_at_offset_local(section, fact->offset);
  if (candidate == NULL ||
      (fact->reason != UINT32_MAX && fact->reason >= candidate->operand_count)) {
    return 0U;
  }
  if (!((fact->reason == 0U || fact->reason == UINT32_MAX) &&
        candidate->mnemonic_id == M68K_ASM_MNEMONIC_MOVE &&
        candidate->size_suffix == 'l' && candidate->operand_count == 2U)) {
    return 0U;
  }
  if (!asm_candidate_operand_absolute_value(candidate, 1U, &sink_address)) return 0U;
  return platform_facts_v2_runtime_address_sink_data_class_flags(lookup->object->platform_backend_kind, sink_address);
}

static int operand_is_address_postincrement_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_EA ||
      operand->value.ea_mode != 3U || operand->value.ea_reg >= 8U) {
    return 0;
  }
  if (out_reg != NULL) *out_reg = operand->value.ea_reg;
  return 1;
}

static const M68kDecodeCandidate *next_accepted_candidate_local(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, const M68kDecodeCandidate *candidate) {
  uint32_t next_offset;
  if (section == NULL || accepted_start == NULL || candidate == NULL || candidate->byte_count == 0U) return NULL;
  next_offset = candidate->offset + candidate->byte_count;
  if (!accepted_start_at(section, accepted_start, next_offset)) return NULL;
  return find_candidate_at_offset_local(section, next_offset);
}

static const M68kDecodeCandidate *next_decoded_fallthrough_candidate_local(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate) {
  uint32_t next_offset;
  if (section == NULL || candidate == NULL || candidate->byte_count == 0U) return NULL;
  next_offset = candidate->offset + candidate->byte_count;
  if (next_offset >= section->size) return NULL;
  return find_candidate_at_offset_local(section, next_offset);
}

static int bootblock_runtime_copy_source_is_from_disk_read(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t source_addr, uint32_t byte_length) {
  size_t index;
  if (lookup == NULL || byte_length == 0U || source_addr > UINT32_MAX - byte_length) return 0;
  for (index = 0U; index < lookup->bootblock_disk_read_count; ++index) {
    const M68kRenderBootblockDiskRead *read = &lookup->bootblock_disk_reads[index];
    if (read->section_index != section_index || read->byte_length == 0U ||
        read->destination_addr > UINT32_MAX - read->byte_length) {
      continue;
    }
    if (source_addr >= read->destination_addr &&
        source_addr + byte_length <= read->destination_addr + read->byte_length) {
      return 1;
    }
  }
  return 0;
}

static int instruction_is_lea_absolute_to_address_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, uint32_t *out_absolute, uint8_t *out_reg) {
  uint8_t dest_reg = 0U;
  if (out_absolute != NULL) *out_absolute = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (candidate == NULL || instruction == NULL || out_absolute == NULL || out_reg == NULL ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA || instruction->operand_count != 2U ||
      !asm_candidate_operand_absolute_value(candidate, 0U, out_absolute) ||
      !operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
    return 0;
  }
  *out_reg = dest_reg;
  return 1;
}

static int instruction_is_postincrement_runtime_copy(const M68kInstructionIR *instruction, uint8_t source_reg,
    uint8_t dest_reg, uint32_t *out_item_size) {
  uint8_t operand_source_reg = 0U, operand_dest_reg = 0U;
  if (out_item_size != NULL) *out_item_size = 0U;
  if (instruction == NULL || out_item_size == NULL ||
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || instruction->operand_count != 2U ||
      !operand_is_address_postincrement_local(&instruction->operands[0], &operand_source_reg) ||
      !operand_is_address_postincrement_local(&instruction->operands[1], &operand_dest_reg) ||
      operand_source_reg != source_reg || operand_dest_reg != dest_reg) {
    return 0;
  }
  if (instruction->size_suffix == 'b') *out_item_size = 1U;
  else if (instruction->size_suffix == 'w') *out_item_size = 2U;
  else if (instruction->size_suffix == 'l') *out_item_size = 4U;
  return *out_item_size != 0U;
}

static int instruction_is_dbf_to_loop(const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint8_t count_reg, uint32_t loop_offset) {
  M68kInstructionIR instruction;
  size_t target_index;
  uint8_t dbf_reg = 0U;
  if (section == NULL || candidate == NULL ||
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_DBF ||
      m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
      instruction.operand_count < 2U ||
      !operand_is_data_register_local(&instruction.operands[0], &dbf_reg) ||
      dbf_reg != count_reg) {
    return 0;
  }
  (void)lookup;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->has_section && target->section_index == section->section_index &&
        target->offset == loop_offset) {
      return 1;
    }
  }
  return 0;
}

static int bootblock_runtime_copy_handoff_after_loop(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *dbf_candidate, uint32_t destination_addr, uint32_t byte_length,
    uint32_t *out_handoff_addr) {
  const M68kDecodeCandidate *candidate;
  unsigned scan_count = 0U;
  if (out_handoff_addr != NULL) *out_handoff_addr = 0U;
  if (section == NULL || accepted_start == NULL || dbf_candidate == NULL || out_handoff_addr == NULL ||
      byte_length == 0U || destination_addr > UINT32_MAX - byte_length) {
    return 0;
  }
  (void)accepted_start;
  candidate = next_decoded_fallthrough_candidate_local(section, dbf_candidate);
  while (candidate != NULL && scan_count < 12U) {
    M68kInstructionIR instruction;
    uint32_t handoff_addr = 0U;
    int decoded = m68k_decode_candidate_to_instruction(candidate, &instruction) == 0;
    if (decoded && instruction_has_call_or_jump_flow_local(&instruction)) {
      int has_absolute_handoff =
        asm_candidate_operand_absolute_value(candidate, 0U, &handoff_addr);
      if (!has_absolute_handoff && instruction.operand_count == 1U) {
        has_absolute_handoff = operand_absolute_offset_local(&instruction.operands[0], &handoff_addr);
      }
      if (has_absolute_handoff &&
          handoff_addr >= destination_addr && handoff_addr < destination_addr + byte_length) {
        *out_handoff_addr = handoff_addr;
        return 1;
      }
    }
    if (decoded && instruction_has_terminal_state_flow_local(&instruction)) {
      return 0;
    }
    candidate = next_decoded_fallthrough_candidate_local(section, candidate);
    ++scan_count;
  }
  return 0;
}

static int render_lookup_infer_bootblock_runtime_copies(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
      lookup->bootblock_disk_read_count == 0U) {
    return 0;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    size_t candidate_index;
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *count_candidate = &section->candidates[candidate_index];
      const M68kDecodeCandidate *source_lea_candidate;
      const M68kDecodeCandidate *dest_lea_candidate;
      const M68kDecodeCandidate *copy_candidate;
      const M68kDecodeCandidate *dbf_candidate;
      M68kInstructionIR count_instruction, source_lea_instruction, dest_lea_instruction, copy_instruction;
      uint32_t count_value = 0U, source_addr = 0U, destination_addr = 0U, item_size = 0U, byte_length = 0U;
      uint32_t handoff_addr = 0U;
      uint8_t count_reg = 0U, source_reg = 0U, dest_reg = 0U;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], count_candidate) ||
          m68k_decode_candidate_to_instruction(count_candidate, &count_instruction) != 0 ||
          count_instruction.mnemonic_id != M68K_ASM_MNEMONIC_MOVE ||
          count_instruction.size_suffix != 'w' || count_instruction.operand_count != 2U ||
          !m68k_ir_operand_immediate_value(&count_instruction.operands[0], &count_value) ||
          !operand_is_data_register_local(&count_instruction.operands[1], &count_reg)) {
        continue;
      }
      source_lea_candidate = next_accepted_candidate_local(section, accepted_start[section_index], count_candidate);
      dest_lea_candidate = next_accepted_candidate_local(section, accepted_start[section_index], source_lea_candidate);
      copy_candidate = next_accepted_candidate_local(section, accepted_start[section_index], dest_lea_candidate);
      dbf_candidate = next_accepted_candidate_local(section, accepted_start[section_index], copy_candidate);
      if (source_lea_candidate == NULL || dest_lea_candidate == NULL || copy_candidate == NULL ||
          dbf_candidate == NULL ||
          m68k_decode_candidate_to_instruction(source_lea_candidate, &source_lea_instruction) != 0 ||
          m68k_decode_candidate_to_instruction(dest_lea_candidate, &dest_lea_instruction) != 0 ||
          m68k_decode_candidate_to_instruction(copy_candidate, &copy_instruction) != 0 ||
          !instruction_is_lea_absolute_to_address_reg(source_lea_candidate, &source_lea_instruction, &source_addr,
            &source_reg) ||
          !instruction_is_lea_absolute_to_address_reg(dest_lea_candidate, &dest_lea_instruction, &destination_addr,
            &dest_reg) ||
          !instruction_is_postincrement_runtime_copy(&copy_instruction, source_reg, dest_reg, &item_size) ||
          count_value > (UINT32_MAX / item_size) - 1U) {
        continue;
      }
      byte_length = (count_value + 1U) * item_size;
      if (!instruction_is_dbf_to_loop(lookup, section, dbf_candidate, count_reg, copy_candidate->offset)) {
        continue;
      }
      if (!bootblock_runtime_copy_source_is_from_disk_read(lookup, section->section_index, source_addr, byte_length)) {
        continue;
      }
      if (!bootblock_runtime_copy_handoff_after_loop(section, accepted_start[section_index], dbf_candidate,
            destination_addr, byte_length, &handoff_addr)) {
        continue;
      }
      if (render_lookup_add_bootblock_runtime_copy(lookup, section->section_index, count_candidate->offset,
          source_addr, destination_addr, byte_length, handoff_addr) != 0) {
        return -1;
      }
    }
  }
  return 0;
}


static int candidate_first_local_control_target(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, uint32_t *out_target_offset) {
  size_t target_index;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (section == NULL || candidate == NULL || out_target_offset == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if ((target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_JUMP) &&
        target->has_section && target->section_index == section->section_index && target->offset < section->size) {
      *out_target_offset = target->offset;
      return 1;
    }
  }
  return 0;
}


static int accepted_range_has_code_byte(const uint8_t *accepted_bytes, uint32_t section_size,
    uint32_t offset, uint32_t size) {
  uint32_t cursor;
  if (accepted_bytes == NULL || offset > section_size || size > section_size - offset) return 1;
  for (cursor = 0U; cursor < size; ++cursor) {
    if (accepted_bytes[offset + cursor] != 0U) return 1;
  }
  return 0;
}

static int render_lookup_mark_label(M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  if (lookup == NULL || section_index >= lookup->section_count || lookup->labels == NULL ||
      lookup->label_extents == NULL || lookup->labels[section_index] == NULL ||
      offset > lookup->label_extents[section_index]) {
    return 0;
  }
  lookup->labels[section_index][offset] = 1U;
  render_lookup_mark_boundary_flag(lookup, section_index, offset, M68K_RENDER_BOUNDARY_LABEL);
  return 1;
}

static int render_lookup_pointer_value_to_source_offset(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t value, uint32_t *out_source_offset) {
  size_t index;
  uint32_t logical_address = 0U;
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (lookup == NULL || section == NULL || out_source_offset == NULL || value == 0U) return 0;
  if (lookup->runtime_address_ranges != NULL) {
    for (index = 0U; index < lookup->runtime_address_range_count; ++index) {
      const M68kFact *range = lookup->runtime_address_ranges[index].fact;
      uint32_t delta;
      uint32_t source_offset;
      if (range == NULL || range->section_index != section->section_index || !range->has_runtime_address ||
          value < range->runtime_address) {
        continue;
      }
      delta = value - range->runtime_address;
      if (delta >= range->size || range->offset > UINT32_MAX - delta) continue;
      source_offset = range->offset + delta;
      if (source_offset >= section->size) continue;
      if (!lookup_source_has_materialized_runtime_address(lookup, section->section_index, source_offset, value))
        continue;
      if (!lookup_source_logical_address(lookup, section->section_index, source_offset, &logical_address) ||
          logical_address != value) {
        continue;
      }
      *out_source_offset = source_offset;
      return 1;
    }
  }
  if (value < section->size &&
      lookup_source_logical_address(lookup, section->section_index, value, &logical_address) &&
      logical_address == value) {
    *out_source_offset = value;
    return 1;
  }
  return 0;
}

static int render_lookup_pointer_value_to_source_location(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint32_t value, size_t *out_section_index, uint32_t *out_source_offset) {
  size_t section_index;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (lookup == NULL || decode == NULL || out_section_index == NULL || out_source_offset == NULL) return 0;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    if (render_lookup_pointer_value_to_source_offset(lookup, &decode->sections[section_index], value,
        out_source_offset)) {
      *out_section_index = section_index;
      return 1;
    }
  }
  return 0;
}

static int render_lookup_pointer_table_target_can_take_auto_label(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const uint8_t *accepted_bytes,
    uint32_t offset) {
  if (lookup == NULL || section == NULL || offset >= section->size) return 0;
  if (accepted_range_has_code_byte(accepted_bytes, section->size, offset, 1U) &&
      (accepted_start == NULL || accepted_start[offset] == 0U)) {
    return 0;
  }
  if (lookup_offset_is_inside_relocation_payload(lookup, section->section_index, offset)) return 0;
  return 1;
}

static int render_lookup_pointer_value_to_object_source_location(const M68kRenderLookup *lookup, uint32_t value,
    size_t *out_section_index, uint32_t *out_source_offset) {
  size_t section_index;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (lookup == NULL || lookup->object == NULL || out_section_index == NULL || out_source_offset == NULL) return 0;
  for (section_index = 0U; section_index < lookup->object->section_count; ++section_index) {
    const M68kSection *object_section = &lookup->object->sections[section_index];
    size_t range_index;
    uint32_t logical_address = 0U;
    if (object_section->data == NULL || value == 0U) continue;
    for (range_index = 0U; range_index < lookup->runtime_address_range_count; ++range_index) {
      const M68kFact *range = lookup->runtime_address_ranges[range_index].fact;
      uint32_t delta;
      uint32_t source_offset;
      if (range == NULL || range->section_index != section_index || !range->has_runtime_address ||
          value < range->runtime_address) continue;
      delta = value - range->runtime_address;
      if (delta >= range->size || range->offset > UINT32_MAX - delta) continue;
      source_offset = range->offset + delta;
      if (source_offset >= object_section->size ||
          !lookup_source_has_materialized_runtime_address(lookup, section_index, source_offset, value) ||
          !lookup_source_logical_address(lookup, section_index, source_offset, &logical_address) ||
          logical_address != value) continue;
      *out_section_index = section_index;
      *out_source_offset = source_offset;
      return 1;
    }
    if (value < object_section->size &&
        lookup_source_logical_address(lookup, section_index, value, &logical_address) && logical_address == value) {
      *out_section_index = section_index;
      *out_source_offset = value;
      return 1;
    }
  }
  return 0;
}

static int typed_flow_build_predecessors(M68kRenderTypedFlowGraph *graph, Arena *arena) {
  size_t *counts = NULL;
  size_t *cursor = NULL;
  size_t node_index;
  ArenaMark mark;
  if (graph == NULL || arena == NULL) return -1;
  if (graph->node_count == 0U) return 0;
  mark = arena_mark(arena);
  counts = (size_t *)arena_calloc(arena, graph->node_count, sizeof(*counts));
  cursor = (size_t *)arena_alloc(arena, graph->node_count * sizeof(*cursor));
  if (counts == NULL || cursor == NULL) goto fail;
  for (node_index = 0U; node_index < graph->node_count; ++node_index) {
    uint8_t successor_index;
    for (successor_index = 0U; successor_index < graph->nodes[node_index].successor_count; ++successor_index) {
      size_t successor = graph->nodes[node_index].successors[successor_index];
      if (successor < graph->node_count) ++counts[successor];
    }
  }
  graph->predecessor_offsets = (size_t *)arena_alloc(arena, (graph->node_count + 1U) *
    sizeof(*graph->predecessor_offsets));
  if (graph->predecessor_offsets == NULL) goto fail;
  graph->predecessor_offsets[0] = 0U;
  for (node_index = 0U; node_index < graph->node_count; ++node_index) {
    if (counts[node_index] > SIZE_MAX - graph->predecessor_offsets[node_index]) goto fail;
    graph->predecessor_offsets[node_index + 1U] = graph->predecessor_offsets[node_index] + counts[node_index];
    cursor[node_index] = graph->predecessor_offsets[node_index];
  }
  graph->predecessor_count = graph->predecessor_offsets[graph->node_count];
  graph->predecessors = (size_t *)arena_alloc(arena, (graph->predecessor_count != 0U ? graph->predecessor_count : 1U) *
    sizeof(*graph->predecessors));
  if (graph->predecessors == NULL) goto fail;
  for (node_index = 0U; node_index < graph->node_count; ++node_index) {
    uint8_t successor_index;
    for (successor_index = 0U; successor_index < graph->nodes[node_index].successor_count; ++successor_index) {
      size_t successor = graph->nodes[node_index].successors[successor_index];
      if (successor < graph->node_count) graph->predecessors[cursor[successor]++] = node_index;
    }
  }
  return 0;
fail:
  arena_rewind(arena, mark);
  return -1;
}

static void typed_state_apply_function_summary_effects(M68kRenderTypedState *state,
    const M68kAnalysisFunctionSummary *summary) {
  M68kRenderTypedState old_state;
  M68kRenderTypedStackSlot preserved_stack_slots[M68K_RENDER_TYPED_STACK_SLOT_LIMIT];
  size_t preserved_stack_slot_count = 0U;
  uint8_t reg;
  int complete_partition = 1;
  if (state == NULL) return;
  old_state = *state;
  for (reg = 0U; reg < old_state.stack_slot_count; ++reg) {
    if (old_state.stack_slots[reg].known != 0U && old_state.stack_slots[reg].caller_save_temporary != 0U)
      preserved_stack_slots[preserved_stack_slot_count++] = old_state.stack_slots[reg];
  }
  if (summary != NULL && summary->effects_invalid == 0U &&
      summary->register_effect_state == M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT) {
    for (reg = 0U; reg < 8U; ++reg) {
      uint8_t data_effect = function_summary_register_effect(summary, M68K_ANALYSIS_REGISTER_DATA, reg);
      uint8_t address_effect = function_summary_register_effect(summary, M68K_ANALYSIS_REGISTER_ADDRESS, reg);
      if ((data_effect != M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED &&
           data_effect != M68K_FUNCTION_SUMMARY_LOCATION_CLOBBERED) ||
          (address_effect != M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED &&
           address_effect != M68K_FUNCTION_SUMMARY_LOCATION_CLOBBERED)) {
        complete_partition = 0;
        break;
      }
    }
  }
  if (summary == NULL || summary->effects_invalid != 0U ||
      summary->register_effect_state != M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT ||
      !complete_partition) {
    typed_state_clear_all(state);
    for (reg = 0U; reg < preserved_stack_slot_count; ++reg) state->stack_slots[reg] = preserved_stack_slots[reg];
    state->stack_slot_count = preserved_stack_slot_count;
    return;
  }
  for (reg = 0U; reg < 8U; ++reg) {
    if (function_summary_register_effect(summary, M68K_ANALYSIS_REGISTER_DATA, reg) !=
        M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED)
      typed_state_clear_reg(state, M68K_ANALYSIS_REGISTER_DATA, reg);
    if (function_summary_register_effect(summary, M68K_ANALYSIS_REGISTER_ADDRESS, reg) !=
        M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED)
      typed_state_clear_reg(state, M68K_ANALYSIS_REGISTER_ADDRESS, reg);
  }
  /* Register location entries do not clobber the caller's private saves.
   * Positive stack-write/escape facts can alias those physical bytes even
   * under a different ABI role. Subjects lack a byte extent, so conservatively
   * drop all private saves rather than assert an unproved disjoint range. */
  {
    int private_stack_write = 0;
    for (size_t i = 0U; i < summary->memory_effect_count; ++i)
      if (summary->memory_effects[i].kind == M68K_FUNCTION_SUMMARY_MEMORY_WRITE &&
          summary->memory_effects[i].subject.kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STACK)
        private_stack_write = 1;
    for (size_t i = 0U; i < summary->escape_count; ++i)
      if (summary->escapes[i].sink_subject.kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STACK)
        private_stack_write = 1;
    for (size_t i = 0U; i < summary->location_effect_count; ++i)
      if (summary->location_effects[i].location.kind == M68K_FUNCTION_SUMMARY_ABI_LOCATION_STACK &&
          summary->location_effects[i].effect == M68K_FUNCTION_SUMMARY_LOCATION_CLOBBERED)
        private_stack_write = 1;
    if (private_stack_write) for (size_t i = 0U; i < state->stack_slot_count;) {
      if (state->stack_slots[i].caller_save_temporary)
        state->stack_slots[i] = state->stack_slots[--state->stack_slot_count];
      else ++i;
    }
  }
  if (summary->memory_effect_state != M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT ||
      summary->escape_effect_state != M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT) {
    typed_state_invalidate_opaque_memory_effects(state);
    return;
  }
  for (reg = 0U; reg < summary->memory_effect_count; ++reg) {
    uint8_t kind = summary->memory_effects[reg].kind;
    if (kind == M68K_FUNCTION_SUMMARY_MEMORY_WRITE) {
      const M68kFunctionSummaryEffectSubjectIR *subject = &summary->memory_effects[reg].subject;
      if (subject->kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STATIC_STORAGE) {
        typed_state_invalidate_static_storage_subject(state, subject);
      } else if (subject->kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_INPUT &&
          subject->input_index < summary->input_count) {
        typed_state_invalidate_input_subject(state, summary, subject->input_index);
      } else if (subject->kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STACK) {
        typed_state_invalidate_stack_subject(state, subject);
      } else {
        /* Abstract regions still lack a stable caller-side storage identity. */
        typed_state_clear_all(state);
        return;
      }
    }
    /* `nonaliasing_write` is already the precise negative alias proof: it
     * cannot affect any caller-visible typed storage identity.  Treating it
     * like an opaque write would discard a declared effect fact rather than
     * applying it. */
  }
  for (reg = 0U; reg < summary->escape_count; ++reg) {
    const M68kFunctionSummaryEffectSubjectIR *sink = &summary->escapes[reg].sink_subject;
    if (sink->kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STATIC_STORAGE) {
      typed_state_invalidate_static_storage_subject(state, sink);
    } else if (sink->kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_INPUT &&
        sink->input_index < summary->input_count) {
      typed_state_invalidate_input_subject(state, summary, sink->input_index);
    } else if (sink->kind == M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_STACK) {
      typed_state_invalidate_stack_subject(state, sink);
    } else {
      /* An abstract escape sink has no caller-side identity in the typed
       * state, so retaining any cache would manufacture a non-alias proof. */
      typed_state_clear_all(state);
      return;
    }
  }
  if (summary->location_effect_count == 0U) {
    typed_state_clear_non_caller_save_stack_slots(state);
  } else {
    for (reg = 0U; reg < state->stack_slot_count;) {
      M68kRenderTypedStackSlot *slot = &state->stack_slots[reg];
      uint8_t effect = slot->caller_save_temporary ? M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED :
        M68K_FUNCTION_SUMMARY_LOCATION_CLOBBERED;
      uint8_t effect_index;
      for (effect_index = 0U; effect_index < summary->location_effect_count; ++effect_index) {
        const M68kFunctionSummaryLocationEffectIR *location_effect = &summary->location_effects[effect_index];
        if (location_effect->location.kind != M68K_FUNCTION_SUMMARY_ABI_LOCATION_STACK ||
            location_effect->location.stack_offset != slot->displacement ||
            location_effect->location.stack_convention != slot->abi_stack_convention ||
            location_effect->location.width != 4U) continue;
        effect = location_effect->effect;
        break;
      }
      if (effect == M68K_FUNCTION_SUMMARY_LOCATION_PRESERVED) {
        ++reg;
      } else {
        state->stack_slots[reg] = state->stack_slots[state->stack_slot_count - 1U];
        state->stack_slot_count -= 1U;
      }
    }
  }
}

static void render_lookup_materialize_typed_address_target(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, uint8_t **accepted_bytes,
    size_t source_section_index, uint32_t source_value, const M68kRenderTypedProvenance *provenance,
    uint8_t *resolution, uint8_t *has_target, size_t *target_section_index_out, uint32_t *target_offset_out,
    uint8_t candidate_target_count, uint32_t *candidate_source_values,
    size_t *candidate_target_section_indices, uint32_t *candidate_target_offsets) {
  const M68kDecodeSectionIR *section;
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  if (lookup == NULL || decode == NULL || accepted_bytes == NULL || resolution == NULL ||
      has_target == NULL || target_section_index_out == NULL || target_offset_out == NULL) return;
  if (*resolution == M68K_ADDRESS_VALUE_RESOLUTION_UNKNOWN_TARGET ||
      *resolution == M68K_ADDRESS_VALUE_RESOLUTION_AMBIGUOUS_TARGET) {
    *has_target = 0U; *target_section_index_out = 0U; *target_offset_out = 0U;
    for (uint8_t i = 0U; i < candidate_target_count; ++i) {
      candidate_target_section_indices[i] = SIZE_MAX; candidate_target_offsets[i] = 0U;
    }
  }
  if (*resolution == M68K_ADDRESS_VALUE_RESOLUTION_AMBIGUOUS_TARGET && candidate_target_count > 1U) {
    uint8_t candidate_index;
    int outside = 0, invalid = 0;
    for (candidate_index = 0U; candidate_index < candidate_target_count; ++candidate_index) {
      if (!render_lookup_pointer_value_to_source_location(lookup, decode, candidate_source_values[candidate_index],
          &target_section_index, &target_offset)) {
        outside = 1; continue;
      }
      section = &decode->sections[target_section_index];
      if (!render_lookup_pointer_table_target_can_take_auto_label(lookup, section,
          accepted_start != NULL ? accepted_start[target_section_index] : NULL,
          accepted_bytes[target_section_index], target_offset)) {
        invalid = 1; continue;
      }
      candidate_target_section_indices[candidate_index] = target_section_index;
      candidate_target_offsets[candidate_index] = target_offset;
    }
    *resolution = outside ? M68K_ADDRESS_VALUE_RESOLUTION_OUTSIDE_KNOWN_ADDRESS_SPACE :
      invalid ? M68K_ADDRESS_VALUE_RESOLUTION_INVALID_TARGET : M68K_ADDRESS_VALUE_RESOLUTION_FINITE_CANDIDATE_TARGETS;
    return;
  }
  if (*resolution != M68K_ADDRESS_VALUE_RESOLUTION_UNKNOWN_TARGET || candidate_target_count == 0U ||
      source_section_index >= decode->section_count) return;
  if (!render_lookup_pointer_value_to_source_location(lookup, decode, source_value,
      &target_section_index, &target_offset)) {
    *resolution = M68K_ADDRESS_VALUE_RESOLUTION_OUTSIDE_KNOWN_ADDRESS_SPACE;
    return;
  }
  section = &decode->sections[target_section_index];
  if (!render_lookup_pointer_table_target_can_take_auto_label(lookup, section,
      accepted_start != NULL ? accepted_start[target_section_index] : NULL,
      accepted_bytes[target_section_index], target_offset)) {
    *resolution = M68K_ADDRESS_VALUE_RESOLUTION_INVALID_TARGET;
    return;
  }
  *has_target = 1U;
  *target_section_index_out = target_section_index;
  *target_offset_out = target_offset;
  candidate_target_section_indices[0] = target_section_index;
  candidate_target_offsets[0] = target_offset;
  *resolution = M68K_ADDRESS_VALUE_RESOLUTION_RESOLVED;
  if (provenance != NULL && provenance->kind == M68K_PLATFORM_TYPE_PROVENANCE_IMMEDIATE) {
    const M68kAnalysisManualRepresentation *representation = lookup_manual_operand_representation(lookup,
      provenance->section_index, provenance->offset, provenance->producer_operand_index);
    /* Keep the resolved analysis target, but a value EQU does not require a
     * source declaration inside the target's data owner. */
    if (representation == NULL || representation->style_id != M68K_ANALYSIS_REPRESENTATION_STYLE_SYMBOL ||
        representation->target_equate_index == 0U) {
      render_lookup_mark_label(lookup, target_section_index, target_offset);
      render_lookup_mark_label_target_ref(lookup, target_section_index, target_offset);
      render_lookup_mark_label_statement_ref(lookup, target_section_index, target_offset);
    }
  }
}

int m68k_analysis_render_lookup_materialize_typed_address_targets(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, uint8_t **accepted_bytes) {
  size_t index;
  if (lookup == NULL || decode == NULL || accepted_bytes == NULL) return -1;
  for (index = 0U; index < lookup->address_value_consumer_count; ++index) {
    M68kRenderTypedAddressConsumer *consumer = &lookup->address_value_consumers[index];
    render_lookup_materialize_typed_address_target(lookup, decode, accepted_start, accepted_bytes,
      consumer->section_index, consumer->source_value, &consumer->provenance, &consumer->resolution,
      &consumer->has_target, &consumer->target_section_index, &consumer->target_offset,
      consumer->candidate_target_count, consumer->candidate_source_values,
      consumer->candidate_target_section_indices, consumer->candidate_target_offsets);
  }
  return 0;
}


static uint16_t trace_base_id_from_name(const char *name) {
  uint16_t base_id = AMIGA_OS_BASE_ID_NONE;
  const char *library_name;
  if (name == NULL || name[0] == '\0') return AMIGA_OS_BASE_ID_NONE;
  if (platform_facts_v2_library_base_id_for_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, name, &base_id)) return base_id;
  library_name = platform_facts_v2_library_name_from_base_symbol_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, name);
  if (library_name == NULL || library_name[0] == '\0') return AMIGA_OS_BASE_ID_NONE;
  return platform_facts_v2_library_base_id_for_name(M68K_PLATFORM_BACKEND_AMIGA_HUNK, library_name, &base_id) ?
    base_id : AMIGA_OS_BASE_ID_NONE;
}

static void trace_reg_set(M68kRenderTraceRegName *reg, const char *name) {
  if (reg == NULL || name == NULL || name[0] == '\0') return;
  reg->known = 1U;
  reg->base_id = trace_base_id_from_name(name);
  snprintf(reg->name, sizeof(reg->name), "%s", name);
}

static void trace_reg_clear(M68kRenderTraceRegName *reg) {
  if (reg == NULL) return;
  reg->known = 0U;
  reg->base_id = AMIGA_OS_BASE_ID_NONE;
  reg->name[0] = '\0';
}

static void trace_target_clear(M68kRenderTraceTarget *target) {
  if (target == NULL) return;
  target->known = 0U;
  target->section_index = 0U;
  target->offset = 0U;
}

static void trace_target_set(M68kRenderTraceTarget *target, size_t section_index, uint32_t offset) {
  if (target == NULL) return;
  target->known = 1U;
  target->section_index = section_index;
  target->offset = offset;
}

static void trace_addr_reg_set_name(M68kRenderBaseTraceState *state, uint8_t reg, const char *name) {
  if (state == NULL || reg >= 8U) return;
  trace_reg_set(&state->addr_regs[reg], name);
  trace_target_clear(&state->addr_targets[reg]);
  state->app_addresses[reg].known = 0U;
  state->app_addresses[reg].displacement = 0;
}

static void trace_addr_reg_clear(M68kRenderBaseTraceState *state, uint8_t reg) {
  if (state == NULL || reg >= 8U) return;
  trace_reg_clear(&state->addr_regs[reg]);
  trace_target_clear(&state->addr_targets[reg]);
  state->app_addresses[reg].known = 0U;
  state->app_addresses[reg].displacement = 0;
}

static void trace_addr_reg_set_app_address(M68kRenderBaseTraceState *state, uint8_t reg, int16_t displacement) {
  if (state == NULL || reg >= 8U) return;
  trace_reg_clear(&state->addr_regs[reg]);
  trace_target_clear(&state->addr_targets[reg]);
  state->app_addresses[reg].known = 1U;
  state->app_addresses[reg].displacement = displacement;
}

static void trace_addr_reg_set_target(M68kRenderBaseTraceState *state, uint8_t reg, size_t section_index,
    uint32_t offset) {
  if (state == NULL || reg >= 8U) return;
  trace_reg_clear(&state->addr_regs[reg]);
  trace_target_set(&state->addr_targets[reg], section_index, offset);
  state->app_addresses[reg].known = 0U;
  state->app_addresses[reg].displacement = 0;
}

static void trace_state_reset(M68kRenderBaseTraceState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static void trace_stack_clear(M68kRenderBaseTraceState *state) {
  if (state == NULL) return;
  state->stack_value_count = 0U;
}

static void trace_stack_push_unknown(M68kRenderBaseTraceState *state) {
  M68kRenderTraceStackValue unknown;
  if (state == NULL) return;
  memset(&unknown, 0, sizeof(unknown));
  if (state->stack_value_count >= sizeof(state->stack_values) / sizeof(state->stack_values[0])) {
    memmove(&state->stack_values[1], &state->stack_values[0],
      (sizeof(state->stack_values) / sizeof(state->stack_values[0]) - 1U) * sizeof(state->stack_values[0]));
    state->stack_values[0] = unknown;
    return;
  }
  if (state->stack_value_count != 0U) {
    memmove(&state->stack_values[1], &state->stack_values[0],
      state->stack_value_count * sizeof(state->stack_values[0]));
  }
  state->stack_values[0] = unknown;
  ++state->stack_value_count;
}

static void trace_stack_push_library(M68kRenderBaseTraceState *state, const char *library_name) {
  if (state == NULL || library_name == NULL || library_name[0] == '\0') return;
  trace_stack_push_unknown(state);
  state->stack_values[0].has_library_name = 1U;
  snprintf(state->stack_values[0].library_name, sizeof(state->stack_values[0].library_name), "%s", library_name);
}

static const char *trace_stack_top_library(const M68kRenderBaseTraceState *state) {
  if (state == NULL || state->stack_value_count == 0U || !state->stack_values[0].has_library_name) return NULL;
  return state->stack_values[0].library_name;
}

static void trace_state_apply_policy_register_seeds(M68kRenderBaseTraceState *state,
    const M68kAnalysisPolicy *policy, size_t section_index, uint32_t offset) {
  uint16_t index;
  if (state == NULL || policy == NULL) return;
  for (index = 0U; index < policy->register_seed_count && index < M68K_ANALYSIS_REGISTER_SEED_LIMIT; ++index) {
    const M68kAnalysisRegisterSeed *seed = &policy->register_seeds[index];
    if ((seed->kind != M68K_ANALYSIS_REGISTER_SEED_LIBRARY_BASE &&
         seed->kind != M68K_ANALYSIS_REGISTER_SEED_STRUCT_PTR) ||
        seed->reg_index >= 8U || seed->name[0] == '\0')
      continue;
    if (seed->has_section_index && seed->section_index != (uint32_t)section_index) continue;
    if (seed->has_entry_offset) {
      if (seed->entry_offset != offset) continue;
    } else if (!policy->has_entry_offset || section_index != 0U || policy->entry_offset != offset) continue;
    if (seed->reg_kind == M68K_ANALYSIS_REGISTER_DATA) trace_reg_set(&state->data_regs[seed->reg_index], seed->name);
    else if (seed->reg_kind == M68K_ANALYSIS_REGISTER_ADDRESS)
      trace_addr_reg_set_name(state, seed->reg_index, seed->name);
  }
}

int operand_is_data_register_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_DN) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_RN && !operand->value.reg_is_address) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 0U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

int operand_address_register_index_local(const M68kOperandIR *operand, uint8_t *out_reg) {
  if (operand == NULL) return 0;
  if (operand->kind == M68K_ASM_OPERAND_AN) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_RN && operand->value.reg_is_address) {
    if (out_reg != NULL) *out_reg = operand->value.reg;
    return 1;
  }
  if (operand->kind == M68K_ASM_OPERAND_EA && operand->value.ea_mode == 1U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    return 1;
  }
  return 0;
}

int operand_is_address_displacement_local(const M68kOperandIR *operand, uint8_t *out_reg,
    int16_t *out_displacement) {
  if (operand == NULL ||
      (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) ||
      operand->value.ea_mode != 5U || operand->value.ea_reg >= 8U) {
    return 0;
  }
  if (out_reg != NULL) *out_reg = operand->value.ea_reg;
  if (out_displacement != NULL) *out_displacement = (int16_t)(operand->value.value & 0xFFFFU);
  return 1;
}

int operand_is_address_memory_local(const M68kOperandIR *operand, uint8_t *out_reg,
    int16_t *out_displacement) {
  if (operand == NULL ||
      (operand->kind != M68K_ASM_OPERAND_EA && operand->kind != M68K_ASM_OPERAND_BF_EA) ||
      operand->value.ea_reg >= 8U) {
    return 0;
  }
  if (operand->value.ea_mode == 2U) {
    if (out_reg != NULL) *out_reg = operand->value.ea_reg;
    if (out_displacement != NULL) *out_displacement = 0;
    return 1;
  }
  return operand_is_address_displacement_local(operand, out_reg, out_displacement);
}

static const M68kRenderTraceRegName *trace_reg_from_operand(const M68kRenderBaseTraceState *state,
    const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg) && state->data_regs[reg].known) return &state->data_regs[reg];
  if (operand_address_register_index_local(operand, &reg) && state->addr_regs[reg].known)
    return &state->addr_regs[reg];
  return NULL;
}

static const char *trace_name_from_operand(const M68kRenderBaseTraceState *state,
    const M68kOperandIR *operand) {
  const M68kRenderTraceRegName *reg = trace_reg_from_operand(state, operand);
  return reg != NULL ? reg->name : NULL;
}

static const char *trace_library_from_operand(const M68kRenderBaseTraceState *state,
    const M68kOperandIR *operand) {
  const M68kRenderTraceRegName *reg = trace_reg_from_operand(state, operand);
  if (reg == NULL || reg->base_id == AMIGA_OS_BASE_ID_NONE) return NULL;
  return platform_facts_v2_library_name_for_base_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, reg->base_id);
}

static const char *trace_local_slot_library(const M68kRenderBaseTraceState *state, uint8_t base_reg,
    int16_t displacement);

static const char *trace_known_library_from_operand(const M68kRenderLookup *lookup,
    const M68kRenderBaseTraceState *state, const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const char *library_name = trace_library_from_operand(state, operand);
  if (library_name != NULL) return library_name;
  if (lookup == NULL || operand == NULL) return NULL;
  if (operand_is_address_displacement_local(operand, &base_reg, &displacement)) {
    library_name = trace_local_slot_library(state, base_reg, displacement);
    if (library_name != NULL && render_lookup_amiga_library_base_name_for_library_name(library_name) != NULL)
      return library_name;
    if (state != NULL && state->addr_regs[base_reg].known) {
      library_name = lookup_base_field_slot_library(lookup, state->addr_regs[base_reg].name, displacement);
      if (library_name != NULL) return library_name;
    }
    if (state == NULL || !state->addr_regs[base_reg].known) {
      char owner_name[32];
      if (amiga_unknown_base_register_owner_name(base_reg, owner_name, sizeof(owner_name))) {
        library_name = lookup_base_field_slot_library(lookup, owner_name, displacement);
        if (library_name != NULL) return library_name;
      }
    }
    if (base_reg == 6U && (state == NULL || !state->addr_regs[6].known))
      return lookup_app_base_field_slot_library(lookup, displacement);
  }
  return NULL;
}

static int trace_library_name_from_candidate_operand(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, uint32_t operand_index, char *out_name, size_t out_size) {
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  uint32_t absolute_offset = 0U;
  if (out_name != NULL && out_size != 0U) out_name[0] = '\0';
  if (lookup == NULL || section == NULL || candidate == NULL || instruction == NULL ||
      out_name == NULL || out_size == 0U || operand_index >= candidate->operand_count ||
      operand_index >= instruction->operand_count) {
    return 0;
  }
  if (candidate_data_target_for_operand(candidate, operand_index, &target_section_index, &target_offset)) {
    return read_library_name_string_from_object(lookup->object, target_section_index, target_offset,
      out_name, out_size);
  }
  if (candidate_relocated_target_for_operand(lookup, section, candidate, operand_index,
      &target_section_index, &target_offset)) {
    return read_library_name_string_from_object(lookup->object, target_section_index, target_offset,
      out_name, out_size);
  }
  if (operand_absolute_offset_local(&instruction->operands[operand_index], &absolute_offset))
    return read_library_name_string_at(section, absolute_offset, out_name, out_size);
  return 0;
}

static void trace_state_update_register_names_after_candidate(M68kRenderBaseTraceState *state,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  const char *source_name;
  const char *source_library;
  uint8_t dest_reg = 0U;
  uint8_t loaded_reg = 0U;
  uint8_t app_address_reg = 0U;
  int16_t app_address_displacement = 0;
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  char loaded_name[64];
  char pushed_name[64];
  if (state == NULL || candidate == NULL) return;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata != NULL && metadata->operation_type == M68K_SIM_OP_PUSH_EA &&
      metadata->source_operand_index < candidate->operand_count) {
    if (trace_library_name_from_candidate_operand(lookup, section, candidate,
        &instruction, metadata->source_operand_index, pushed_name, sizeof(pushed_name))) {
      trace_stack_push_library(state, pushed_name);
    } else {
      trace_stack_push_unknown(state);
    }
    return;
  }
  if (metadata != NULL && metadata->sp_effect_count != 0U) trace_stack_clear(state);
  if (candidate->operand_count != 2U) return;
  if (candidate->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      operand_address_register_index_local(&instruction.operands[1], &dest_reg)) {
    if (candidate_lea_known_amiga_name_to_address_reg(lookup, section, candidate, &loaded_reg,
        loaded_name, sizeof(loaded_name)) && loaded_reg == dest_reg) {
      trace_addr_reg_set_name(state, dest_reg, loaded_name);
    } else if (candidate_lea_app_base_address_to_address_reg(candidate, &app_address_reg,
        &app_address_displacement) && app_address_reg == dest_reg) {
      return;
    } else if (candidate_data_target_for_operand(candidate, 0U, &target_section_index, &target_offset)) {
      trace_addr_reg_set_target(state, dest_reg, target_section_index, target_offset);
    }
    return;
  }
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVEA) {
    return;
  }
  if (candidate_moves_relocated_immediate_target_to_address_reg(lookup, section, candidate, &instruction,
      &target_section_index, &target_offset, &dest_reg)) {
    trace_addr_reg_set_target(state, dest_reg, target_section_index, target_offset);
    return;
  }
  source_name = trace_name_from_operand(state, &instruction.operands[0]);
  source_library = trace_known_library_from_operand(lookup, state, &instruction.operands[0]);
  if (operand_is_data_register_local(&instruction.operands[1], &dest_reg)) {
    if (source_name != NULL) trace_reg_set(&state->data_regs[dest_reg], source_name);
    else trace_reg_clear(&state->data_regs[dest_reg]);
  } else if (operand_address_register_index_local(&instruction.operands[1], &dest_reg)) {
    if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && source_library != NULL) {
      trace_addr_reg_set_name(state, dest_reg, source_library);
    } else if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEA &&
        operand_is_absolute_address_local(&instruction.operands[0], 4U)) {
      trace_addr_reg_set_name(state, dest_reg, amiga_os_exec_base_library_name());
    } else if (source_name != NULL) trace_addr_reg_set_name(state, dest_reg, source_name);
    else trace_addr_reg_clear(state, dest_reg);
  }
}

typedef struct M68kRenderWrapperTraceQueueEntry {
  uint32_t offset;
  M68kRenderBaseTraceState state;
} M68kRenderWrapperTraceQueueEntry;

static int wrapper_trace_enqueue(M68kRenderWrapperTraceQueueEntry *queue, size_t *queue_count, uint32_t offset,
    const M68kRenderBaseTraceState *state) {
  size_t index;
  if (queue == NULL || queue_count == NULL || state == NULL || *queue_count >= 32U) return 0;
  for (index = 0U; index < *queue_count; ++index) {
    if (queue[index].offset == offset &&
        memcmp(&queue[index].state, state, sizeof(queue[index].state)) == 0) {
      return 1;
    }
  }
  queue[*queue_count].offset = offset;
  queue[*queue_count].state = *state;
  ++(*queue_count);
  return 1;
}

static int trace_indexed_vector_wrapper_from_entry(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t entry_offset,
    const M68kRenderBaseTraceState *entry_state, uint8_t *out_index_reg, char *out_library_name,
    size_t out_library_name_size) {
  M68kRenderWrapperTraceQueueEntry queue[32];
  size_t queue_count = 0U;
  size_t queue_index = 0U;
  if (out_index_reg != NULL) *out_index_reg = 0U;
  if (out_library_name != NULL && out_library_name_size > 0U) out_library_name[0] = '\0';
  if (lookup == NULL || section == NULL || accepted_start == NULL || entry_state == NULL ||
      out_index_reg == NULL || out_library_name == NULL || out_library_name_size == 0U ||
      entry_offset >= section->size) {
    return 0;
  }
  if (!wrapper_trace_enqueue(queue, &queue_count, entry_offset, entry_state)) return 0;
  while (queue_index < queue_count) {
    M68kRenderWrapperTraceQueueEntry entry = queue[queue_index++];
    M68kRenderBaseTraceState state = entry.state;
    const M68kDecodeCandidate *candidate;
    uint8_t index_reg = 0U;
    uint32_t target_offset = 0U;
    uint32_t next_offset;
    if (!accepted_start_at(section, accepted_start, entry.offset)) continue;
    candidate = find_candidate_at_offset_local(section, entry.offset);
    if (candidate == NULL || candidate->byte_count == 0U) continue;
    if (candidate_calls_a6_data_indexed_vector(candidate, &index_reg) && state.addr_regs[6].known) {
      *out_index_reg = index_reg;
      snprintf(out_library_name, out_library_name_size, "%s", state.addr_regs[6].name);
      return 1;
    }
    trace_state_update_register_names_after_candidate(&state, lookup, section, candidate);
    if (candidate_first_local_control_target(section, candidate, &target_offset)) {
      if (!wrapper_trace_enqueue(queue, &queue_count, target_offset, &state)) return 0;
    }
    next_offset = candidate->offset + candidate->byte_count;
    if (render_cfg_candidate_has_fallthrough(candidate) && next_offset < section->size &&
        accepted_start_at(section, accepted_start, next_offset)) {
      if (!wrapper_trace_enqueue(queue, &queue_count, next_offset, &state)) return 0;
    }
  }
  return 0;
}

static void trace_local_slot_set(M68kRenderBaseTraceState *state, uint8_t base_reg, int16_t displacement,
    const char *library_name) {
  size_t index;
  uint16_t base_id = trace_base_id_from_name(library_name);
  if (state == NULL || base_reg >= 8U || library_name == NULL || library_name[0] == '\0') return;
  if (base_id == AMIGA_OS_BASE_ID_NONE) return;
  for (index = 0U; index < sizeof(state->local_slots) / sizeof(state->local_slots[0]); ++index) {
    M68kRenderTraceLocalSlot *slot = &state->local_slots[index];
    if (slot->valid && slot->base_reg == base_reg && slot->displacement == displacement) {
      slot->base_id = base_id;
      snprintf(slot->library_name, sizeof(slot->library_name), "%s", library_name);
      return;
    }
  }
  for (index = 0U; index < sizeof(state->local_slots) / sizeof(state->local_slots[0]); ++index) {
    M68kRenderTraceLocalSlot *slot = &state->local_slots[index];
    if (slot->valid) continue;
    slot->valid = 1U;
    slot->base_reg = base_reg;
    slot->base_id = base_id;
    slot->displacement = displacement;
    snprintf(slot->library_name, sizeof(slot->library_name), "%s", library_name);
    return;
  }
}

static const char *trace_local_slot_library(const M68kRenderBaseTraceState *state, uint8_t base_reg,
    int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return NULL;
  for (index = 0U; index < sizeof(state->local_slots) / sizeof(state->local_slots[0]); ++index) {
    const M68kRenderTraceLocalSlot *slot = &state->local_slots[index];
    if (slot->valid && slot->base_reg == base_reg && slot->displacement == displacement)
      return platform_facts_v2_library_name_for_base_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, slot->base_id);
  }
  return NULL;
}

static int read_library_name_string_at(const M68kDecodeSectionIR *section, uint32_t offset, char *out_name,
    size_t out_size) {
  size_t index = 0U;
  if (section == NULL || section->data == NULL || out_name == NULL || out_size == 0U || offset >= section->size)
    return 0;
  while (offset + index < section->size && index + 1U < out_size) {
    uint8_t value = section->data[offset + index];
    if (value == 0U) {
      out_name[index] = '\0';
      return index != 0U && render_lookup_amiga_library_base_name_for_library_name(out_name) != NULL;
    }
    if (value < 0x20U || value > 0x7EU) return 0;
    out_name[index++] = (char)value;
  }
  return 0;
}

static int read_library_name_string_from_object(const M68kObject *object, size_t section_index, uint32_t offset,
    char *out_name, size_t out_size) {
  size_t index = 0U;
  const M68kSection *section;
  if (object == NULL || section_index >= object->section_count || out_name == NULL || out_size == 0U) return 0;
  section = &object->sections[section_index];
  if (section->data == NULL || offset >= section->data_size) return 0;
  while (offset + index < section->data_size && index + 1U < out_size) {
    uint8_t value = section->data[offset + index];
    if (value == 0U) {
      out_name[index] = '\0';
      return index != 0U && render_lookup_amiga_library_base_name_for_library_name(out_name) != NULL;
    }
    if (value < 0x20U || value > 0x7EU) return 0;
    out_name[index++] = (char)value;
  }
  return 0;
}

static int candidate_lea_relocated_library_name_to_address_reg(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate, char *out_name, size_t out_size) {
  uint32_t relocation_offset, relocation_end;
  if (lookup == NULL || section == NULL || candidate == NULL || out_name == NULL || out_size == 0U) return 0;
  relocation_end = candidate->offset + candidate->byte_count;
  for (relocation_offset = candidate->offset; relocation_offset < relocation_end; ++relocation_offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, relocation_offset);
    size_t operand_index = 0U;
    if (relocation == NULL) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 0U) continue;
    return read_library_name_string_from_object(lookup->object, relocation->target_section_index,
      relocation->target_offset, out_name, out_size);
  }
  return 0;
}

static int format_lower_symbol_component(const char *text, char *out, size_t out_size) {
  size_t in_index;
  size_t out_index = 0U;
  int previous_sep = 0;
  if (out == NULL || out_size == 0U) return 0;
  out[0] = '\0';
  if (text == NULL || text[0] == '\0') return 0;
  for (in_index = 0U; text[in_index] != '\0'; ++in_index) {
    char ch = text[in_index];
    int is_alnum = (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9');
    if (is_alnum) {
      if (out_index + 1U >= out_size) return 0;
      out[out_index++] = ascii_lower_local(ch);
      previous_sep = 0;
    } else if (out_index != 0U && !previous_sep) {
      if (out_index + 1U >= out_size) return 0;
      out[out_index++] = '_';
      previous_sep = 1;
    }
  }
  while (out_index != 0U && out[out_index - 1U] == '_') --out_index;
  out[out_index] = '\0';
  return out_index != 0U;
}

static int format_app_named_value_slot_symbol(const char *source_name, char *symbol_name, size_t symbol_name_size) {
  char name_part[48];
  int written;
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  symbol_name[0] = '\0';
  if (source_name == NULL || source_name[0] == '\0') return 0;
  if (strcmp(source_name, "SegList") == 0 || strcmp(source_name, "seglist") == 0) {
    written = snprintf(symbol_name, symbol_name_size, "app_SegList");
    return written > 0 && (size_t)written < symbol_name_size;
  }
  if (!format_lower_symbol_component(source_name, name_part, sizeof(name_part))) return 0;
  written = snprintf(symbol_name, symbol_name_size, "app_%s", name_part);
  return written > 0 && (size_t)written < symbol_name_size;
}

static int open_device_iorequest_input_info(PlatformFactsV2CallInput *out_input) {
  PlatformFactsV2CallInput input;
  if (out_input != NULL) platform_facts_v2_call_input_init(out_input);
  if (!platform_facts_v2_call_input_by_register(M68K_PLATFORM_BACKEND_AMIGA_HUNK, "_LVOOpenDevice",
      AMIGA_OS_REGISTER_ADDRESS, 1U, &input)) {
    return 0;
  }
  if (strcmp(input.type_name, "IO") != 0) return 0;
  if (out_input != NULL) *out_input = input;
  return 1;
}

static int amiga_vector_iorequest_address_register(const AmigaOsLibraryVectorInfo *vector, uint8_t *out_reg) {
  const char *symbol_name;
  size_t count = 0U;
  size_t index;
  if (out_reg != NULL) *out_reg = 0U;
  if (vector == NULL) return 0;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  if (symbol_name == NULL || symbol_name[0] == '\0') return 0;
  if (!platform_facts_v2_call_input_count_for_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK, symbol_name, &count)) return 0;
  for (index = 0U; index < count; ++index) {
    PlatformFactsV2CallInput input;
    if (!platform_facts_v2_call_input_at(M68K_PLATFORM_BACKEND_AMIGA_HUNK, symbol_name, index, &input)) continue;
    if (input.reg_kind == AMIGA_OS_REGISTER_ADDRESS && input.reg_index < 8U &&
        input.has_struct_type && strcmp(input.type_name, "IO") == 0) {
      if (out_reg != NULL) *out_reg = input.reg_index;
      return 1;
    }
  }
  return 0;
}

static int format_open_device_app_iorequest_slot_name(const char *device_name, char *symbol_name,
    size_t symbol_name_size) {
  PlatformFactsV2CallInput input;
  char device_part[48];
  char input_part[32];
  int written;
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  symbol_name[0] = '\0';
  if (!open_device_iorequest_input_info(&input)) return 0;
  if (!format_lower_symbol_component(device_name, device_part, sizeof(device_part)) ||
      !format_lower_symbol_component(input.input_name, input_part, sizeof(input_part))) {
    return 0;
  }
  written = snprintf(symbol_name, symbol_name_size, "app_%s_%s", device_part, input_part);
  return written > 0 && (size_t)written < symbol_name_size;
}

int candidate_lea_known_amiga_name_to_address_reg(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate, uint8_t *out_reg, char *out_name,
    size_t out_size) {
  M68kInstructionIR instruction;
  uint32_t absolute_offset = 0U;
  uint8_t dest_reg = 0U;
  int16_t displacement;
  int64_t target;
  if (section == NULL || candidate == NULL || out_name == NULL || out_size == 0U) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_LEA || candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_address_register_index_local(&instruction.operands[1], &dest_reg)) return 0;
  if (instruction.operands[0].kind == M68K_ASM_OPERAND_EA &&
      instruction.operands[0].value.ea_mode == 7U && instruction.operands[0].value.ea_reg == 2U) {
    displacement = (int16_t)(instruction.operands[0].value.value & 0xFFFFU);
    target = (int64_t)candidate->offset + 2 + displacement;
    if (target < 0 || target > UINT32_MAX) return 0;
    if (!read_library_name_string_at(section, (uint32_t)target, out_name, out_size)) return 0;
    if (out_reg != NULL) *out_reg = dest_reg;
    return 1;
  }
  if (operand_absolute_offset_local(&instruction.operands[0], &absolute_offset)) {
    if (!read_library_name_string_at(section, absolute_offset, out_name, out_size) &&
        !candidate_lea_relocated_library_name_to_address_reg(lookup, section, candidate, out_name, out_size)) {
      return 0;
    }
    if (out_reg != NULL) *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static int candidate_lea_app_base_address_to_address_reg(const M68kDecodeCandidate *candidate, uint8_t *out_reg,
    int16_t *out_displacement) {
  M68kInstructionIR instruction;
  uint8_t base_reg = 0U;
  uint8_t dest_reg = 0U;
  int16_t displacement = 0;
  if (candidate == NULL || out_reg == NULL || out_displacement == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_LEA || candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_is_address_displacement_local(&instruction.operands[0], &base_reg, &displacement) ||
      base_reg != 6U) {
    return 0;
  }
  if (!operand_address_register_index_local(&instruction.operands[1], &dest_reg)) return 0;
  *out_reg = dest_reg;
  *out_displacement = displacement;
  return 1;
}

static int candidate_is_exec_open_library_call(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate) {
  int16_t lvo = 0;
  if (state == NULL || !state->addr_regs[6].known ||
      state->addr_regs[6].base_id != AMIGA_OS_BASE_ID_SYSBASE) {
    return 0;
  }
  if (!candidate_calls_a6_lvo(candidate, &lvo)) return 0;
  return platform_facts_v2_library_vector_lvo_matches_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK, lvo,
      "_LVOOpenLibrary") ||
    platform_facts_v2_library_vector_lvo_matches_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK, lvo,
      "_LVOOldOpenLibrary");
}

static int amiga_vector_is_open_library(const AmigaOsLibraryVectorInfo *vector) {
  if (vector == NULL) return 0;
  return vector->function_id == AMIGA_OS_FUNCTION_ID_OPENLIBRARY ||
    vector->function_id == AMIGA_OS_FUNCTION_ID_OLDOPENLIBRARY;
}

static int candidate_is_exec_open_device_call(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate) {
  int16_t lvo = 0;
  if (state == NULL || !state->addr_regs[6].known ||
      state->addr_regs[6].base_id != AMIGA_OS_BASE_ID_SYSBASE) {
    return 0;
  }
  if (!candidate_calls_a6_lvo(candidate, &lvo)) return 0;
  return platform_facts_v2_library_vector_lvo_matches_symbol(M68K_PLATFORM_BACKEND_AMIGA_HUNK, lvo,
    "_LVOOpenDevice");
}

static int render_lookup_record_device_call_from_iorequest(M68kRenderLookup *lookup,
    const M68kRenderBaseTraceState *state, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate) {
  int16_t lvo = 0;
  const AmigaOsLibraryVectorInfo *vector;
  uint8_t iorequest_reg = 0U;
  const char *device_name;
  if (lookup == NULL || state == NULL || section == NULL || candidate == NULL) return 0;
  if (!state->addr_regs[6].known || state->addr_regs[6].base_id == AMIGA_OS_BASE_ID_NONE ||
      !candidate_calls_a6_lvo(candidate, &lvo)) {
    return 0;
  }
  vector = amiga_os_find_library_vector_by_base_id(state->addr_regs[6].base_id, lvo);
  if (!amiga_vector_iorequest_address_register(vector, &iorequest_reg)) return 0;
  if (!state->app_addresses[iorequest_reg].known) return 0;
  device_name = render_lookup_device_name_for_iorequest(lookup, state->app_addresses[iorequest_reg].displacement);
  if (device_name == NULL) return 0;
  return render_lookup_add_device_call(lookup, section->section_index, candidate->offset, device_name);
}

static int candidate_stores_library_to_local_slot(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate, uint8_t *out_base_reg, int16_t *out_displacement,
    const char **out_library_name) {
  M68kInstructionIR instruction;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const char *library_name;
  if (state == NULL || candidate == NULL || out_base_reg == NULL || out_displacement == NULL ||
      out_library_name == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  library_name = trace_library_from_operand(state, &instruction.operands[0]);
  if (library_name == NULL || render_lookup_amiga_library_base_name_for_library_name(library_name) == NULL)
    return 0;
  if (!operand_is_address_displacement_local(&instruction.operands[1], &base_reg, &displacement)) return 0;
  *out_base_reg = base_reg;
  *out_displacement = displacement;
  *out_library_name = library_name;
  return 1;
}

static int candidate_stores_d0_to_a6_slot(const M68kDecodeCandidate *candidate, int16_t *out_displacement) {
  M68kInstructionIR instruction;
  uint8_t source_reg = 0U;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (out_displacement != NULL) *out_displacement = 0;
  if (candidate == NULL || out_displacement == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_is_data_register_local(&instruction.operands[0], &source_reg) || source_reg != 0U) return 0;
  if (!operand_is_address_displacement_local(&instruction.operands[1], &base_reg, &displacement) ||
      base_reg != 6U) return 0;
  *out_displacement = displacement;
  return 1;
}

int reglist_contains_data_register_local(const M68kOperandIR *operand, uint8_t reg_index) {
  uint32_t mask;
  if (operand == NULL || operand->kind != M68K_ASM_OPERAND_REGLIST || reg_index >= 8U) return 0;
  mask = operand->value.value;
  return (mask & (1UL << reg_index)) != 0U;
}

static int candidate_writes_d0_unknown(const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  if (candidate == NULL) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  metadata = m68k_sim_metadata_for_instruction(&instruction);
  if (metadata != NULL && metadata->flow_kind == M68K_SIM_FLOW_CALL) return 1;
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEM)
    return instruction.operand_count >= 2U && reglist_contains_data_register_local(&instruction.operands[1], 0U);
  if (instruction.operand_count >= 2U) {
    const M68kOperandIR *dest = &instruction.operands[instruction.operand_count - 1U];
    uint8_t dest_reg = 0U;
    if (operand_is_data_register_local(dest, &dest_reg) && dest_reg == 0U) return 1;
  }
  return 0;
}

static int candidate_stops_open_library_store_scan(const M68kDecodeCandidate *candidate) {
  return !candidate_has_local_helper_summary_fallthrough(candidate);
}

static int candidate_has_open_library_store_scan_fallthrough(const M68kDecodeCandidate *candidate) {
  return !candidate_stops_open_library_store_scan(candidate);
}

static void update_open_library_store_scan_a6_state(const M68kDecodeCandidate *candidate, int *a6_is_exec) {
  M68kInstructionIR instruction;
  if (candidate == NULL || a6_is_exec == NULL) return;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return;
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEM) {
    if (instruction.operand_count >= 2U && reglist_contains_address_register_local(&instruction.operands[1], 6U))
      *a6_is_exec = 0;
    return;
  }
  if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_MOVEA && instruction.operand_count >= 2U &&
      operand_is_address_register_local(&instruction.operands[1], 6U)) {
    *a6_is_exec = operand_is_absolute_address_local(&instruction.operands[0], 4U) ? 1 : 0;
  }
}

static int open_library_store_scan_enqueue(uint32_t *queue_offsets, uint64_t *queue_a6_is_exec, size_t *queue_count,
    const uint32_t *visited_offsets, uint64_t visited_a6_is_exec, size_t visited_count, uint32_t offset,
    int a6_is_exec) {
  size_t index;
  if (queue_offsets == NULL || queue_a6_is_exec == NULL || queue_count == NULL ||
      visited_offsets == NULL) return 0;
  for (index = 0U; index < visited_count; ++index)
    if (visited_offsets[index] == offset &&
        m68k_bitset_u64_has(visited_a6_is_exec, (uint8_t)index) == (a6_is_exec != 0)) {
      return 0;
    }
  for (index = 0U; index < *queue_count; ++index)
    if (queue_offsets[index] == offset &&
        m68k_bitset_u64_has(*queue_a6_is_exec, (uint8_t)index) == (a6_is_exec != 0)) {
      return 0;
    }
  if (*queue_count >= 64U) return 0;
  queue_offsets[*queue_count] = offset;
  if (a6_is_exec) {
    m68k_bitset_u64_set(queue_a6_is_exec, (uint8_t)*queue_count);
  } else {
    m68k_bitset_u64_clear(queue_a6_is_exec, (uint8_t)*queue_count);
  }
  ++(*queue_count);
  return 1;
}

static int render_lookup_add_open_library_result_app_base_slots(M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t start_offset,
    const char *library_name) {
  uint32_t queue_offsets[64];
  uint32_t visited_offsets[64];
  uint64_t queue_a6_is_exec = 0U;
  uint64_t visited_a6_is_exec = 0U;
  size_t queue_head = 0U;
  size_t queue_count = 0U;
  size_t visited_count = 0U;
  int result = 0;
  if (lookup == NULL || section == NULL || accepted_start == NULL ||
      library_name == NULL || library_name[0] == '\0') return 0;
  open_library_store_scan_enqueue(queue_offsets, &queue_a6_is_exec, &queue_count,
    visited_offsets, visited_a6_is_exec, visited_count, start_offset, 1);
  while (queue_head < queue_count && visited_count < sizeof(visited_offsets) / sizeof(visited_offsets[0])) {
    uint32_t offset = queue_offsets[queue_head];
    int a6_is_exec = m68k_bitset_u64_has(queue_a6_is_exec, (uint8_t)queue_head);
    const M68kDecodeCandidate *candidate;
    int16_t displacement = 0;
    size_t target_index;
    int next_a6_is_exec;
    ++queue_head;
    visited_offsets[visited_count] = offset;
    if (a6_is_exec) {
      m68k_bitset_u64_set(&visited_a6_is_exec, (uint8_t)visited_count);
    } else {
      m68k_bitset_u64_clear(&visited_a6_is_exec, (uint8_t)visited_count);
    }
    ++visited_count;
    if (!accepted_start_at(section, accepted_start, offset)) continue;
    candidate = find_candidate_at_offset_local(section, offset);
    if (candidate == NULL || candidate->byte_count == 0U) continue;
    if (!a6_is_exec && candidate_stores_d0_to_a6_slot(candidate, &displacement)) {
      if (render_lookup_add_base_field_slot(lookup, M68K_APP_BASE_SYMBOL, displacement, library_name,
          section->section_index, candidate->offset) != 0)
        return -1;
      result = 1;
      continue;
    }
    if (candidate_writes_d0_unknown(candidate)) continue;
    next_a6_is_exec = a6_is_exec;
    update_open_library_store_scan_a6_state(candidate, &next_a6_is_exec);
    for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
      const M68kDecodeTarget *target = &candidate->targets[target_index];
      if (target->has_section == 0U || target->section_index != section->section_index) continue;
      open_library_store_scan_enqueue(queue_offsets, &queue_a6_is_exec, &queue_count,
        visited_offsets, visited_a6_is_exec, visited_count, target->offset, next_a6_is_exec);
    }
    if (candidate_has_open_library_store_scan_fallthrough(candidate)) {
      open_library_store_scan_enqueue(queue_offsets, &queue_a6_is_exec, &queue_count,
        visited_offsets, visited_a6_is_exec, visited_count, candidate->offset + candidate->byte_count,
        next_a6_is_exec);
    }
  }
  return result;
}

static int candidate_copies_local_slot_to_global_slot(const M68kRenderLookup *lookup,
    const M68kRenderBaseTraceState *state, size_t section_index, const M68kDecodeCandidate *candidate,
    size_t *out_target_section, uint32_t *out_target_offset, const char **out_library_name) {
  M68kInstructionIR instruction;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const char *library_name;
  uint32_t offset;
  uint32_t end;
  if (lookup == NULL || state == NULL || candidate == NULL || out_target_section == NULL ||
      out_target_offset == NULL || out_library_name == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  if (!operand_is_address_displacement_local(&instruction.operands[0], &base_reg, &displacement)) return 0;
  library_name = trace_local_slot_library(state, base_reg, displacement);
  if (library_name == NULL || render_lookup_amiga_library_base_name_for_library_name(library_name) == NULL)
    return 0;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset + 2U; offset < end; ++offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, offset);
    size_t operand_index = 0U;
    if (relocation == NULL) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 1U) continue;
    *out_target_section = relocation->target_section_index;
    *out_target_offset = relocation->target_offset;
    *out_library_name = library_name;
    return 1;
  }
  return 0;
}

static int candidate_stores_library_to_global_slot(const M68kRenderLookup *lookup,
    const M68kRenderBaseTraceState *state, size_t section_index, const M68kDecodeCandidate *candidate,
    size_t *out_target_section, uint32_t *out_target_offset, const char **out_library_name) {
  M68kInstructionIR instruction;
  const char *library_name;
  uint32_t offset;
  uint32_t end;
  if (lookup == NULL || state == NULL || candidate == NULL || out_target_section == NULL ||
      out_target_offset == NULL || out_library_name == NULL) return 0;
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  library_name = trace_library_from_operand(state, &instruction.operands[0]);
  if (library_name == NULL || render_lookup_amiga_library_base_name_for_library_name(library_name) == NULL)
    return 0;
  end = candidate->offset + candidate->byte_count;
  for (offset = candidate->offset + 2U; offset < end; ++offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, offset);
    size_t operand_index = 0U;
    if (relocation == NULL) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) || operand_index != 1U) continue;
    *out_target_section = relocation->target_section_index;
    *out_target_offset = relocation->target_offset;
    *out_library_name = library_name;
    return 1;
  }
  return 0;
}

static int candidate_stores_named_value_to_app_slot(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate, int16_t *out_displacement, char *out_symbol_name,
    size_t out_symbol_name_size) {
  M68kInstructionIR instruction;
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  const char *source_name;
  if (out_symbol_name != NULL && out_symbol_name_size != 0U) out_symbol_name[0] = '\0';
  if (state == NULL || candidate == NULL || out_displacement == NULL ||
      out_symbol_name == NULL || out_symbol_name_size == 0U) {
    return 0;
  }
  if (candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->size_suffix != 'l' ||
      candidate->operand_count != 2U) {
    return 0;
  }
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  source_name = trace_name_from_operand(state, &instruction.operands[0]);
  if (source_name == NULL || source_name[0] == '\0' || platform_state_name_is_app_base(source_name)) return 0;
  if (render_lookup_amiga_library_or_base_name_known(source_name)) {
    return 0;
  }
  if (!operand_is_address_displacement_local(&instruction.operands[1], &base_reg, &displacement)) return 0;
  if (base_reg >= 8U || !state->addr_regs[base_reg].known ||
      !platform_state_name_is_app_base(state->addr_regs[base_reg].name)) {
    return 0;
  }
  if (!format_app_named_value_slot_symbol(source_name, out_symbol_name, out_symbol_name_size)) return 0;
  *out_displacement = displacement;
  return 1;
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_traced_helper_call_vector(
    const M68kRenderLookup *lookup, const M68kDecodeIR *decode, uint8_t **accepted_start,
    size_t source_section_index, const M68kDecodeCandidate *candidate, const M68kRenderBaseTraceState *state) {
  M68kInstructionIR instruction;
  uint8_t reg = 0U;
  int16_t displacement = 0;
  const M68kRenderTraceTarget *target;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || candidate == NULL || state == NULL ||
      source_section_index >= decode->section_count || !candidate_has_call_flow_local(candidate)) {
    return NULL;
  }
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 || instruction.operand_count == 0U)
    return NULL;
  if (!operand_is_address_memory_local(&instruction.operands[0], &reg, &displacement) || reg >= 8U ||
      displacement != 0) {
    return NULL;
  }
  target = &state->addr_targets[reg];
  if (!target->known || target->section_index >= decode->section_count) return NULL;
  if (target->section_index == source_section_index && target->offset == candidate->offset) return NULL;
  return resolve_amiga_local_helper_primary_vector_at(lookup, decode, accepted_start,
    target->section_index, target->offset, 1U);
}

static int app_slot_access_memory_write_is_readwrite(const M68kSimFormMetadata *metadata) {
  if (metadata == NULL) return 0;
  switch (metadata->operation_type) {
  case M68K_SIM_OP_MOVE:
  case M68K_SIM_OP_CLEAR:
  case M68K_SIM_OP_SET_COND:
  case M68K_SIM_OP_MOVE_MULTIPLE:
  case M68K_SIM_OP_MOVE_PERIPHERAL:
    return 0;
  default:
    return 1;
  }
}

uint8_t app_slot_access_kind_from_instruction(const M68kInstructionIR *instruction, size_t operand_index) {
  const M68kSimFormMetadata *metadata;
  uint8_t access_kind;
  if (instruction == NULL || operand_index >= instruction->operand_count || operand_index >= 4U)
    return M68K_APP_SLOT_ACCESS_NONE;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return M68K_APP_SLOT_ACCESS_NONE;
  access_kind = metadata->operand_access_kinds[operand_index];
  if (access_kind == M68K_SIM_ACCESS_COMPUTE_ADDRESS || access_kind == M68K_SIM_ACCESS_BRANCH_TARGET)
    return M68K_APP_SLOT_ACCESS_ADDRESS;
  if (access_kind == M68K_SIM_ACCESS_MEMORY_READ || access_kind == M68K_SIM_ACCESS_REGISTER_READ)
    return M68K_APP_SLOT_ACCESS_READ;
  if (access_kind == M68K_SIM_ACCESS_MEMORY_WRITE || access_kind == M68K_SIM_ACCESS_REGISTER_WRITE) {
    return app_slot_access_memory_write_is_readwrite(metadata)
      ? M68K_APP_SLOT_ACCESS_READ_WRITE
      : M68K_APP_SLOT_ACCESS_WRITE;
  }
  return M68K_APP_SLOT_ACCESS_NONE;
}

uint8_t app_slot_access_size_from_instruction(const M68kInstructionIR *instruction, uint8_t access_kind) {
  if (access_kind == M68K_APP_SLOT_ACCESS_ADDRESS) return 0U;
  if (instruction == NULL) return 0U;
  if (instruction->size_suffix == 'b') return 1U;
  if (instruction->size_suffix == 'w') return 2U;
  if (instruction->size_suffix == 'l') return 4U;
  return 0U;
}

static int render_lookup_seed_policy_rsset_use_site_app_refs(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  uint16_t binding_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || policy == NULL ||
      lookup->object == NULL || lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (binding_index = 0U; binding_index < policy->rsset_use_site_binding_count &&
       binding_index < M68K_ANALYSIS_RSSET_USE_SITE_BINDING_LIMIT; ++binding_index) {
    const M68kAnalysisRssetUseSiteBinding *binding = &policy->rsset_use_site_bindings[binding_index];
    size_t section_index;
    if (binding->base_evidence_id[0] == '\0' || binding->base_reg >= 8U || binding->operand_index >= 4U ||
        binding->displacement > 0x7FFFU) {
      continue;
    }
    for (section_index = 0U; section_index < decode->section_count; ++section_index) {
      const M68kDecodeSectionIR *section = &decode->sections[section_index];
      size_t candidate_index;
      if (section->section_index != binding->section_index) continue;
      for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
        const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
        M68kInstructionIR instruction;
        uint8_t base_reg = 0U;
        int16_t displacement = 0;
        uint8_t access_kind;
        if (candidate->offset != binding->offset ||
            !candidate_is_accepted_start(section, accepted_start[section_index], candidate)) {
          continue;
        }
        if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0 ||
            binding->operand_index >= instruction.operand_count ||
            !operand_is_address_displacement_local(&instruction.operands[binding->operand_index], &base_reg,
              &displacement) ||
            base_reg != binding->base_reg || displacement != (int16_t)binding->displacement) {
          continue;
        }
        access_kind = app_slot_access_kind_from_instruction(&instruction, binding->operand_index);
        if (render_lookup_add_app_access_ref(lookup, section->section_index, candidate->offset, base_reg,
            displacement, binding->operand_index, access_kind,
            app_slot_access_size_from_instruction(&instruction, access_kind), 0,
            M68K_APP_SLOT_BASE_USE_SITE_BINDING) != 0) {
          return -1;
        }
      }
    }
  }
  return 0;
}

static int displacement_is_custom_hardware_offset(int16_t displacement) {
  uint16_t custom_base_id = PLATFORM_FACTS_V2_HARDWARE_BASE_ID_NONE;
  if (displacement < 0) return 0;
  if (!platform_facts_v2_custom_hardware_base_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, &custom_base_id)) return 0;
  return platform_facts_v2_hardware_base_offset_known(M68K_PLATFORM_BACKEND_AMIGA_HUNK,
    custom_base_id, (uint32_t)(uint16_t)displacement);
}

int render_state_operand_uses_app_base(const M68kRenderPlatformState *state, uint8_t base_reg,
    int16_t displacement) {
  if (state == NULL || base_reg >= 8U) return 0;
  if (state->relative_hardware[base_reg].offsets.count != 0U) return 0;
  if (m68k_bitset_u32_has(state->address_hardware_base_known, base_reg)) return 0;
  if (m68k_bitset_u32_has(state->address_app_base_known, base_reg)) return 1;
  if (m68k_bitset_u32_has(state->address_base_known, base_reg))
    return library_base_can_use_app_extension_slot(state->address_base_library[base_reg], displacement);
  return base_reg == 6U && !displacement_is_custom_hardware_offset(displacement);
}

uint8_t render_app_base_evidence_kind(const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *state, uint8_t base_reg, int16_t displacement, uint8_t access_size) {
  const M68kAnalysisPolicy *policy = lookup != NULL ? lookup->policy : NULL;
  if (state == NULL || base_reg >= 8U || state->relative_hardware[base_reg].offsets.count != 0U ||
      m68k_bitset_u32_has(state->address_hardware_base_known, base_reg))
    return M68K_APP_SLOT_BASE_UNSPECIFIED;
  if (m68k_bitset_u32_has(state->address_app_base_known, base_reg))
    return M68K_APP_SLOT_BASE_REGISTER_STATE;
  if (m68k_bitset_u32_has(state->address_base_known, base_reg))
    return library_base_can_use_app_extension_slot(state->address_base_library[base_reg], displacement)
      ? M68K_APP_SLOT_BASE_LIBRARY_EXTENSION : M68K_APP_SLOT_BASE_UNSPECIFIED;
  if (m68k_bitset_u32_has(state->address_layout_base_known, base_reg))
    return strcmp(state->address_layout_base_symbol[base_reg], M68K_APP_BASE_SYMBOL) == 0
      ? M68K_APP_SLOT_BASE_REGISTER_STATE : M68K_APP_SLOT_BASE_UNSPECIFIED;
  if (base_reg != 6U) return M68K_APP_SLOT_BASE_UNSPECIFIED;
  if (!displacement_is_custom_hardware_offset(displacement)) return M68K_APP_SLOT_BASE_A6_FALLBACK;
  /* A declared app field can disambiguate a numeric hardware-offset collision,
   * but does not prove an unknown A6 value. Retain that distinction in the IR.
   * Require the whole access, not just its start, inside the canonical owner. */
  return policy_declared_app_extent_covers(policy, displacement, access_size)
    ? M68K_APP_SLOT_BASE_DECLARED_LAYOUT_A6_FALLBACK : M68K_APP_SLOT_BASE_UNSPECIFIED;
}

/* Reuse the final CFG state to bind existing RSSET declarations to encoded
 * operands. The vector follows the final source-ordered access walk, enabling
 * binary lookup during rendering. Ambiguous aliases do not choose a name. */
static int render_lookup_record_layout_field_uses(M68kRenderLookup *lookup, size_t section_index,
    const M68kRenderPlatformState *state, const M68kInstructionIR *instruction, uint32_t offset) {
  size_t operand_index;
  const M68kAnalysisPolicy *policy = lookup->policy;
  if (policy == NULL || lookup->typed_flow_incomplete_count != 0U) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t reg = 0U, width = 0U;
    int16_t displacement;
    uint16_t index, selected = UINT16_MAX;
    const char *base;
    if (!operand_is_address_displacement_local(&instruction->operands[operand_index], &reg, &displacement) ||
        reg >= 8U || displacement < 0) continue;
    if (m68k_bitset_u32_has(state->address_app_base_known, reg)) base = M68K_APP_BASE_SYMBOL;
    else if (m68k_bitset_u32_has(state->address_layout_base_known, reg)) base = state->address_layout_base_symbol[reg];
    else continue;
    if (!platform_operand_memory_span(instruction, operand_index, NULL, NULL, &width)) continue;
    for (index = 0U; index < policy->rsset_layout_region_count; ++index) {
      const M68kAnalysisRssetLayoutRegion *region = &policy->rsset_layout_regions[index];
      const char *owner = region->base_symbol[0] ? region->base_symbol : M68K_APP_BASE_SYMBOL;
      if (strcmp(base, owner) != 0 || region->symbol[0] == '\0' || region->size == 0U ||
          (uint32_t)displacement < region->offset ||
          (uint64_t)(uint16_t)displacement + width > (uint64_t)region->offset + region->size) continue;
      if (selected != UINT16_MAX &&
          (strcmp(policy->rsset_layout_regions[selected].symbol, region->symbol) != 0 ||
           policy->rsset_layout_regions[selected].offset != region->offset)) { selected = UINT16_MAX; break; }
      selected = index;
    }
    if (selected != UINT16_MAX) {
      M68kRenderLayoutFieldUse *use;
      if (lookup->layout_field_use_count == lookup->layout_field_use_capacity) {
        size_t capacity = lookup->layout_field_use_capacity ? lookup->layout_field_use_capacity * 2U : 16U;
        void *grown = render_lookup_grow_array(lookup, lookup->layout_field_uses, lookup->layout_field_use_count,
          sizeof(*use), capacity);
        if (grown == NULL) return -1;
        lookup->layout_field_uses = grown;
        lookup->layout_field_use_capacity = capacity;
      }
      use = &lookup->layout_field_uses[lookup->layout_field_use_count++];
      use->section_index = section_index;
      use->offset = offset;
      use->region_index = selected;
      use->operand_index = (uint8_t)operand_index;
      use->base_reg = reg;
      use->displacement = displacement;
    }
  }
  return 0;
}

/* Explicit base identity comes from the converged CFG. The old linear lane
 * contributes only its qualified fallback/library-extension interpretations. */
static int render_lookup_record_base_app_accesses(M68kRenderLookup *lookup, size_t section_index,
    const M68kRenderPlatformState *state, const M68kInstructionIR *instruction, uint32_t offset,
    int legacy_fallbacks) {
  if (!legacy_fallbacks && lookup->typed_flow_incomplete_count != 0U) return 0;
  int32_t minimum = 0;
  size_t operand_index;
  if (lookup == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  if (lookup_has_amiga_resident_library_context(lookup) &&
      !render_amiga_constant_value_by_symbol_id(AMIGA_OS_SYMBOL_ID_LIB_SIZE, &minimum)) return 0;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    uint8_t base_reg = 0U, access, evidence, width;
    int16_t displacement = 0;
    if (!operand_is_address_displacement_local(&instruction->operands[operand_index], &base_reg,
        &displacement) || (int32_t)displacement < minimum) continue;
    access = app_slot_access_kind_from_instruction(instruction, operand_index);
    if (access == M68K_APP_SLOT_ACCESS_NONE) continue;
    width = app_slot_access_size_from_instruction(instruction, access);
    evidence = render_app_base_evidence_kind(lookup, state, base_reg, displacement, width);
    if (legacy_fallbacks && evidence == M68K_APP_SLOT_BASE_REGISTER_STATE) {
      static const M68kRenderPlatformState unattributed = {0};
      /* A linear identity is not CFG provenance. Retain only the same A6
       * fallback interpretation available without that identity; never drop
       * an old conditional site merely because the linear scan saw a load. */
      evidence = render_app_base_evidence_kind(lookup, &unattributed, base_reg, displacement, width);
    }
    if (evidence == M68K_APP_SLOT_BASE_UNSPECIFIED ||
        (legacy_fallbacks ? evidence == M68K_APP_SLOT_BASE_REGISTER_STATE :
          evidence != M68K_APP_SLOT_BASE_REGISTER_STATE)) continue;
    if (render_lookup_add_app_access_ref(lookup, section_index, offset, base_reg, displacement,
        (uint8_t)operand_index, access, width, 1, evidence) != 0) return -1;
  }
  return 0;
}

static int render_lookup_analyze_amiga_app_state_slots(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return -1;
  if (lookup->object == NULL || lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK)
    return 0;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderPlatformState state;
    size_t candidate_index;
    memset(&state, 0, sizeof(state));
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      if (render_lookup_record_base_app_accesses(lookup, section->section_index, &state,
          &instruction, candidate->offset, 1) != 0) return -1;
      {
        M68kRenderPlatformState before = state;
        platform_state_update_after_instruction(&state, lookup, &instruction);
        hardware_relative_transfer_linear(&state, &before, &instruction);
      }
    }
  }
  return 0;
}

static int render_lookup_infer_global_base_slots(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  Arena *workflow_arena = NULL;
  M68kRenderGlobalBaseObservation *observations = NULL;
  M68kRenderGlobalBaseObservation *wrapper_observations = NULL;
  size_t observation_count = 0U;
  size_t observation_capacity = 0U;
  size_t wrapper_observation_count = 0U;
  size_t wrapper_observation_capacity = 0U;
  size_t section_index;
  int result = -1;
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return -1;
  workflow_arena = arena_create(4096U);
  if (workflow_arena == NULL) return -1;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderBaseTraceState trace_state;
    size_t candidate_index;
    uint32_t expected_offset = 0U;
    int have_expected_offset = 0;
    int current_slot_valid = 0;
    int current_segment_valid = 0;
    uint32_t current_segment_entry = 0U;
    size_t current_slot_section = 0U;
    uint32_t current_slot_offset = 0U;
    trace_state_reset(&trace_state);
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      size_t slot_section = 0U;
      uint32_t slot_offset = 0U;
      const char *library_name = NULL;
      const AmigaOsLibraryVectorInfo *helper_vector = NULL;
      uint8_t local_base_reg = 0U, loaded_address_reg = 0U, app_address_reg = 0U;
      int16_t local_displacement = 0, app_address_displacement = 0, named_app_slot_displacement = 0;
      char loaded_library_name[64], named_app_slot_symbol[64];
      int16_t lvo = 0, wrapper_lvo = 0;
      int candidate_sets_d0_library = 0;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      if (have_expected_offset && candidate->offset != expected_offset) {
        current_segment_valid = 0;
      }
      if (!current_segment_valid) {
        current_segment_valid = 1;
        current_segment_entry = candidate->offset;
      }
      trace_state_apply_policy_register_seeds(&trace_state, lookup->policy, section->section_index,
        candidate->offset);
      if (candidate_lea_known_amiga_name_to_address_reg(lookup, section, candidate, &loaded_address_reg,
          loaded_library_name, sizeof(loaded_library_name))) {
        trace_addr_reg_set_name(&trace_state, loaded_address_reg, loaded_library_name);
      }
      if (candidate_lea_app_base_address_to_address_reg(candidate, &app_address_reg, &app_address_displacement)) {
        trace_addr_reg_set_app_address(&trace_state, app_address_reg, app_address_displacement);
      }
      if (candidate_is_exec_open_library_call(&trace_state, candidate) && trace_state.addr_regs[1].known) {
        trace_reg_set(&trace_state.data_regs[0], trace_state.addr_regs[1].name);
        candidate_sets_d0_library = 1;
        if (render_lookup_add_open_library_result_app_base_slots(lookup, section, accepted_start[section_index],
            candidate->offset + candidate->byte_count, trace_state.addr_regs[1].name) < 0) {
          goto cleanup;
        }
      }
      helper_vector = resolve_amiga_local_helper_call_vector(lookup, decode, accepted_start, section->section_index,
        candidate);
      if (helper_vector == NULL) {
        helper_vector = resolve_amiga_traced_helper_call_vector(lookup, decode, accepted_start,
          section->section_index, candidate, &trace_state);
      }
      if (amiga_vector_is_open_library(helper_vector) &&
          (trace_state.addr_regs[1].known || trace_stack_top_library(&trace_state) != NULL)) {
        const char *opened_library_name = trace_state.addr_regs[1].known
          ? trace_state.addr_regs[1].name
          : trace_stack_top_library(&trace_state);
        trace_reg_set(&trace_state.data_regs[0], opened_library_name);
        candidate_sets_d0_library = 1;
        if (render_lookup_add_open_library_result_app_base_slots(lookup, section, accepted_start[section_index],
            candidate->offset + candidate->byte_count, opened_library_name) < 0) {
          goto cleanup;
        }
      }
      if (candidate_is_exec_open_device_call(&trace_state, candidate) &&
          trace_state.addr_regs[0].known && trace_state.app_addresses[1].known) {
        char iorequest_slot_name[64];
        PlatformFactsV2CallInput iorequest_input;
        uint16_t iorequest_struct_id = AMIGA_OS_STRUCT_ID_NONE;
        int typed_slot_added = 0;
        int32_t device_base_displacement = (int32_t)trace_state.app_addresses[1].displacement +
          (int32_t)AMIGA_OS_STRUCT_IO_FIELD_IO_DEVICE_OFFSET;
        if (open_device_iorequest_input_info(&iorequest_input)) {
          iorequest_struct_id = lookup_policy_struct_id_by_name(lookup->policy, iorequest_input.type_name);
        }
        if (render_lookup_add_device_instance(lookup, trace_state.app_addresses[1].displacement,
            trace_state.addr_regs[0].name) != 0 ||
            render_lookup_add_device_call(lookup, section->section_index, candidate->offset,
            trace_state.addr_regs[0].name) != 0) {
          goto cleanup;
        }
        if (iorequest_struct_id != AMIGA_OS_STRUCT_ID_NONE &&
            render_lookup_add_typed_app_slot_region(lookup, trace_state.app_addresses[1].displacement,
              iorequest_struct_id, section->section_index, candidate->offset, &typed_slot_added) != 0) {
          goto cleanup;
        }
        if (format_open_device_app_iorequest_slot_name(trace_state.addr_regs[0].name, iorequest_slot_name,
            sizeof(iorequest_slot_name))) {
          if (render_lookup_add_base_field_slot_with_symbol(lookup, M68K_APP_BASE_SYMBOL,
              trace_state.app_addresses[1].displacement, trace_state.addr_regs[0].name, iorequest_slot_name,
              M68K_RENDER_BASE_FIELD_SLOT_IOREQUEST, 4U, section->section_index, candidate->offset) != 0) {
            goto cleanup;
          }
        }
        if (device_base_displacement >= -32768 && device_base_displacement <= 32767) {
          if (render_lookup_add_device_base_field_slot(lookup, M68K_APP_BASE_SYMBOL,
              (int16_t)device_base_displacement, trace_state.addr_regs[0].name, section->section_index,
              candidate->offset) != 0) {
            goto cleanup;
          }
        }
      }
      if (render_lookup_record_device_call_from_iorequest(lookup, &trace_state, section, candidate) != 0)
        goto cleanup;
      if (candidate_stores_library_to_local_slot(&trace_state, candidate, &local_base_reg, &local_displacement,
          &library_name)) {
        char unknown_owner_name[32];
        const char *owner_name = trace_state.addr_regs[local_base_reg].known
          ? trace_state.addr_regs[local_base_reg].name
          : (local_base_reg == 6U ? M68K_APP_BASE_SYMBOL : NULL);
        if (owner_name == NULL &&
            amiga_unknown_base_register_owner_name(local_base_reg, unknown_owner_name, sizeof(unknown_owner_name))) {
          owner_name = unknown_owner_name;
        }
        trace_local_slot_set(&trace_state, local_base_reg, local_displacement, library_name);
        if (owner_name != NULL &&
            render_lookup_add_base_field_slot(lookup, owner_name, local_displacement, library_name,
              section->section_index, candidate->offset) != 0) {
          goto cleanup;
        }
      }
      if (candidate_stores_named_value_to_app_slot(&trace_state, candidate, &named_app_slot_displacement,
          named_app_slot_symbol, sizeof(named_app_slot_symbol))) {
        if (render_lookup_add_named_layout_field_slot(lookup, M68K_APP_BASE_SYMBOL, named_app_slot_displacement,
            named_app_slot_symbol, section->section_index, candidate->offset) != 0) {
          goto cleanup;
        }
      }
      if (candidate_copies_local_slot_to_global_slot(lookup, &trace_state, section->section_index, candidate,
          &slot_section, &slot_offset, &library_name)) {
        if (render_lookup_add_global_base_slot(lookup, slot_section, slot_offset, library_name,
            section->section_index, candidate->offset) != 0) goto cleanup;
      }
      if (candidate_stores_library_to_global_slot(lookup, &trace_state, section->section_index, candidate,
          &slot_section, &slot_offset, &library_name)) {
        if (render_lookup_add_global_base_slot(lookup, slot_section, slot_offset, library_name,
            section->section_index, candidate->offset) != 0) goto cleanup;
      }
      if (candidate_loads_relocated_global_slot_to_a6(lookup, section->section_index, candidate,
          &slot_section, &slot_offset)) {
        current_slot_valid = 1;
        current_slot_section = slot_section;
        current_slot_offset = slot_offset;
      } else if (candidate_writes_a6_unknown(candidate)) {
        current_slot_valid = 0;
      }
      if (current_slot_valid && candidate_calls_a6_lvo(candidate, &lvo)) {
        if (global_base_observation_add(&observations, &observation_count, &observation_capacity,
          current_slot_section, current_slot_offset, 0U, lvo, workflow_arena) != 0) goto cleanup;
      }
      {
        uint8_t wrapper_reg = 0U;
        uint32_t next_offset = candidate->offset + candidate->byte_count;
        const M68kDecodeCandidate *next_candidate = NULL;
        uint32_t wrapper_offset = 0U;
        if (candidate_loads_data_lvo_immediate(candidate, &wrapper_reg, &wrapper_lvo) &&
            accepted_start_at(section, accepted_start[section_index], next_offset))
          next_candidate = find_candidate_at_offset_local(section, next_offset);
        if (next_candidate != NULL &&
            candidate_direct_same_section_target(next_candidate, section->section_index, &wrapper_offset)) {
          if (global_base_observation_add(&wrapper_observations, &wrapper_observation_count,
              &wrapper_observation_capacity, section->section_index, wrapper_offset, wrapper_reg,
              wrapper_lvo, workflow_arena) != 0) {
            goto cleanup;
          }
        }
      }
      {
        uint8_t index_reg = 0U;
        if (trace_state.addr_regs[6].known && candidate_calls_a6_data_indexed_vector(candidate, &index_reg) &&
            (render_lookup_add_indexed_vector_wrapper(lookup, section->section_index, current_segment_entry,
            index_reg, trace_state.addr_regs[6].name) != 0 ||
            render_lookup_add_indexed_vector_wrapper(lookup, section->section_index, candidate->offset,
            index_reg, trace_state.addr_regs[6].name) != 0 ||
            render_lookup_add_indexed_vector_wrapper_branch_aliases(lookup, section, accepted_start[section_index],
            current_segment_entry, index_reg, trace_state.addr_regs[6].name) != 0)) {
          goto cleanup;
        }
      }
      {
        uint32_t wrapper_entry = 0U;
        uint8_t index_reg = 0U;
        char wrapper_library_name[64];
        if (candidate_direct_same_section_target(candidate, section->section_index, &wrapper_entry) &&
            trace_indexed_vector_wrapper_from_entry(lookup, section, accepted_start[section_index],
              wrapper_entry, &trace_state, &index_reg, wrapper_library_name, sizeof(wrapper_library_name)) &&
            render_lookup_add_indexed_vector_wrapper(lookup, section->section_index, wrapper_entry,
              index_reg, wrapper_library_name) != 0) {
          goto cleanup;
        }
      }
      if (candidate_terminates_a6_state(candidate)) {
        current_slot_valid = 0;
        current_segment_valid = 0;
        trace_state_reset(&trace_state);
      } else {
        if (!candidate_sets_d0_library && candidate_writes_d0_unknown(candidate))
          trace_reg_clear(&trace_state.data_regs[0]);
        trace_state_update_register_names_after_candidate(&trace_state, lookup, section, candidate);
      }
      expected_offset = candidate->offset + candidate->byte_count;
      have_expected_offset = 1;
    }
  }
  for (section_index = 0U; section_index < observation_count; ++section_index) {
    const M68kRenderGlobalBaseObservation *observation = &observations[section_index];
    const char *library_name = unique_library_for_observed_lvos(observation);
    if (library_name == NULL) continue;
    if (render_lookup_add_global_base_slot(lookup, observation->section_index, observation->offset,
        library_name, SIZE_MAX, UINT32_MAX) != 0) goto cleanup;
  }
  for (section_index = 0U; section_index < wrapper_observation_count; ++section_index) {
    const M68kRenderGlobalBaseObservation *observation = &wrapper_observations[section_index];
    const char *library_name = unique_library_for_observed_lvos(observation);
    if (library_name == NULL) continue;
    if (render_lookup_add_indexed_vector_wrapper(lookup, observation->section_index, observation->offset,
        observation->index_reg, library_name) != 0) goto cleanup;
  }
  result = 0;
cleanup:
  arena_destroy(workflow_arena);
  return result;
}

const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_vector_at(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index, uint32_t wrapper_offset,
    unsigned depth) {
  const M68kDecodeSectionIR *section;
  M68kRenderPlatformState state;
  const AmigaOsLibraryVectorInfo *pending_vector = NULL;
  uint32_t cursor;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || section_index >= decode->section_count)
    return NULL;
  if (depth > 4U) return NULL;
  section = &decode->sections[section_index];
  if (!accepted_start_at(section, accepted_start[section_index], wrapper_offset)) return NULL;
  memset(&state, 0, sizeof(state));
  cursor = wrapper_offset;
  while (cursor < section->size && cursor - wrapper_offset < 128U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    uint32_t relocation_offset;
    uint32_t relocation_end;
    const AmigaOsLibraryVectorInfo *vector;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    if (!accepted_start_at(section, accepted_start[section_index], cursor)) break;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    relocation_end = candidate->offset + candidate->byte_count;
    for (relocation_offset = candidate->offset; relocation_offset < relocation_end; ++relocation_offset) {
      const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, relocation_offset);
      size_t operand_index = 0U;
      if (relocation == NULL) continue;
      if (!find_unique_relocation_operand(candidate, relocation, &operand_index) ||
          operand_index >= instruction.operand_count) {
        continue;
      }
      attach_operand_label_symbol(lookup, &instruction, operand_index, section->section_index, candidate->offset,
        relocation->target_section_index, relocation->target_offset);
    }
    if (pending_vector != NULL) {
      if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_RTS) return pending_vector;
      if (!instruction_is_local_wrapper_cleanup(&instruction)) return NULL;
      cursor += candidate->byte_count;
      continue;
    }
    if (candidate_has_non_call_control_target(candidate)) return NULL;
    vector = resolve_amiga_direct_wrapper_call_vector_depth(lookup, decode, accepted_start, section->section_index,
      candidate, depth + 1U);
    if (vector != NULL) {
      pending_vector = vector;
      cursor += candidate->byte_count;
      continue;
    }
    vector = attach_amiga_lvo_symbol_if_known(&state, &instruction);
    if (vector != NULL) {
      if (instruction.mnemonic_id == M68K_ASM_MNEMONIC_JMP) return vector;
      pending_vector = vector;
      cursor += candidate->byte_count;
      continue;
    }
    platform_state_update_after_instruction(&state, lookup, &instruction);
    if (candidate_terminates_a6_state(candidate)) break;
    cursor += candidate->byte_count;
  }
  return NULL;
}

const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_call_vector_depth(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
    const M68kDecodeCandidate *candidate, unsigned depth) {
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  if (depth > 4U) return NULL;
  if (candidate == NULL || !candidate_has_call_flow_local(candidate)) return NULL;
  if (!candidate_direct_control_target(lookup, source_section_index, candidate, &target_section_index, &target_offset))
    return NULL;
  if (target_section_index == source_section_index && target_offset == candidate->offset) return NULL;
  return resolve_amiga_direct_wrapper_vector_at(lookup, decode, accepted_start, target_section_index, target_offset,
    depth);
}

const AmigaOsLibraryVectorInfo *resolve_amiga_direct_wrapper_call_vector(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
    const M68kDecodeCandidate *candidate) {
  return resolve_amiga_direct_wrapper_call_vector_depth(lookup, decode, accepted_start, source_section_index,
    candidate, 0U);
}

void attach_known_instruction_relocations(const M68kRenderLookup *lookup, size_t section_index,
    const M68kDecodeCandidate *candidate, M68kInstructionIR *instruction) {
  uint32_t relocation_offset;
  uint32_t relocation_end;
  if (lookup == NULL || candidate == NULL || instruction == NULL) return;
  relocation_end = candidate->offset + candidate->byte_count;
  for (relocation_offset = candidate->offset; relocation_offset < relocation_end; ++relocation_offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section_index, relocation_offset);
    size_t operand_index = 0U;
    if (relocation == NULL) continue;
    if (!find_unique_relocation_operand(candidate, relocation, &operand_index) ||
        operand_index >= instruction->operand_count) {
      continue;
    }
    attach_operand_label_symbol(lookup, instruction, operand_index, section_index, candidate->offset,
      relocation->target_section_index, relocation->target_offset);
  }
}

static const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_primary_vector_at(
    const M68kRenderLookup *lookup, const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index,
    uint32_t helper_offset, unsigned depth) {
  const M68kDecodeSectionIR *section;
  M68kRenderPlatformState state;
  uint32_t cursor;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK ||
      section_index >= decode->section_count || depth > 4U) {
    return NULL;
  }
  section = &decode->sections[section_index];
  if (!accepted_start_at(section, accepted_start[section_index], helper_offset)) return NULL;
  memset(&state, 0, sizeof(state));
  cursor = helper_offset;
  while (cursor < section->size && cursor - helper_offset < 256U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const AmigaOsLibraryVectorInfo *vector;
    const AmigaOsLibraryVectorInfo *nested_vector;
    if (!accepted_start_at(section, accepted_start[section_index], cursor)) break;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index, cursor);
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
    vector = attach_amiga_lvo_symbol_if_known(&state, &instruction);
    if (vector != NULL) return vector;
    vector = attach_amiga_lvo_immediate_if_known(lookup, section, accepted_start[section_index], candidate,
      &instruction);
    if (vector != NULL) return vector;
    vector = resolve_amiga_indexed_wrapper_call_vector(lookup, &state, section, candidate);
    if (vector != NULL) return vector;
    vector = resolve_amiga_direct_wrapper_call_vector_depth(lookup, decode, accepted_start, section->section_index,
      candidate, depth + 1U);
    if (vector != NULL) return vector;
    nested_vector = resolve_amiga_local_helper_call_vector_depth(lookup, decode, accepted_start,
      section->section_index, candidate, depth + 1U);
    if (nested_vector != NULL) return nested_vector;
    if (candidate_has_call_flow_local(candidate)) {
      return NULL;
    }
    platform_state_update_data_lvo_after_instruction(&state, &instruction);
    platform_state_update_after_instruction(&state, lookup, &instruction);
    if (!candidate_has_local_helper_summary_fallthrough(candidate)) break;
    cursor += candidate->byte_count;
  }
  return NULL;
}

const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_call_vector_depth(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
    const M68kDecodeCandidate *candidate, unsigned depth) {
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U;
  if (depth > 4U || candidate == NULL || !candidate_has_call_flow_local(candidate)) return NULL;
  if (!candidate_direct_control_target(lookup, source_section_index, candidate, &target_section_index, &target_offset))
    return NULL;
  if (target_section_index == source_section_index && target_offset == candidate->offset) return NULL;
  return resolve_amiga_local_helper_primary_vector_at(lookup, decode, accepted_start, target_section_index,
    target_offset, depth);
}

const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_call_vector(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t source_section_index,
    const M68kDecodeCandidate *candidate) {
  return resolve_amiga_local_helper_call_vector_depth(lookup, decode, accepted_start, source_section_index,
    candidate, 0U);
}

int m68k_analysis_render_lookup_run_platform_passes(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, uint8_t **accepted_bytes, M68kPlatformAnalysisPassStats *stats) {
  clock_t start;
  clock_t end;
  clock_t pass_start;
  clock_t typed_stage_start;
  int direct_summaries_ready;
  size_t inferred_summary_count_before_callbacks;
  M68kRenderTypedFlowWorkflow typed_flow_workflow;
  (void)accepted_bytes;
  memset(&typed_flow_workflow, 0, sizeof(typed_flow_workflow));
  pass_start = clock();
  if (stats != NULL) memset(stats, 0, sizeof(*stats));
  start = clock();
  if (render_lookup_seed_policy_rsset_layout_regions(lookup) != 0) return -1;
  if (render_lookup_infer_global_base_slots(lookup, decode, accepted_start) != 0) return -1;
  end = clock();
  if (stats != NULL) stats->base_slot_seconds = elapsed_seconds_local(start, end);
  start = clock();
  if (render_lookup_infer_amiga_platform_derived_summaries(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_infer_amiga_recovered_function_args(lookup, decode, accepted_start) != 0) return -1;
  end = clock();
  if (stats != NULL) stats->call_summary_seconds = elapsed_seconds_local(start, end);
  start = clock();
  if (render_lookup_analyze_amiga_app_state_slots(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_seed_policy_rsset_use_site_app_refs(lookup, decode, accepted_start) != 0) return -1;
  end = clock();
  if (stats != NULL) stats->app_slot_seconds = elapsed_seconds_local(start, end);
  start = clock();
  /* Discover the complete direct-call graph before any typed transfer.  The
   * solver then owns recursive edges; typed flow only consumes its facts. */
  typed_stage_start = clock();
  if (render_lookup_collect_inferred_direct_function_summaries(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_solve_inferred_direct_function_summaries(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_collect_platform_call_thunks(lookup, decode, accepted_start) != 0) return -1;
  /* A direct inferred summary guarantees the post-callback solve below. Its
   * final access walk supersedes the provisional one, so the discovery solve
   * need only converge callback identities and storage facts. */
  if (stats != NULL) stats->typed_summary_seconds = elapsed_seconds_local(typed_stage_start, clock());
  typed_stage_start = clock();
  direct_summaries_ready = lookup->inferred_function_summary_count != 0U;
  if (typed_flow_workflow_prepare(&typed_flow_workflow, lookup, decode, accepted_start) != 0) return -1;
  if (stats != NULL) stats->typed_graph_seconds = elapsed_seconds_local(typed_stage_start, clock());
  typed_stage_start = clock();
  if (render_lookup_analyze_amiga_typed_refs(lookup, decode, accepted_start, &typed_flow_workflow,
      !direct_summaries_ready) != 0) goto typed_flow_fail;
  if (stats != NULL) stats->typed_flow_seconds = elapsed_seconds_local(typed_stage_start, clock());
  typed_stage_start = clock();
  inferred_summary_count_before_callbacks = lookup->inferred_function_summary_count;
  if (render_lookup_collect_inferred_callback_table_function_summaries(lookup, decode, accepted_start) != 0)
    goto typed_flow_fail;
  lookup->inferred_function_summaries_ready = 1U;
  if (lookup->inferred_function_summary_count != 0U) {
    if (lookup->inferred_function_summary_count != inferred_summary_count_before_callbacks) {
      if (render_lookup_analyze_amiga_typed_refs(lookup, decode, accepted_start, &typed_flow_workflow, 1) != 0)
        goto typed_flow_fail;
    } else if (direct_summaries_ready != 0 &&
        typed_flow_record_final_accesses(lookup, decode, accepted_start, &typed_flow_workflow) != 0) {
      goto typed_flow_fail;
    }
  }
  if (typed_flow_enable_call_inputs(lookup, decode, accepted_start, &typed_flow_workflow) != 0 ||
      typed_flow_solve_call_inputs(lookup, decode, accepted_start, &typed_flow_workflow) != 0)
    goto typed_flow_fail;
  if (render_lookup_record_typed_app_slot_pointer_accesses(lookup, decode, accepted_start) != 0) goto typed_flow_fail;
  typed_flow_filter_nonapp_fallbacks(lookup, decode, &typed_flow_workflow);
  /* Loop proof deliberately borrows node value storage after projection. */
  if (typed_flow_record_app_loop_ranges(lookup, decode, accepted_start, &typed_flow_workflow) != 0) goto typed_flow_fail;
  typed_flow_workflow_destroy(&typed_flow_workflow);
  end = clock();
  if (stats != NULL) stats->typed_ref_seconds = elapsed_seconds_local(start, end);
  if (stats != NULL) stats->typed_callback_seconds = elapsed_seconds_local(typed_stage_start, end);
  start = clock();
  if (render_lookup_infer_bootblock_runtime_copies(lookup, decode, accepted_start) != 0) return -1;
  end = clock();
  if (stats != NULL) stats->call_comment_seconds = elapsed_seconds_local(start, end);
  start = clock();
  end = clock();
  if (stats != NULL) stats->runtime_data_seconds = elapsed_seconds_local(start, end);
  start = clock();
  end = clock();
  if (stats != NULL) stats->hardware_data_seconds = elapsed_seconds_local(start, end);
  start = clock();
  end = clock();
  if (stats != NULL) {
    stats->generic_data_seconds = elapsed_seconds_local(start, end);
    stats->pass_seconds = elapsed_seconds_local(pass_start, end);
  }
  return 0;

typed_flow_fail:
  typed_flow_workflow_destroy(&typed_flow_workflow);
  return -1;
}

static void source_analysis_build_stats_record_platform_vector(M68kSourceAnalysisBuildStats *stats,
    const AmigaOsLibraryVectorInfo *vector) {
  if (stats == NULL || vector == NULL) return;
  ++stats->platform_call_count;
  stats->platform_effect_count += vector->input_count;
  if (vector->output.reg_kind != AMIGA_OS_REGISTER_NONE ||
      vector->output.output_id != AMIGA_OS_SYMBOL_ID_NONE ||
      vector->output.type_id != AMIGA_OS_TYPE_ID_NONE ||
      vector->output.struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    ++stats->platform_effect_count;
  }
}

static int analysis_record_platform_vector_effects(
    M68kSectionAnalysisIR *section_analysis, uint32_t offset, const AmigaOsLibraryVectorInfo *vector) {
  const AmigaOsCallOutputInfo *output;
  const char *output_symbol_name;
  const char *output_type_name;
  const char *output_semantic_kind;
  const char *output_value_domain_name;
  if (section_analysis == NULL || vector == NULL) return 0;
  output = &vector->output;
  if (output->reg_kind == AMIGA_OS_REGISTER_NONE || output->reg_index >= 8U) return 0;
  output_symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, output->output_id);
  output_type_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, output->struct_id);
  if (output_type_name == NULL || output_type_name[0] == '\0')
    output_type_name = amiga_os_name(M68K_PLATFORM_NAME_TYPE, output->type_id);
  output_semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, output->semantic_kind_id);
  output_value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, output->value_domain_id);
  if ((output_symbol_name == NULL || output_symbol_name[0] == '\0') &&
      (output_type_name == NULL || output_type_name[0] == '\0') &&
      (output_semantic_kind == NULL || output_semantic_kind[0] == '\0') &&
      (output_value_domain_name == NULL || output_value_domain_name[0] == '\0')) {
    return 0;
  }
  if (m68k_ir_section_analysis_append_recovered_platform_effect(section_analysis,
      M68K_PLATFORM_BACKEND_AMIGA_HUNK, offset, M68K_PLATFORM_EFFECT_SET_TYPED_REG,
      output->reg_kind, output->reg_index, INT16_MIN, INT16_MIN, NULL,
      output_symbol_name, output_type_name, output_semantic_kind, output_value_domain_name, 0U, 0) != 0) {
    return -1;
  }
  return 0;
}

static int analysis_record_platform_vector_call(M68kSourceAnalysisBuildStats *stats,
    const M68kRenderLookup *lookup, M68kSectionAnalysisIR *section_analysis, uint32_t offset, uint8_t kind,
    uint8_t note_kind, const AmigaOsLibraryVectorInfo *vector) {
  const char *symbol_name, *library_name, *device_name;
  const char *note_symbol_name = NULL, *available_since = NULL, *note_base_name = NULL;
  if (vector == NULL) return 0;
  source_analysis_build_stats_record_platform_vector(stats, vector);
  if (section_analysis == NULL) return 0;
  symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, vector->lvo_symbol_id);
  if (symbol_name == NULL || symbol_name[0] == '\0') return 0;
  if (note_kind != M68K_PLATFORM_CALL_NOTE_NONE) {
    note_symbol_name = symbol_name;
    symbol_name = NULL;
    library_name = platform_facts_v2_library_name_for_id(M68K_PLATFORM_BACKEND_AMIGA_HUNK, vector->library_id);
    note_base_name = render_lookup_amiga_library_base_name_for_library_name(library_name);
  }
  available_since = vector->available_since_raw;
  if (m68k_ir_section_analysis_append_recovered_platform_call(section_analysis,
      M68K_PLATFORM_BACKEND_AMIGA_HUNK, offset, kind, symbol_name, note_kind,
      note_base_name, note_symbol_name, 0U, INT16_MIN, INT16_MIN, 0U, 0U, 0U,
      available_since != NULL && available_since[0] != '\0' ? available_since : NULL,
      vector->fd_version != NULL && vector->fd_version[0] != '\0' ? vector->fd_version : NULL) != 0) {
    return -1;
  }
  device_name = render_lookup_device_name_for_call(lookup, section_analysis->section_index, offset);
  if (device_name != NULL &&
      m68k_ir_section_analysis_set_recovered_platform_call_device_name(section_analysis, offset, kind,
        device_name) != 0) {
    return -1;
  }
  return analysis_record_platform_vector_effects(section_analysis, offset, vector);
}

static int analysis_record_facts_v2_platform_call(M68kSourceAnalysisBuildStats *stats,
    M68kSectionAnalysisIR *section_analysis, uint32_t offset,
    const PlatformFactsV2ResolvedCall *call_info) {
  if (call_info == NULL || call_info->platform_kind == 0U) return 0;
  if (stats != NULL) ++stats->platform_call_count;
  if (section_analysis == NULL) return 0;
  if (m68k_ir_section_analysis_append_recovered_platform_call(section_analysis, call_info->platform_kind,
      offset, call_info->kind, NULL, call_info->note_kind,
      call_info->note_base_name[0] != '\0' ? call_info->note_base_name : NULL,
      call_info->note_symbol_name[0] != '\0' ? call_info->note_symbol_name : NULL,
      0U, INT16_MIN, INT16_MIN, call_info->note_stack_cleanup_known,
      call_info->note_stack_cleanup_bytes, call_info->note_return_kind, NULL, NULL) != 0) {
    return -1;
  }
  return 0;
}

static int mac_instruction_stack_argument_operand(const M68kInstructionIR *instruction,
    const M68kOperandIR **out_operand) {
  if (out_operand != NULL) *out_operand = NULL;
  if (instruction == NULL || out_operand == NULL) return 0;
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_PEA && instruction->operand_count == 1U) {
    *out_operand = &instruction->operands[0];
    return 1;
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE && instruction->size_suffix == 'l' &&
      instruction->operand_count == 2U && instruction->operands[1].kind == M68K_ASM_OPERAND_EA &&
      instruction->operands[1].value.ea_mode == 4U && instruction->operands[1].value.ea_reg == 7U) {
    *out_operand = &instruction->operands[0];
    return 1;
  }
  return 0;
}

typedef struct MacStackArgumentOperand {
  uint32_t offset;
  uint8_t source_reg_kind;
  uint8_t source_reg_index;
  int16_t source_displacement;
  uint8_t is_output_pointer;
  char pointee_type_name[64];
  char field_name[64];
} MacStackArgumentOperand;

static int mac_stack_argument_source_from_operand(const M68kOperandIR *operand, MacStackArgumentOperand *out_arg) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (out_arg != NULL) memset(out_arg, 0, sizeof(*out_arg));
  if (operand == NULL || out_arg == NULL) return 0;
  if (operand_is_address_memory_local(operand, &base_reg, &displacement) && base_reg < 8U) {
    out_arg->source_reg_kind = 2U;
    out_arg->source_reg_index = base_reg;
    out_arg->source_displacement = displacement;
    return 1;
  }
  return 0;
}

static const char *analysis_trim_left(const char *text) {
  if (text == NULL) return NULL;
  while (*text == ' ' || *text == '\t') ++text;
  return text;
}

static void analysis_trim_right_in_place(char *text) {
  size_t length;
  if (text == NULL) return;
  length = strlen(text);
  while (length != 0U && (text[length - 1U] == ' ' || text[length - 1U] == '\t')) {
    text[--length] = '\0';
  }
}

static uint16_t mac_instruction_access_size(const M68kInstructionIR *instruction) {
  if (instruction == NULL) return 0U;
  if (instruction->size_suffix == 'b') return 1U;
  if (instruction->size_suffix == 'w') return 2U;
  if (instruction->size_suffix == 'l') return 4U;
  return 0U;
}

static int mac_output_pointer_pointee_type(const MacOsCallParameterInfo *param, char *out_type,
    size_t out_type_size) {
  const char *type_name;
  const char *star;
  size_t length;
  if (out_type != NULL && out_type_size != 0U) out_type[0] = '\0';
  if (param == NULL || param->direction == NULL || strcmp(param->direction, "output_or_inout_pointer") != 0 ||
      param->type_name == NULL || out_type == NULL || out_type_size == 0U) {
    return 0;
  }
  star = strrchr(param->type_name, '*');
  if (star == NULL || star == param->type_name) return 0;
  type_name = analysis_trim_left(param->type_name);
  length = (size_t)(star - type_name);
  if (length >= out_type_size) length = out_type_size - 1U;
  memcpy(out_type, type_name, length);
  out_type[length] = '\0';
  analysis_trim_right_in_place(out_type);
  return out_type[0] != '\0';
}

static int mac_operand_matches_stack_arg_source(const M68kOperandIR *operand, const MacStackArgumentOperand *arg,
    uint8_t *out_base_reg, int16_t *out_displacement) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (out_base_reg != NULL) *out_base_reg = 0U;
  if (out_displacement != NULL) *out_displacement = 0;
  if (operand == NULL || arg == NULL || arg->source_reg_kind != 2U ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement)) {
    return 0;
  }
  if (base_reg != arg->source_reg_index || displacement != arg->source_displacement) return 0;
  if (out_base_reg != NULL) *out_base_reg = base_reg;
  if (out_displacement != NULL) *out_displacement = displacement;
  return 1;
}

static int analysis_record_mac_output_pointer_local_read_facts(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t call_offset,
    M68kSectionAnalysisIR *section_analysis, const MacStackArgumentOperand *args, size_t arg_count) {
  uint32_t cursor;
  if (section == NULL || accepted_start == NULL || section_analysis == NULL || args == NULL || arg_count == 0U) {
    return 0;
  }
  cursor = call_offset + 2U;
  while (cursor < section->size && cursor - call_offset <= 96U) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const M68kSimFormMetadata *metadata;
    size_t operand_index;
    if (!accepted_start_at(section, accepted_start, cursor)) break;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U) break;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    metadata = m68k_sim_metadata_for_instruction(&instruction);
    if (metadata == NULL) break;
    for (operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U; ++operand_index) {
      size_t arg_index;
      uint8_t base_reg = 0U;
      int16_t displacement = 0;
      if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_MEMORY_READ) continue;
      for (arg_index = 0U; arg_index < arg_count; ++arg_index) {
        const MacStackArgumentOperand *arg = &args[arg_index];
        uint16_t access_size = mac_instruction_access_size(&instruction);
        if (!arg->is_output_pointer ||
            !mac_operand_matches_stack_arg_source(&instruction.operands[operand_index], arg, &base_reg,
              &displacement)) {
          continue;
        }
        if (m68k_ir_section_analysis_append_recovered_platform_typed_access(section_analysis,
            M68K_PLATFORM_BACKEND_MACOS, candidate->offset, (uint8_t)operand_index, base_reg, displacement, 0,
            0, 0U, access_size, arg->pointee_type_name, arg->pointee_type_name, arg->field_name,
            "", 0U, 0U, M68K_PLATFORM_TYPE_PROVENANCE_API_OUTPUT, 0U, section->section_index, call_offset, NULL) != 0) {
          return -1;
        }
        {
          size_t dest_index;
          for (dest_index = 0U; dest_index < instruction.operand_count && dest_index < 4U; ++dest_index) {
            uint8_t dest_base_reg = 0U;
            int16_t dest_displacement = 0;
            if (metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_MEMORY_WRITE ||
                !operand_is_address_memory_local(&instruction.operands[dest_index], &dest_base_reg,
                  &dest_displacement)) {
              continue;
            }
            if (m68k_ir_section_analysis_append_recovered_platform_typed_access(section_analysis,
                M68K_PLATFORM_BACKEND_MACOS, candidate->offset, (uint8_t)dest_index, dest_base_reg,
                dest_displacement, 0, 0, 0U, access_size, arg->pointee_type_name, arg->pointee_type_name,
                arg->field_name, "", 0U, 0U, M68K_PLATFORM_TYPE_PROVENANCE_API_OUTPUT, 0U, section->section_index,
                call_offset, NULL) != 0) {
              return -1;
            }
          }
        }
      }
    }
    if (candidate_has_call_flow_local(candidate) || candidate_has_non_call_control_target(candidate)) break;
    cursor += candidate->byte_count;
  }
  return 0;
}

static int analysis_record_mac_call_stack_arg_facts(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, uint32_t block_start,
    uint32_t call_offset, M68kSectionAnalysisIR *section_analysis,
    const PlatformFactsV2ResolvedCall *call_info) {
  const MacOsCallInfo *mac_call;
  MacStackArgumentOperand args[16];
  size_t arg_count = 0U;
  uint32_t cursor;
  if (lookup == NULL || lookup->object == NULL || section == NULL || accepted_start == NULL ||
      section_analysis == NULL || call_info == NULL) {
    return 0;
  }
  if (lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_MACOS ||
      call_info->note_kind != M68K_PLATFORM_CALL_NOTE_DIRECT_OS_CALL ||
      call_info->note_symbol_name[0] == '\0') {
    return 0;
  }
  mac_call = mac_os_find_call_by_name(call_info->note_symbol_name);
  if (mac_call == NULL || mac_call->parameter_count == 0U || mac_call->parameter_count > 16U) return 0;
  memset(args, 0, sizeof(args));
  cursor = block_start < call_offset ? block_start : (call_offset > 48U ? call_offset - 48U : 0U);
  while (cursor < call_offset && cursor < section->size) {
    const M68kDecodeCandidate *candidate;
    M68kInstructionIR instruction;
    const M68kOperandIR *arg_operand = NULL;
    if (!accepted_start_at(section, accepted_start, cursor)) break;
    candidate = find_candidate_at_offset_local(section, cursor);
    if (candidate == NULL || candidate->byte_count == 0U || cursor + candidate->byte_count > call_offset) break;
    if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) break;
    if (mac_instruction_stack_argument_operand(&instruction, &arg_operand)) {
      if (arg_count >= 16U) {
        arg_count = 0U;
      } else {
        (void)mac_stack_argument_source_from_operand(arg_operand, &args[arg_count]);
        args[arg_count].offset = cursor;
        ++arg_count;
      }
    } else if (candidate_has_call_flow_local(candidate) || candidate_has_non_call_control_target(candidate)) {
      arg_count = 0U;
    }
    cursor += candidate->byte_count;
  }
  if (cursor != call_offset || arg_count < mac_call->parameter_count) return 0;
  {
    uint16_t param_index;
    size_t first_arg = arg_count - mac_call->parameter_count;
    for (param_index = 0U; param_index < mac_call->parameter_count; ++param_index) {
      const MacOsCallParameterInfo *param = mac_os_call_parameter(mac_call, param_index);
      const MacStackArgumentOperand *arg = &args[first_arg + param_index];
      uint16_t stack_offset = (uint16_t)((mac_call->parameter_count - param_index) * 4U);
      if (param == NULL) continue;
      if (mac_output_pointer_pointee_type(param, args[first_arg + param_index].pointee_type_name,
          sizeof(args[first_arg + param_index].pointee_type_name))) {
        args[first_arg + param_index].is_output_pointer = 1U;
        snprintf(args[first_arg + param_index].field_name, sizeof(args[first_arg + param_index].field_name),
          "%s", param->name != NULL ? param->name : "");
      }
      if (m68k_ir_section_analysis_append_recovered_function_arg(section_analysis, M68K_PLATFORM_BACKEND_MACOS,
          call_offset, stack_offset, 0U, 0U, mac_call->c_name, param->name, param->type_name,
          param->direction, NULL, 0U, 0, arg->source_reg_kind != 0U, arg->offset, arg->source_reg_kind,
          arg->source_reg_index, arg->source_displacement) != 0) {
        return -1;
      }
      if (param->direction != NULL && strcmp(param->direction, "input_value") == 0 &&
          param->type_name != NULL && param->type_name[0] != '\0' && arg->source_reg_kind == 2U) {
        if (m68k_ir_section_analysis_append_recovered_platform_typed_access(section_analysis,
            M68K_PLATFORM_BACKEND_MACOS, arg->offset, 0U, arg->source_reg_index, arg->source_displacement, 0,
            0, 0U, 0U, param->type_name, param->type_name, param->name != NULL ? param->name : "",
            "", 0U, 0U, M68K_PLATFORM_TYPE_PROVENANCE_API_INPUT, 0U, section->section_index, call_offset, NULL) != 0) {
          return -1;
        }
      }
    }
    return analysis_record_mac_output_pointer_local_read_facts(section, accepted_start, call_offset,
      section_analysis, args + first_arg, mac_call->parameter_count);
  }
}

static int analysis_record_platform_trap_call_facts(M68kSourceAnalysisBuildStats *stats,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *candidate, M68kSectionAnalysisIR *section_analysis) {
  PlatformFactsV2ResolvedCall call_info;
  uint32_t block_start;
  if (lookup == NULL || lookup->object == NULL || section == NULL || candidate == NULL)
    return 0;
  block_start = lookup_code_block_start_before_or_at(lookup, section->section_index, candidate->offset);
  if (!platform_facts_v2_resolve_trap_call(lookup->object->platform_backend_kind, section, accepted_start,
      block_start, candidate->offset, &call_info)) {
    return 0;
  }
  if (analysis_record_facts_v2_platform_call(stats, section_analysis, candidate->offset, &call_info) != 0)
    return -1;
  if (analysis_record_mac_call_stack_arg_facts(lookup, section, accepted_start, block_start,
      candidate->offset, section_analysis, &call_info) < 0) {
    return -1;
  }
  return 1;
}

static int analysis_record_platform_stack_cleanup_call_facts(M68kSourceAnalysisBuildStats *stats,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *candidate, M68kSectionAnalysisIR *section_analysis) {
  M68kInstructionIR instruction;
  PlatformFactsV2ResolvedCall call_info;
  uint32_t block_start;
  if (lookup == NULL || lookup->object == NULL || section == NULL || accepted_start == NULL || candidate == NULL) {
    return 0;
  }
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  block_start = lookup_code_block_start_before_or_at(lookup, section->section_index, candidate->offset);
  if (!platform_facts_v2_resolve_stack_cleanup_call(lookup->object->platform_backend_kind, section,
      accepted_start, block_start, candidate->offset, &instruction, &call_info)) {
    return 0;
  }
  if (analysis_record_facts_v2_platform_call(stats, section_analysis, candidate->offset, &call_info) != 0)
    return -1;
  return 1;
}

static int analysis_record_amiga_instruction_platform_call_facts(M68kSourceAnalysisBuildStats *stats,
    M68kRenderLookup *lookup, M68kRenderPlatformState *platform_state, const M68kDecodeIR *decode,
    uint8_t **accepted_start_all, const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    const M68kDecodeCandidate *candidate, M68kSectionAnalysisIR *section_analysis) {
  M68kInstructionIR instruction;
  M68kRenderAmigaVectorResolution vector_resolution;
  if (lookup == NULL || lookup->object == NULL || platform_state == NULL || decode == NULL ||
      accepted_start_all == NULL || section == NULL || accepted_start == NULL || candidate == NULL) {
    return 0;
  }
  if (lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) return 0;
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
  m68k_analysis_render_lookup_resolve_amiga_instruction_platform_vectors(lookup, platform_state, decode,
    accepted_start_all, section, accepted_start, candidate, &instruction, &vector_resolution);
  if (vector_resolution.chosen_vector == NULL) return 0;
  return analysis_record_platform_vector_call(stats, lookup, section_analysis, candidate->offset,
    vector_resolution.chosen_kind, vector_resolution.chosen_note_kind, vector_resolution.chosen_vector);
}

static void analysis_platform_state_update_known_library_load_after_candidate(M68kRenderPlatformState *platform_state,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate) {
  uint8_t loaded_address_reg = 0U;
  char loaded_library_name[64];
  if (platform_state == NULL || lookup == NULL || section == NULL || candidate == NULL) return;
  if (candidate_lea_known_amiga_name_to_address_reg(lookup, section, candidate, &loaded_address_reg,
      loaded_library_name, sizeof(loaded_library_name))) {
    platform_state_set_register_library(platform_state, loaded_address_reg, loaded_library_name);
  }
}

static int analysis_advance_platform_state_after_candidate(M68kRenderLookup *lookup,
    M68kRenderPlatformState *platform_state, const M68kDecodeIR *decode, uint8_t **accepted_start_all,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, const M68kDecodeCandidate *candidate) {
  M68kInstructionIR instruction;
  M68kRenderAmigaVectorResolution vector_resolution;
  if (lookup == NULL || lookup->object == NULL || platform_state == NULL || decode == NULL ||
      accepted_start_all == NULL || section == NULL || accepted_start == NULL || candidate == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) return 0;
  attach_known_instruction_relocations(lookup, section->section_index, candidate, &instruction);
  m68k_analysis_render_lookup_resolve_amiga_instruction_platform_vectors(lookup, platform_state, decode,
    accepted_start_all, section, accepted_start, candidate, &instruction, &vector_resolution);
  platform_state_update_data_lvo_after_instruction(platform_state, &instruction);
  platform_state_update_after_instruction(platform_state, lookup, &instruction);
  analysis_platform_state_update_known_library_load_after_candidate(platform_state, lookup, section, candidate);
  if (instruction_has_call_flow_local(&instruction)) {
    platform_state_note_call_result_after_instruction(platform_state, &instruction, vector_resolution.chosen_vector);
  }
  return 0;
}

int m68k_analysis_render_lookup_append_platform_call_facts_for_section(M68kSourceAnalysisBuildStats *stats,
    M68kRenderLookup *lookup, M68kRenderPlatformState *platform_state, const M68kDecodeIR *decode,
    const M68kAnalysisPolicy *policy, uint8_t **accepted_start_all, size_t section_array_index,
    const M68kDecodeSectionIR *section, M68kSectionAnalysisIR *section_analysis) {
  uint32_t offset = 0U;
  uint32_t render_extent;
  if (lookup == NULL || lookup->object == NULL || decode == NULL ||
      platform_state == NULL || accepted_start_all == NULL || section == NULL ||
      section_array_index >= decode->section_count) {
    return 0;
  }
  render_extent = render_section_extent(section);
  while (offset < render_extent) {
    platform_state_apply_policy_register_seeds(platform_state, policy, section->section_index, offset);
    if (accepted_start_at(section, accepted_start_all[section_array_index], offset)) {
      const M68kDecodeCandidate *candidate = m68k_decode_ir_find_candidate_at_offset(section, offset);
      if (candidate == NULL || candidate->byte_count == 0U) {
        PlatformFactsV2ResolvedCall call_info;
        uint16_t opcode = section->data != NULL && offset + 2U <= section->size
          ? m68k_read_u16be(section->data + offset) : 0U;
        if (platform_facts_v2_resolve_opcode_call(lookup->object->platform_backend_kind, opcode, &call_info) &&
            offset + 2U <= render_extent) {
          if (analysis_record_facts_v2_platform_call(stats, section_analysis, offset, &call_info) != 0)
            return -1;
          if (analysis_record_mac_call_stack_arg_facts(lookup, section,
              accepted_start_all[section_array_index],
              lookup_code_block_start_before_or_at(lookup, section->section_index, offset), offset,
              section_analysis, &call_info) < 0) {
            return -1;
          }
          offset += 2U;
          continue;
        }
        return -1;
      }
      if (analysis_record_platform_trap_call_facts(stats, lookup, section, accepted_start_all[section_array_index],
          candidate, section_analysis) < 0) {
        return -1;
      }
      if (analysis_record_platform_stack_cleanup_call_facts(stats, lookup, section,
          accepted_start_all[section_array_index], candidate, section_analysis) < 0) {
        return -1;
      }
      if (analysis_record_amiga_instruction_platform_call_facts(stats, lookup, platform_state, decode,
          accepted_start_all, section, accepted_start_all[section_array_index], candidate, section_analysis) < 0) {
        return -1;
      }
      if (analysis_advance_platform_state_after_candidate(lookup, platform_state, decode, accepted_start_all, section,
          accepted_start_all[section_array_index], candidate) < 0) {
        return -1;
      }
      offset += candidate->byte_count;
      continue;
    }
    ++offset;
  }
  return 0;
}

static int append_base_layout_fields_from_slots(M68kSourceAnalysisIR *source_analysis,
    const M68kBaseLayoutSlot *slots, size_t slot_count) {
  size_t index;
  if (source_analysis == NULL || slots == NULL) return 0;
  for (index = 0U; index < slot_count; ++index) {
    M68kBaseLayoutFieldIR field;
    memset(&field, 0, sizeof(field));
    field.layout_name = (char *)slots[index].layout_name;
    field.base_symbol = (char *)slots[index].base_symbol;
    field.sizeof_symbol = (char *)slots[index].sizeof_symbol;
    field.symbol = (char *)slots[index].name;
    field.owner_struct_name = slots[index].owner_struct_name[0] != '\0' ?
      (char *)slots[index].owner_struct_name : NULL;
    field.offset = (uint32_t)slots[index].displacement;
    field.size = (uint32_t)slots[index].size;
    field.alias = slots[index].alias;
    field.has_alias_of = slots[index].has_alias_of;
    field.alias_of_symbol = slots[index].has_alias_of ? (char *)slots[index].alias_of_name : NULL;
    field.alias_of_offset = (uint32_t)slots[index].alias_of_displacement;
    field.source_kind = slots[index].source_kind;
    field.value_kind = slots[index].value_kind;
    field.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
    field.conflicted = 0U;
    field.layout_kind = slots[index].layout_kind;
    field.base_kind = slots[index].base_kind;
    field.has_source = slots[index].has_source;
    field.source_section_index = slots[index].source_section_index;
    field.source_offset = slots[index].source_offset;
    if (m68k_ir_source_analysis_append_base_layout_field(source_analysis, &field) != 0) return -1;
  }
  return 0;
}

int m68k_analysis_render_lookup_append_base_layout_fields(Arena *scratch_arena,
    const M68kRenderLookup *lookup, const M68kDecodeIR *decode, M68kSourceAnalysisIR *source_analysis) {
  ArenaMark scratch_mark;
  M68kBaseLayoutSlot *slots = NULL;
  M68kBaseLayoutGroup *layouts = NULL;
  size_t slot_capacity;
  size_t slot_count = 0U;
  int32_t base_offset = 0, app_sizeof_value = 0;
  int has_app_sizeof_value = 0;
  int has_resident_context = 0;
  size_t layout_count;
  int result = -1;
  if (source_analysis == NULL) return 0;
  if (scratch_arena == NULL || lookup == NULL) return -1;
  slot_capacity = base_layout_slot_capacity_for_lookup(lookup);
  scratch_mark = arena_mark(scratch_arena);
  slots = (M68kBaseLayoutSlot *)arena_calloc(scratch_arena, slot_capacity, sizeof(*slots));
  layouts = (M68kBaseLayoutGroup *)arena_calloc(scratch_arena, slot_capacity, sizeof(*layouts));
  if (slots == NULL || layouts == NULL) goto cleanup;
  if (base_layout_collect_slots(lookup, decode, slots, slot_capacity, &slot_count,
      &has_resident_context, &has_app_sizeof_value, &base_offset, &app_sizeof_value) != 0) {
    goto cleanup;
  }
  if (slot_count == 0U) {
    result = 0;
    goto cleanup;
  }
  layout_count = base_layout_prepare_groups(slots, slot_count, layouts, slot_capacity, base_offset,
    has_resident_context, has_app_sizeof_value, app_sizeof_value);
  if (layout_count == SIZE_MAX) goto cleanup;
  result = append_base_layout_fields_from_slots(source_analysis, slots, slot_count);
cleanup:
  arena_rewind(scratch_arena, scratch_mark);
  return result;
}

static int append_manual_data_references_for_section(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, M68kSectionAnalysisIR *section) {
  uint16_t index;
  if (lookup->policy == NULL) return 0;
  if (lookup->policy->manual_data_reference_count > M68K_ANALYSIS_MANUAL_DATA_REFERENCE_LIMIT) return -1;
  for (index = 0U; index < lookup->policy->manual_data_reference_count; ++index) {
    const M68kAnalysisManualDataReference *manual = &lookup->policy->manual_data_references[index];
    M68kDataReferenceIR ref;
    const M68kDecodeSectionIR *source;
    uint32_t cursor;
    uint32_t scale = manual->is_range ? manual->value_scale : 1U;
    uint8_t is_signed = manual->is_range ? manual->raw_value_signed : 1U;
    if (manual->section_index != section->section_index) continue;
    if (manual->section_index >= decode->section_count) return -1;
    source = &decode->sections[manual->section_index];
    if (source->data == NULL || manual->size < 2U || (manual->size & 1U) || manual->offset > source->size ||
        manual->size > source->size - manual->offset ||
        m68k_read_u16be(source->data + manual->offset) != manual->raw_value ||
        manual->base_section_index != manual->section_index ||
        manual->target_section_index != manual->section_index ||
        manual->base_offset >= source->size) return -1;
    for (cursor = 0U; cursor < manual->size; cursor += 2U) {
      uint32_t raw = m68k_read_u16be(source->data + manual->offset + cursor);
      int64_t target = (int64_t)manual->base_offset +
        (is_signed ? (int16_t)raw : (int64_t)raw) * scale;
      if (target < 0 || target >= source->size) return -1;
      memset(&ref, 0, sizeof(ref));
      ref.source_kind = M68K_DATA_REFERENCE_SOURCE_MANUAL;
      ref.source_offset = manual->offset + cursor;
      ref.reference_kind = manual->is_range ? M68K_DATA_REFERENCE_KIND_BASE_DISPLACEMENT_RANGE :
        M68K_DATA_REFERENCE_KIND_BASE_DISPLACEMENT;
      ref.raw_value = raw;
      ref.value_scale = scale;
      ref.raw_value_width = 2U;
      ref.raw_value_signed = is_signed;
      ref.has_base = 1U;
      ref.base_section_index = manual->base_section_index;
      ref.base_offset = manual->base_offset;
      ref.target_section_index = manual->target_section_index;
      ref.target_offset = (uint32_t)target;
      ref.target_status = M68K_TABLE_ENTRY_TARGET_STATUS_ACCEPTED_TARGET;
      ref.evidence_flags = M68K_DATA_REFERENCE_EVIDENCE_ACCEPTED_TARGET;
      ref.owner_kind = (char *)manual->owner_kind;
      ref.owner_id = (char *)manual->owner_id;
      ref.owner_layout_id = (char *)manual->owner_layout_id;
      ref.owner_element_offset = manual->owner_element_offset + cursor;
      ref.xref_generation_mode = (char *)manual->xref_generation_mode;
      if (m68k_ir_section_analysis_append_data_reference(section, &ref) != 0) return -1;
    }
  }
  return 0;
}

int m68k_analysis_render_lookup_append_section(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  for (index = 0U; index < lookup->hardware_address_use_count; ++index) {
    const M68kRenderHardwareAddressUse *entry = &lookup->hardware_address_uses[index];
    if (entry->section_index == section_analysis->section_index &&
        m68k_ir_section_analysis_append_platform_address_use(section_analysis, &entry->use) != 0) return -1;
  }
  if (append_manual_data_references_for_section(lookup, decode, section_analysis) != 0) return -1;
  if (append_render_lookup_platform_effects_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_app_slot_refs_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_runtime_views_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_runtime_address_refs_for_section(lookup, decode, section_analysis) != 0) return -1;
  if (append_render_lookup_code_start_refs_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_violations_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_function_summaries_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_platform_derived_summaries_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_recovered_function_args_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_typed_accesses_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_affine_address_evidence_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_unresolved_typed_accesses_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_address_value_consumers_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_bootblock_disk_reads_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_bootblock_runtime_copies_for_section(lookup, section_analysis) != 0) return -1;
  return 0;
}

int m68k_analysis_render_lookup_build_source_analysis(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, const M68kAnalysisPolicy *policy, uint8_t **accepted_start,
    uint8_t **accepted_bytes, M68kSourceAnalysisIR *source_analysis, M68kSourceAnalysisBuildStats *out_stats) {
  M68kRenderPlatformState platform_analysis_state;
  M68kSectionAnalysisIR section_analysis;
  int section_analysis_live = 0;
  Arena *scratch_arena = NULL;
  size_t section_index;
  if (out_stats != NULL) memset(out_stats, 0, sizeof(*out_stats));
  if (lookup == NULL || decode == NULL || accepted_start == NULL ||
      accepted_bytes == NULL || source_analysis == NULL) {
    return -1;
  }
  if (out_stats != NULL) {
    out_stats->platform_base_slot_count = (uint32_t)(lookup->global_base_slot_count + lookup->base_field_slot_count);
  }
  memset(&platform_analysis_state, 0, sizeof(platform_analysis_state));
  memset(&section_analysis, 0, sizeof(section_analysis));
  scratch_arena = arena_create(4096U);
  if (scratch_arena == NULL) return -1;
  if (m68k_analysis_render_lookup_append_base_layout_fields(scratch_arena, lookup, decode, source_analysis) != 0)
    goto fail;
  for (section_index = 0U; section_index < lookup->typed_flow_incomplete_count; ++section_index)
    if (m68k_ir_source_analysis_append_incomplete_analysis(source_analysis,
        &lookup->typed_flow_incomplete[section_index]) != 0) goto fail;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    if (m68k_ir_section_analysis_create(&section_analysis, source_analysis->arena) != 0) goto fail;
    section_analysis_live = 1;
    section_analysis.section_index = section->section_index;
    section_analysis.section_kind = section->kind;
    section_analysis.section_size = section->allocation_size != 0U ? section->allocation_size : section->size;
    if (m68k_ir_section_analysis_set_name(&section_analysis, section->name) != 0 ||
        m68k_ir_section_analysis_set_code_map(&section_analysis, accepted_start[section_index],
          accepted_bytes[section_index], section->size) != 0) {
      goto fail;
    }
    if (m68k_analysis_render_lookup_append_section(lookup, decode, &section_analysis) != 0) goto fail;
    if (m68k_analysis_render_lookup_append_platform_call_facts_for_section(out_stats, lookup, &platform_analysis_state,
        decode, policy, accepted_start, section_index, section, &section_analysis) < 0) {
      goto fail;
    }
    if (m68k_analysis_render_lookup_append_labels_for_section(lookup, section, accepted_start[section_index],
        &section_analysis) != 0) {
      goto fail;
    }
    if (m68k_analysis_render_lookup_append_cfg_for_section(lookup, section, accepted_start[section_index],
        accepted_bytes[section_index], scratch_arena, &section_analysis) != 0) {
      goto fail;
    }
    if (m68k_analysis_render_lookup_append_orphan_code_signals_for_section(lookup, section,
        accepted_start[section_index], accepted_bytes[section_index], &section_analysis) != 0) {
      goto fail;
    }
    if (m68k_ir_source_analysis_append_section(source_analysis, &section_analysis) != 0) goto fail;
    m68k_ir_section_analysis_destroy(&section_analysis);
    section_analysis_live = 0;
  }
  arena_destroy(scratch_arena);
  return 0;
fail:
  if (section_analysis_live) m68k_ir_section_analysis_destroy(&section_analysis);
  arena_destroy(scratch_arena);
  return -1;
}

