#include "m68k_render_lookup_internal.h"
#include "m68k_bitset.h"
#include "m68k_disassembler.h"
#include "generated/mac_os_runtime.h"

#include <time.h>

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

static int analysis_cfg_candidate_has_control_target(const M68kDecodeCandidate *candidate) {
  size_t target_index;
  if (candidate == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_CALL ||
        target->kind == M68K_DECODE_TARGET_JUMP) {
      return 1;
    }
  }
  return 0;
}

static uint8_t analysis_cfg_edge_kind_for_target(const M68kDecodeCandidate *candidate,
    const M68kDecodeTarget *target) {
  M68kInstructionIR instruction;
  const M68kSimFormMetadata *metadata;
  if (target != NULL && target->kind == M68K_DECODE_TARGET_CALL) return M68K_CFG_EDGE_CALL;
  if (target != NULL && target->kind == M68K_DECODE_TARGET_JUMP) return M68K_CFG_EDGE_JUMP;
  metadata = analysis_cfg_candidate_metadata(candidate, &instruction);
  if (metadata != NULL && (metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
      (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && !metadata->flow_conditional))) {
    return M68K_CFG_EDGE_JUMP;
  }
  return M68K_CFG_EDGE_BRANCH;
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
    const uint8_t *accepted_start, const uint8_t *accepted_bytes, uint8_t *block_starts, uint32_t render_extent) {
  uint32_t offset = 0U;
  if (section == NULL || accepted_start == NULL || accepted_bytes == NULL || block_starts == NULL) return -1;
  while (offset < render_extent) {
    const M68kDecodeCandidate *candidate;
    uint32_t next_offset;
    size_t target_index;
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
    for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
      const M68kDecodeTarget *target = &candidate->targets[target_index];
      if ((target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_CALL ||
          target->kind == M68K_DECODE_TARGET_JUMP) && target->has_section &&
          target->section_index == section->section_index && target->offset < render_extent &&
          accepted_start_at(section, accepted_start, target->offset)) {
        block_starts[target->offset] = 1U;
      }
    }
    if (analysis_cfg_candidate_has_control_target(candidate) && render_cfg_candidate_has_fallthrough(candidate) &&
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
  if (analysis_cfg_build_block_start_map(lookup, section, accepted_start, accepted_bytes, block_starts,
      render_extent) != 0) {
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
      size_t target_index;
      int has_control_target;
      int has_fallthrough;
      if (candidate == NULL || candidate->byte_count == 0U || candidate->byte_count > render_extent - cursor) {
        uint32_t platform_opcode_size = analysis_platform_opcode_size_at(lookup, section, cursor);
        if (platform_opcode_size == 0U || platform_opcode_size > render_extent - cursor) goto cleanup;
        cursor += platform_opcode_size;
        continue;
      }
      next_offset = cursor + candidate->byte_count;
      has_control_target = analysis_cfg_candidate_has_control_target(candidate);
      has_fallthrough = render_cfg_candidate_has_fallthrough(candidate);
      for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
        const M68kDecodeTarget *target = &candidate->targets[target_index];
        if ((target->kind == M68K_DECODE_TARGET_BRANCH || target->kind == M68K_DECODE_TARGET_CALL ||
            target->kind == M68K_DECODE_TARGET_JUMP) && target->has_section &&
            target->section_index == section->section_index) {
          if (analysis_cfg_append_edge(section_analysis, section_analysis->block_count, cursor, target->offset,
              analysis_cfg_edge_kind_for_target(candidate, target)) != 0) {
            goto cleanup;
          }
        }
      }
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

static int lookup_label_statement_ref_is_semantic_runtime_data(const M68kRenderLookup *lookup,
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

int lookup_should_emit_label_statement(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_start, size_t section_index, uint32_t offset) {
  if (!lookup_has_renderable_label(lookup, section_index, offset)) return 0;
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

static int analysis_append_object_symbol_origin_for_label(const M68kRenderLookup *lookup,
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
      if (analysis_append_object_symbol_origin_for_label(lookup, section, offset, section_analysis) != 0) return -1;
    }
    if (lookup_has_renderable_label(lookup, section->section_index, render_extent) &&
        m68k_ir_section_analysis_add_label(section_analysis, render_extent) != 0) {
      return -1;
    }
    if (lookup_has_renderable_label(lookup, section->section_index, render_extent) &&
        analysis_append_object_symbol_origin_for_label(lookup, section, render_extent, section_analysis) != 0) {
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

static int analysis_append_object_symbol_origin_for_label(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t offset, M68kSectionAnalysisIR *section_analysis) {
  M68kSymbolOriginIR origin;
  const char *name;
  if (lookup == NULL || section == NULL || section_analysis == NULL) return -1;
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

static const char *amiga_input_type_or_struct_name(const AmigaOsCallInputInfo *input) {
  const char *name;
  if (input == NULL) return NULL;
  if (input->struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, input->struct_id);
    if (name != NULL && name[0] != '\0') return name;
  }
  if (input->type_id != AMIGA_OS_TYPE_ID_NONE) {
    name = amiga_os_name(M68K_PLATFORM_NAME_TYPE, input->type_id);
    if (name != NULL && name[0] != '\0') return name;
  }
  return NULL;
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
static void typed_memory_base_clear(M68kRenderTypedMemoryBaseValue *value);
static int candidate_loads_data_target_to_address_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg);
static int candidate_data_target_for_operand(const M68kDecodeCandidate *candidate, uint32_t operand_index,
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
static int lookup_has_anchor_local(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset);
static int render_lookup_add_auto_string_item(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint32_t span, uint32_t role_flags, uint8_t source_pattern_id);
static const AmigaOsLibraryVectorInfo *resolve_amiga_local_helper_primary_vector_at(const M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, size_t section_index, uint32_t helper_offset,
    unsigned depth);
static int instruction_move_operand_indices_from_metadata(const M68kInstructionIR *instruction,
    size_t *out_source_index, size_t *out_dest_index, const M68kSimFormMetadata **out_metadata);

#define M68K_RENDER_TYPED_FLOW_DEFAULT_NODE_VISIT_LIMIT 2000000U
#define M68K_RENDER_TYPED_FLOW_DEFAULT_ITERATION_LIMIT 64U

static int instruction_stack_delta_for_comment(const M68kInstructionIR *instruction, int32_t *out_delta) {
  size_t operand_index;
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
      operand_is_address_register_local(&instruction->operands[1], 7U)) {
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
      instruction->operand_count == 2U && operand_is_address_register_local(&instruction->operands[1], 7U)) {
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
      operand_is_address_register_local(&instruction->operands[instruction->operand_count - 1U], 7U)) {
    return 0;
  }
  return 1;
}

static int operand_is_stack_displacement_local(const M68kOperandIR *operand, int16_t *out_displacement) {
  uint8_t reg = 0U;
  int16_t displacement = 0;
  if (out_displacement != NULL) *out_displacement = 0;
  if (!operand_is_address_displacement_local(operand, &reg, &displacement) || reg != 7U) return 0;
  if (out_displacement != NULL) *out_displacement = displacement;
  return 1;
}

static const M68kDecodeCandidate *find_previous_accepted_candidate(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t before_offset) {
  uint32_t probe;
  if (section == NULL || accepted_start == NULL || before_offset == 0U) return NULL;
  probe = before_offset;
  while (probe > 0U) {
    --probe;
    if (accepted_start_at(section, accepted_start, probe)) return find_candidate_at_offset_local(section, probe);
  }
  return NULL;
}

static int recovered_function_arg_temp_add(M68kRenderRecoveredFunctionArg *args, size_t *arg_count,
    size_t arg_capacity, size_t section_index, uint32_t function_offset, uint16_t stack_offset,
    uint8_t reg_kind, uint8_t reg_index, const AmigaOsCallInputInfo *input) {
  size_t index;
  if (args == NULL || arg_count == NULL || input == NULL || stack_offset == 0U ||
      reg_kind == 0U || reg_index >= 8U) {
    return 0;
  }
  for (index = 0U; index < *arg_count; ++index) {
    M68kRenderRecoveredFunctionArg *arg = &args[index];
    if (arg->section_index == section_index && arg->function_offset == function_offset &&
        arg->stack_offset == stack_offset && arg->reg_kind == reg_kind && arg->reg_index == reg_index) {
      return arg->input == input ? 0 : -1;
    }
  }
  if (*arg_count >= arg_capacity) return -1;
  memset(&args[*arg_count], 0, sizeof(args[*arg_count]));
  args[*arg_count].section_index = section_index;
  args[*arg_count].function_offset = function_offset;
  args[*arg_count].stack_offset = stack_offset;
  args[*arg_count].reg_kind = reg_kind;
  args[*arg_count].reg_index = reg_index;
  args[*arg_count].input = input;
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
    const AmigaOsCallInputInfo *input;
    if (operand_is_data_register_local(&instruction->operands[1], &reg)) reg_kind = 1U;
    else if (instruction->operands[1].kind == M68K_ASM_OPERAND_AN) {
      reg = (uint8_t)instruction->operands[1].value.reg;
      reg_kind = 2U;
    }
    input = amiga_vector_input_by_register(vector, reg_kind, reg);
    if (input != NULL) {
      return recovered_function_arg_temp_add(args, arg_count, arg_capacity, section_index, function_offset,
        (uint16_t)(displacement - (int16_t)stack_frame_depth), reg_kind, reg, input);
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
      const AmigaOsCallInputInfo *input;
      if ((mask & (1UL << bit)) == 0U) continue;
      reg_kind = bit < 8U ? 1U : 2U;
      reg_index = (uint8_t)(bit < 8U ? bit : bit - 8U);
      input = amiga_vector_input_by_register(vector, reg_kind, reg_index);
      if (input != NULL && recovered_function_arg_temp_add(args, arg_count, arg_capacity, section_index,
          function_offset, stack_offset, reg_kind, reg_index, input) != 0) {
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
        if (render_lookup_add_recovered_function_arg(lookup, args[index].section_index, args[index].function_offset,
            args[index].stack_offset, args[index].reg_kind, args[index].reg_index, args[index].input) != 0) {
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

static int render_lookup_infer_amiga_recovered_local_call_summaries(M68kRenderLookup *lookup,
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
          render_lookup_add_recovered_local_call_summary(lookup, target_section_index, target_offset, vector) != 0) {
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

static void typed_stored_value_clear(M68kRenderTypedStoredValue *value) {
  if (value == NULL) return;
  memset(value, 0, sizeof(*value));
  value->struct_id = AMIGA_OS_STRUCT_ID_NONE;
}

static int typed_stored_value_has_payload(const M68kRenderTypedStoredValue *value) {
  return value != NULL && (value->struct_id != AMIGA_OS_STRUCT_ID_NONE || value->app_address_known != 0U);
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

static int typed_provenances_equal(const M68kRenderTypedProvenance *left,
    const M68kRenderTypedProvenance *right);

static uint8_t typed_provenance_rank(uint8_t kind) {
  switch (kind) {
  case M68K_RENDER_TYPED_PROVENANCE_API_OUTPUT:
  case M68K_RENDER_TYPED_PROVENANCE_API_INPUT:
  case M68K_RENDER_TYPED_PROVENANCE_POLICY_SEED:
    return 70U;
  case M68K_RENDER_TYPED_PROVENANCE_FIELD_POINTER:
  case M68K_RENDER_TYPED_PROVENANCE_FIELD_ADDRESS:
    return 60U;
  case M68K_RENDER_TYPED_PROVENANCE_LOOKUP_STORAGE:
    return 50U;
  case M68K_RENDER_TYPED_PROVENANCE_APP_SLOT:
  case M68K_RENDER_TYPED_PROVENANCE_BASE_SLOT:
  case M68K_RENDER_TYPED_PROVENANCE_STACK_SLOT:
    return 40U;
  case M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT:
    return 30U;
  case M68K_RENDER_TYPED_PROVENANCE_REGISTER_COPY:
    return 10U;
  case M68K_RENDER_TYPED_PROVENANCE_NONE:
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
  if (dest->kind == M68K_RENDER_TYPED_PROVENANCE_NONE) return;
  dest_rank = typed_provenance_rank(dest->kind);
  source_rank = typed_provenance_rank(source->kind);
  if (source_rank > dest_rank) {
    *dest = *source;
  } else if (source_rank == dest_rank) {
    typed_provenance_clear(dest);
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
    left->offset == right->offset;
}

static void typed_state_clear_addr_alias_for_reg(M68kRenderTypedState *state, uint8_t reg_index) {
  uint8_t index;
  if (state == NULL || reg_index >= 8U) return;
  m68k_bitset_u32_clear(&state->addr_reg_alias_known, reg_index);
  state->addr_reg_alias_source[reg_index] = 0U;
  for (index = 0U; index < 8U; ++index) {
    if (m68k_bitset_u32_has(state->addr_reg_alias_known, index) &&
        state->addr_reg_alias_source[index] == reg_index) {
      m68k_bitset_u32_clear(&state->addr_reg_alias_known, index);
      state->addr_reg_alias_source[index] = 0U;
    }
  }
}

static void typed_state_clear_io_request_setup(M68kRenderTypedState *state, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  memset(&state->io_request_setups[reg_index], 0, sizeof(state->io_request_setups[reg_index]));
}

static void typed_state_set_addr_alias(M68kRenderTypedState *state, uint8_t dest_reg, uint8_t source_reg) {
  if (state == NULL || dest_reg >= 8U || source_reg >= 8U || dest_reg == source_reg) return;
  m68k_bitset_u32_set(&state->addr_reg_alias_known, dest_reg);
  state->addr_reg_alias_source[dest_reg] = source_reg;
}

static void typed_state_clear_reg(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == 1U) {
    typed_reg_value_clear(&state->data_regs[reg_index]);
    state->data_app_addr_regs[reg_index].known = 0U;
    state->data_app_addr_regs[reg_index].displacement = 0;
    typed_memory_base_clear(&state->data_memory_base_regs[reg_index]);
  } else if (reg_kind == 2U) {
    typed_reg_value_clear(&state->addr_regs[reg_index]);
    state->app_addr_regs[reg_index].known = 0U;
    state->app_addr_regs[reg_index].displacement = 0;
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
    state->data_regs[reg_index].output = output;
    state->data_regs[reg_index].struct_id = output->struct_id;
    typed_origin_clear(&state->data_regs[reg_index].origin);
    state->data_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
    state->data_app_addr_regs[reg_index].known = 0U;
    state->data_app_addr_regs[reg_index].displacement = 0;
    typed_memory_base_clear(&state->data_memory_base_regs[reg_index]);
  } else if (reg_kind == 2U) {
    state->addr_regs[reg_index].known = 1U;
    state->addr_regs[reg_index].output = output;
    state->addr_regs[reg_index].struct_id = output->struct_id;
    typed_origin_clear(&state->addr_regs[reg_index].origin);
    state->addr_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
    state->app_addr_regs[reg_index].known = 0U;
    state->app_addr_regs[reg_index].displacement = 0;
    typed_memory_base_clear(&state->memory_base_regs[reg_index]);
    typed_state_clear_addr_alias_for_reg(state, reg_index);
  }
}

static void typed_state_set_reg_struct_id(M68kRenderTypedState *state, uint8_t reg_kind, uint8_t reg_index,
    uint16_t struct_id, const M68kRenderTypedProvenance *provenance) {
  if (state == NULL || reg_index >= 8U || struct_id == AMIGA_OS_STRUCT_ID_NONE) return;
  if (reg_kind == 1U) {
    state->data_regs[reg_index].known = 1U;
    state->data_regs[reg_index].output = NULL;
    state->data_regs[reg_index].struct_id = struct_id;
    typed_origin_clear(&state->data_regs[reg_index].origin);
    state->data_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
    state->data_app_addr_regs[reg_index].known = 0U;
    state->data_app_addr_regs[reg_index].displacement = 0;
    typed_memory_base_clear(&state->data_memory_base_regs[reg_index]);
  } else if (reg_kind == 2U) {
    state->addr_regs[reg_index].known = 1U;
    state->addr_regs[reg_index].output = NULL;
    state->addr_regs[reg_index].struct_id = struct_id;
    typed_origin_clear(&state->addr_regs[reg_index].origin);
    state->addr_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
    state->app_addr_regs[reg_index].known = 0U;
    state->app_addr_regs[reg_index].displacement = 0;
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
  char field_expr[96];
} M68kRenderResolvedStructField;

static uint16_t amiga_struct_size_for_struct_id(uint16_t struct_id);
static int render_lookup_add_typed_access_by_names(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
  uint8_t operand_index, uint8_t base_reg, int16_t displacement, uint16_t struct_size,
  const M68kRenderResolvedStructField *field, const M68kRenderTypedProvenance *provenance);
static int render_lookup_add_unresolved_typed_access_by_names(M68kRenderLookup *lookup, size_t section_index,
  uint32_t offset, uint8_t operand_index, uint8_t base_reg, int16_t displacement, const char *root_struct_name,
  uint16_t struct_size, uint8_t classification, uint16_t container_candidate_count,
  const char *container_struct_name, const char *container_field_expr, uint8_t refinement_applied,
  const char *refined_struct_name, const M68kRenderTypedProvenance *provenance);

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

static const char *lookup_policy_struct_name_by_id(const M68kAnalysisPolicy *policy, uint16_t struct_id) {
  const M68kAnalysisCustomStruct *custom_struct;
  const char *platform_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id);
  if (platform_name != NULL && platform_name[0] != '\0') return platform_name;
  custom_struct = lookup_policy_custom_struct_by_id(policy, struct_id);
  return custom_struct != NULL && custom_struct->name[0] != '\0' ? custom_struct->name : NULL;
}

static uint16_t lookup_policy_struct_size_by_id(const M68kAnalysisPolicy *policy, uint16_t struct_id) {
  const M68kAnalysisCustomStruct *custom_struct = lookup_policy_custom_struct_by_id(policy, struct_id);
  if (custom_struct != NULL)
    return custom_struct->size > UINT16_MAX ? UINT16_MAX : (uint16_t)custom_struct->size;
  return amiga_struct_size_for_struct_id(struct_id);
}

static int lookup_policy_resolve_struct_field(const M68kAnalysisPolicy *policy, uint16_t struct_id,
    int16_t displacement, M68kRenderResolvedStructField *out_field) {
  const M68kAnalysisCustomStruct *custom_struct = lookup_policy_custom_struct_by_id(policy, struct_id);
  const char *struct_name;
  if (out_field != NULL) memset(out_field, 0, sizeof(*out_field));
  if (custom_struct != NULL) {
    uint16_t field_index;
    for (field_index = 0U; field_index < custom_struct->field_count &&
         field_index < M68K_ANALYSIS_CUSTOM_STRUCT_FIELD_LIMIT; ++field_index) {
      const M68kAnalysisCustomStructField *field = &custom_struct->fields[field_index];
      if (field->offset != (uint32_t)displacement || field->size == 0U || field->name[0] == '\0') continue;
      if (out_field != NULL) {
        out_field->offset = displacement;
        out_field->size = field->size > UINT16_MAX ? UINT16_MAX : (uint16_t)field->size;
        snprintf(out_field->root_struct_name, sizeof(out_field->root_struct_name), "%s", custom_struct->name);
        snprintf(out_field->owner_struct_name, sizeof(out_field->owner_struct_name), "%s", custom_struct->name);
        snprintf(out_field->field_name, sizeof(out_field->field_name), "%s", field->name);
        snprintf(out_field->field_expr, sizeof(out_field->field_expr), "%s", field->name);
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
    provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_POLICY_SEED, section_index, offset);
    typed_state_set_reg_struct_id(state, seed->reg_kind, seed->reg_index, struct_id, &provenance);
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

static void typed_state_apply_platform_call_clobbers(M68kRenderTypedState *state) {
  uint8_t preserved_data;
  uint8_t preserved_address;
  uint8_t bit;
  if (state == NULL) return;
  preserved_data = amiga_os_calling_convention_preserved_data_mask();
  preserved_address = amiga_os_calling_convention_preserved_address_mask();
  for (bit = 0U; bit < 8U; ++bit) {
    if ((preserved_data & (uint8_t)(1U << bit)) == 0U) typed_state_clear_reg(state, 1U, bit);
    if ((preserved_address & (uint8_t)(1U << bit)) == 0U) typed_state_clear_reg(state, 2U, bit);
  }
}

static void typed_state_set_app_address(M68kRenderTypedState *state, uint8_t reg_index, int16_t displacement,
    uint16_t struct_id, const M68kRenderTypedProvenance *provenance) {
  if (state == NULL || reg_index >= 8U) return;
  state->addr_regs[reg_index].known = struct_id != AMIGA_OS_STRUCT_ID_NONE ? 1U : 0U;
  state->addr_regs[reg_index].output = NULL;
  state->addr_regs[reg_index].struct_id = struct_id;
  typed_origin_clear(&state->addr_regs[reg_index].origin);
  state->addr_regs[reg_index].provenance = provenance != NULL ? *provenance : typed_provenance_make(0U, 0U, 0U);
  state->app_addr_regs[reg_index].known = 1U;
  state->app_addr_regs[reg_index].displacement = displacement;
  typed_memory_base_clear(&state->memory_base_regs[reg_index]);
  typed_state_clear_addr_alias_for_reg(state, reg_index);
}

static void typed_state_set_data_app_address(M68kRenderTypedState *state, uint8_t reg_index, int16_t displacement) {
  if (state == NULL || reg_index >= 8U) return;
  state->data_app_addr_regs[reg_index].known = 1U;
  state->data_app_addr_regs[reg_index].displacement = displacement;
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
  value->known = 1U;
  value->section_index = section_index;
  value->offset = offset;
}

static int typed_state_copy_memory_base(const M68kRenderTypedState *state, const M68kOperandIR *operand,
    M68kRenderTypedMemoryBaseValue *out_value) {
  uint8_t reg = 0U;
  if (out_value != NULL) typed_memory_base_clear(out_value);
  if (state == NULL || operand == NULL || out_value == NULL) return 0;
  if (operand_is_data_register_local(operand, &reg) && reg < 8U && state->data_memory_base_regs[reg].known) {
    *out_value = state->data_memory_base_regs[reg];
    return 1;
  }
  if (operand_address_register_index_local(operand, &reg) && reg < 8U && state->memory_base_regs[reg].known) {
    *out_value = state->memory_base_regs[reg];
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
    int16_t *out_displacement) {
  uint8_t reg = 0U;
  if (out_displacement != NULL) *out_displacement = 0;
  if (state == NULL || operand == NULL || out_displacement == NULL) return 0;
  if (operand_address_register_index_local(operand, &reg) && reg < 8U && state->app_addr_regs[reg].known) {
    *out_displacement = state->app_addr_regs[reg].displacement;
    return 1;
  }
  if (operand_is_data_register_local(operand, &reg) && reg < 8U && state->data_app_addr_regs[reg].known) {
    *out_displacement = state->data_app_addr_regs[reg].displacement;
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
  return value != NULL && value->known != 0U && typed_stored_value_has_payload(value);
}

static M68kRenderTypedStoredValue typed_stored_value_for_operand(const M68kRenderTypedState *state,
    const M68kOperandIR *operand) {
  M68kRenderTypedStoredValue value;
  int16_t app_displacement = 0;
  uint8_t reg = 0U;
  typed_stored_value_clear(&value);
  value.struct_id = typed_state_struct_id_for_operand(state, operand);
  value.output = typed_state_output_for_operand(state, operand, NULL, NULL);
  if (state != NULL && operand_is_data_register_local(operand, &reg))
    value.provenance = state->data_regs[reg].provenance;
  else if (state != NULL && operand_address_register_index_local(operand, &reg))
    value.provenance = state->addr_regs[reg].provenance;
  if (typed_state_copy_app_address(state, operand, &app_displacement)) {
    value.app_address_known = 1U;
    value.app_displacement = app_displacement;
  }
  typed_stored_value_update_known(&value);
  return value;
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

static void typed_state_set_stack_slot(M68kRenderTypedState *state, int16_t displacement,
    const M68kRenderTypedStoredValue *value) {
  size_t index;
  if (state == NULL || value == NULL || !typed_stored_value_has_useful_info(value)) return;
  for (index = 0U; index < state->stack_slot_count; ++index) {
    if (state->stack_slots[index].known == 0U || state->stack_slots[index].displacement != displacement) continue;
    state->stack_slots[index].value = *value;
    return;
  }
  if (state->stack_slot_count >= M68K_RENDER_TYPED_STACK_SLOT_LIMIT) return;
  state->stack_slots[state->stack_slot_count].known = 1U;
  state->stack_slots[state->stack_slot_count].displacement = displacement;
  state->stack_slots[state->stack_slot_count].value = *value;
  ++state->stack_slot_count;
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

static void typed_state_clear_base_slot(M68kRenderTypedState *state, uint8_t base_reg, int16_t displacement) {
  size_t index;
  if (state == NULL || base_reg >= 8U) return;
  for (index = 0U; index < state->base_slot_count; ++index) {
    if (state->base_slots[index].known == 0U || state->base_slots[index].base_reg != base_reg ||
        state->base_slots[index].displacement != displacement) {
      continue;
    }
    state->base_slots[index] = state->base_slots[state->base_slot_count - 1U];
    --state->base_slot_count;
    return;
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
      return lookup_app_base_field_slot_struct_id(lookup, displacement);
    }
    if (m68k_bitset_u32_has(platform_state->address_base_known, base_reg)) {
      return lookup_base_field_slot_struct_id(lookup, platform_state->address_base_library[base_reg], displacement);
    }
    if (base_reg == 6U) return lookup_app_base_field_slot_struct_id(lookup, displacement);
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
    uint16_t *out_struct_id) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  if (out_displacement != NULL) *out_displacement = 0;
  if (out_struct_id != NULL) *out_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  if (lookup == NULL || operand == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U) {
    return 0;
  }
  if (!render_state_operand_uses_app_base(platform_state, base_reg, displacement)) return 0;
  if (out_displacement != NULL) *out_displacement = displacement;
  if (out_struct_id != NULL) *out_struct_id = lookup_typed_app_slot_struct_id(lookup, displacement);
  return 1;
}

static int typed_storage_key_for_lookup_memory_operand(const M68kRenderLookup *lookup,
    const M68kRenderTypedState *state, const M68kRenderPlatformState *platform_state,
    size_t current_section_index, const M68kOperandIR *operand, uint8_t access_kind, uint8_t *out_kind,
    size_t *out_section_index, int32_t *out_displacement, uint32_t *out_address) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint32_t absolute_offset = 0U;
  (void)lookup;
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
    if (amiga_os_find_hardware_register_by_cpu_address(absolute_offset) != NULL) return 0;
    if (out_kind != NULL) *out_kind = M68K_RENDER_TYPED_STORAGE_ABSOLUTE;
    if (out_section_index != NULL)
      *out_section_index = operand->symbol_ref.has_section ? operand->symbol_ref.section_index : current_section_index;
    if (out_address != NULL) *out_address = absolute_offset;
    return 1;
  }
  return 0;
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

static uint16_t typed_pointer_struct_id_for_field_read(const M68kRenderTypedState *state,
    const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint16_t struct_id = AMIGA_OS_STRUCT_ID_NONE;
  AmigaOsResolvedStructFieldInfo resolved;
  const AmigaOsStructFieldInfo *field;
  if (state == NULL || operand == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U ||
      !state->addr_regs[base_reg].known) {
    return AMIGA_OS_STRUCT_ID_NONE;
  }
  struct_id = state->addr_regs[base_reg].struct_id;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE) return AMIGA_OS_STRUCT_ID_NONE;
  if (!amiga_os_resolve_struct_field_by_struct_id(struct_id, displacement, 0, &resolved)) return AMIGA_OS_STRUCT_ID_NONE;
  if (resolved.query_offset != resolved.offset) return AMIGA_OS_STRUCT_ID_NONE;
  field = amiga_os_find_struct_field_by_field_id(resolved.field_id);
  if (field == NULL || field->pointer_struct_id == AMIGA_OS_STRUCT_ID_NONE) return AMIGA_OS_STRUCT_ID_NONE;
  return field->pointer_struct_id;
}

static int typed_stored_value_from_field_pointer_read(M68kRenderTypedStoredValue *value,
    const M68kRenderTypedState *state, const M68kOperandIR *operand, size_t section_index, uint32_t offset) {
  uint16_t struct_id;
  if (value == NULL) return 0;
  struct_id = typed_pointer_struct_id_for_field_read(state, operand);
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE) return 0;
  typed_stored_value_clear(value);
  value->struct_id = struct_id;
  value->provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_FIELD_POINTER, section_index, offset);
  typed_stored_value_update_known(value);
  return 1;
}

static uint16_t typed_nested_struct_id_for_field_address(const M68kRenderTypedState *state,
    const M68kOperandIR *operand) {
  uint8_t base_reg = 0U;
  int16_t displacement = 0;
  uint16_t struct_id = AMIGA_OS_STRUCT_ID_NONE;
  AmigaOsResolvedStructFieldInfo resolved;
  const AmigaOsStructFieldInfo *field;
  if (state == NULL || operand == NULL ||
      !operand_is_address_memory_local(operand, &base_reg, &displacement) || base_reg >= 8U ||
      !state->addr_regs[base_reg].known) {
    return AMIGA_OS_STRUCT_ID_NONE;
  }
  struct_id = state->addr_regs[base_reg].struct_id;
  if (struct_id == AMIGA_OS_STRUCT_ID_NONE) return AMIGA_OS_STRUCT_ID_NONE;
  if (!amiga_os_resolve_struct_field_by_struct_id(struct_id, displacement, 0, &resolved))
    return AMIGA_OS_STRUCT_ID_NONE;
  if (resolved.query_offset != resolved.offset) return AMIGA_OS_STRUCT_ID_NONE;
  field = amiga_os_find_struct_field_by_field_id(resolved.field_id);
  if (field == NULL || field->pointer_struct_id != AMIGA_OS_STRUCT_ID_NONE || field->size == 0U)
    return AMIGA_OS_STRUCT_ID_NONE;
  return amiga_os_struct_id_from_type_id(field->nested_type_id);
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
  if (out_value != NULL) typed_stored_value_clear(out_value);
  if (out_origin != NULL) typed_origin_clear(out_origin);
  if (lookup == NULL || state == NULL || operand == NULL || out_value == NULL ||
      access_kind != M68K_SIM_ACCESS_MEMORY_READ) {
    return 0;
  }
  if (operand_is_stack_displacement_local(operand, &stack_displacement)) {
    value = typed_state_stack_slot_value(state, stack_displacement);
    if (value != NULL) {
      *out_value = *value;
      if (out_value->provenance.kind == M68K_RENDER_TYPED_PROVENANCE_NONE)
        out_value->provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_STACK_SLOT, current_section_index, 0U);
      if (out_origin != NULL) {
        out_origin->kind = M68K_RENDER_TYPED_ORIGIN_STACK_SLOT;
        out_origin->displacement = stack_displacement;
      }
      return 1;
    }
  }
  if (operand_is_address_memory_local(operand, &base_reg, &base_displacement) && base_reg < 8U && base_reg != 7U &&
      !render_state_operand_uses_app_base(platform_state, base_reg, base_displacement)) {
    value = typed_state_base_slot_value(state, base_reg, base_displacement);
    if (value != NULL) {
      *out_value = *value;
      if (out_value->provenance.kind == M68K_RENDER_TYPED_PROVENANCE_NONE)
        out_value->provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_BASE_SLOT, current_section_index, 0U);
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
    slot = lookup_typed_storage_slot(lookup, storage_kind, storage_section, storage_displacement, storage_address);
    value = slot != NULL ? &slot->value : NULL;
  }
  if (value == NULL) return 0;
  *out_value = *value;
  if (out_value->provenance.kind == M68K_RENDER_TYPED_PROVENANCE_NONE)
    out_value->provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_LOOKUP_STORAGE,
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
        typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
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
          typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
        changed = 1;
        break;
      }
    }
  } else if (origin->kind == M68K_RENDER_TYPED_ORIGIN_BASE_SLOT) {
    M68kRenderTypedBaseSlot *slot = typed_state_mutable_base_slot_entry(state, origin->base_reg,
      (int16_t)origin->displacement);
    if (slot != NULL && typed_stored_value_promote_struct(&slot->value, root_struct_id, refined_struct_id)) {
      slot->value.provenance =
        typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
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
    typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
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
        typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
      changed = 1;
    }
  }
  for (index = 0U; index < state->base_slot_count; ++index) {
    M68kRenderTypedBaseSlot *slot = &state->base_slots[index];
    if (slot->known != 0U && typed_reg_value_same_type_source(source, &slot->value) &&
        typed_stored_value_promote_struct(&slot->value, root_struct_id, refined_struct_id)) {
      slot->value.provenance =
        typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, source_section_index, source_offset);
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
    int16_t displacement = 0;
    uint16_t struct_id, struct_size, container_struct_id = AMIGA_OS_STRUCT_ID_NONE, container_candidate_count = 0U;
    uint8_t access_size;
    char container_struct_name[64], container_field_expr[96];
    int refinement_applied = 0;
    M68kRenderResolvedStructField field;
    M68kRenderTypedProvenance app_slot_provenance;
    const M68kRenderTypedProvenance *provenance = NULL;
    container_struct_name[0] = '\0';
    container_field_expr[0] = '\0';
    /*
     * Keep zero-offset (An) field facts analysis-only. Rendering FIELD(a0) would
     * force d16(An) encoding and break exact reproduction of original (An) bytes.
     */
    if (metadata != NULL && metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_BRANCH_TARGET)
      continue;
    if (!operand_is_address_displacement_local(operand, &base_reg, &displacement) || base_reg >= 8U) continue;
    if (state->addr_regs[base_reg].known) {
      struct_id = state->addr_regs[base_reg].struct_id;
      provenance = &state->addr_regs[base_reg].provenance;
    } else if (state->app_addr_regs[base_reg].known) {
      struct_id = lookup_typed_app_slot_struct_id(lookup, state->app_addr_regs[base_reg].displacement);
      if (struct_id == AMIGA_OS_STRUCT_ID_NONE)
        struct_id = lookup_app_base_field_slot_struct_id(lookup, state->app_addr_regs[base_reg].displacement);
      app_slot_provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_APP_SLOT, section_index, offset);
      provenance = &app_slot_provenance;
    } else {
      continue;
    }
    if (struct_id == AMIGA_OS_STRUCT_ID_NONE) continue;
    struct_size = lookup_policy_struct_size_by_id(lookup->policy, struct_id);
    access_size = instruction_size_suffix_bytes_local(instruction->size_suffix);
    if (!lookup_policy_resolve_struct_field(lookup->policy, struct_id, displacement, &field)) {
      int refined_exact_field_access_recorded = 0;
      if (amiga_os_name(M68K_PLATFORM_NAME_STRUCT, struct_id) != NULL) {
        classify_unresolved_typed_access(struct_id, displacement, struct_size, access_size,
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
            lookup_policy_resolve_struct_field(lookup->policy, container_struct_id, displacement, &field) &&
            field.offset == displacement && field.size == access_size &&
            field.field_expr[0] != '\0') {
          M68kRenderTypedProvenance prefix_provenance =
            typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_PREFIX_REFINEMENT, section_index, offset);
          if (render_lookup_add_typed_access_by_names(lookup, section_index, offset, (uint8_t)operand_index,
              base_reg, displacement, lookup_policy_struct_size_by_id(lookup->policy, container_struct_id), &field,
              &prefix_provenance) != 0) {
            return -1;
          }
          refined_exact_field_access_recorded = 1;
        }
        if (!refined_exact_field_access_recorded) {
          const char *root_struct_name = lookup_policy_struct_name_by_id(lookup->policy, struct_id);
          if (root_struct_name != NULL &&
              render_lookup_add_unresolved_typed_access_by_names(lookup, section_index, offset,
                (uint8_t)operand_index, base_reg, displacement, root_struct_name, struct_size, classification,
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
              (uint8_t)operand_index, base_reg, displacement, root_struct_name, struct_size,
              M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_FIELD_GAP, 0U, NULL, NULL, 0U, NULL, provenance) != 0) {
          return -1;
        }
      }
      continue;
    }
    if (record_accesses) {
      if (render_lookup_add_typed_access_by_names(lookup, section_index, offset, (uint8_t)operand_index,
          base_reg, displacement, struct_size, &field, provenance) != 0) {
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
      ioreq->provenance.kind != M68K_RENDER_TYPED_PROVENANCE_POLICY_SEED ||
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

static void typed_flow_apply_call_input_alias_type(size_t section_index, uint32_t offset,
    M68kRenderTypedState *state, const AmigaOsCallInputInfo *input, int *io_changed) {
  uint8_t source_reg;
  uint8_t preserved_address;
  M68kRenderTypedProvenance provenance;
  if (state == NULL || input == NULL || input->struct_id == AMIGA_OS_STRUCT_ID_NONE ||
      input->reg_kind != AMIGA_OS_REGISTER_ADDRESS || input->reg_index >= 8U ||
      !m68k_bitset_u32_has(state->addr_reg_alias_known, input->reg_index)) {
    return;
  }
  source_reg = state->addr_reg_alias_source[input->reg_index];
  if (source_reg >= 8U) return;
  preserved_address = amiga_os_calling_convention_preserved_address_mask();
  if ((preserved_address & (uint8_t)(1U << source_reg)) == 0U) return;
  provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_API_INPUT, section_index, offset);
  if (state->addr_regs[source_reg].known == 0U) {
    typed_state_set_reg_struct_id(state, AMIGA_OS_REGISTER_ADDRESS, source_reg, input->struct_id, &provenance);
    if (io_changed != NULL) *io_changed = 1;
  } else if (state->addr_regs[source_reg].struct_id != input->struct_id) {
    int conflict = 0;
    uint16_t merged_struct_id = typed_struct_id_refined_merge(state->addr_regs[source_reg].struct_id,
      input->struct_id, &conflict);
    if (conflict == 0U && merged_struct_id != AMIGA_OS_STRUCT_ID_NONE &&
        merged_struct_id != state->addr_regs[source_reg].struct_id) {
      state->addr_regs[source_reg].struct_id = merged_struct_id;
      state->addr_regs[source_reg].output = NULL;
      state->addr_regs[source_reg].provenance = provenance;
      if (io_changed != NULL) *io_changed = 1;
    }
  }
}

static int typed_flow_apply_call_input_type_refs(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, M68kRenderTypedState *state, const AmigaOsLibraryVectorInfo *vector,
    int allow_lookup_storage, int *io_changed) {
  const AmigaOsCallInputInfo *inputs;
  size_t input_count = 0U;
  size_t index;
  if (lookup == NULL || state == NULL || vector == NULL) return 0;
  inputs = amiga_os_library_vector_inputs(vector, &input_count);
  if (inputs == NULL) return 0;
  for (index = 0U; index < input_count; ++index) {
    const AmigaOsCallInputInfo *input = &inputs[index];
    int added = 0;
    if (input->struct_id == AMIGA_OS_STRUCT_ID_NONE ||
        input->reg_kind != AMIGA_OS_REGISTER_ADDRESS || input->reg_index >= 8U) {
      continue;
    }
    if (allow_lookup_storage && state->app_addr_regs[input->reg_index].known) {
      if (render_lookup_add_typed_app_slot_region(lookup, state->app_addr_regs[input->reg_index].displacement,
          input->struct_id, section_index, offset, &added) != 0) {
        return -1;
      }
      if (added && io_changed != NULL) *io_changed = 1;
    }
    if (state->addr_regs[input->reg_index].known &&
        state->addr_regs[input->reg_index].struct_id != input->struct_id &&
        amiga_struct_prefix_chain_contains(input->struct_id, state->addr_regs[input->reg_index].struct_id)) {
      int refined = 0;
      uint16_t root_struct_id = state->addr_regs[input->reg_index].struct_id;
      M68kRenderTypedRegValue input_value = state->addr_regs[input->reg_index];
      if (typed_state_refine_address_reg_from_prefix(lookup, state, input->reg_index,
          root_struct_id, input->struct_id, section_index, offset, &refined) != 0) {
        return -1;
      }
      if (typed_state_promote_matching_stored_values(state, &input_value, root_struct_id, input->struct_id,
          section_index, offset)) {
        refined = 1;
      }
      if (refined && io_changed != NULL) *io_changed = 1;
    }
    typed_flow_apply_call_input_alias_type(section_index, offset, state, input, io_changed);
  }
  return 0;
}

int instruction_operand_writes_register_from_metadata(const M68kInstructionIR *instruction,
    size_t operand_index) {
  const M68kSimFormMetadata *metadata;
  uint8_t access_kind;
  if (instruction == NULL || operand_index >= instruction->operand_count) return 0;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return operand_index + 1U == instruction->operand_count;
  access_kind = metadata->operand_access_kinds[operand_index];
  return access_kind == M68K_SIM_ACCESS_REGISTER_WRITE ||
    access_kind == M68K_SIM_ACCESS_REGISTER_LIST_WRITE;
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
    uint8_t reg = 0U;
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        operand_address_register_index_local(&instruction->operands[operand_index], &reg) && reg == 7U) {
      return 1;
    }
    if (metadata->operand_ea_register_updates[operand_index] != M68K_SIM_EA_UPDATE_NONE &&
        (operand_is_predec_a7_local(&instruction->operands[operand_index]) ||
         operand_is_postinc_a7_local(&instruction->operands[operand_index]))) {
      return 1;
    }
  }
  return 0;
}

static int render_lookup_record_typed_storage_store(M68kRenderLookup *lookup, M68kRenderTypedState *state,
    const M68kRenderPlatformState *platform_state, size_t section_index, const M68kInstructionIR *instruction,
    uint32_t offset, int allow_lookup_storage, int *io_changed) {
  const M68kSimFormMetadata *metadata = NULL;
  size_t source_index = 0U, dest_index = 0U;
  uint8_t base_reg = 0U;
  int16_t base_displacement = 0, stack_displacement = 0;
  if (lookup == NULL || state == NULL || instruction == NULL) return 0;
  if (!instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index, &metadata))
    return 0;
  if (metadata == NULL || metadata->operand_access_kinds[dest_index] != M68K_SIM_ACCESS_MEMORY_WRITE) return 0;
  const M68kOperandIR *source_operand = &instruction->operands[source_index];
  const M68kOperandIR *dest_operand = &instruction->operands[dest_index];
  M68kRenderTypedStoredValue value = typed_stored_value_for_operand(state, source_operand);
  if (!typed_stored_value_has_useful_info(&value) &&
      metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ) {
    (void)typed_value_for_memory_read_operand(lookup, state, platform_state, section_index, source_operand,
      metadata->operand_access_kinds[source_index], &value, NULL);
    if (!typed_stored_value_has_useful_info(&value) && instruction->size_suffix == 'l')
      (void)typed_stored_value_from_field_pointer_read(&value, state, source_operand, section_index, offset);
  }
  if (operand_is_stack_displacement_local(dest_operand, &stack_displacement)) {
    if (typed_stored_value_has_useful_info(&value)) typed_state_set_stack_slot(state, stack_displacement, &value);
    else typed_state_clear_stack_slot(state, stack_displacement);
    return 0;
  }
  if (operand_is_address_memory_local(dest_operand, &base_reg, &base_displacement) && base_reg < 8U &&
      base_reg != 7U && !render_state_operand_uses_app_base(platform_state, base_reg, base_displacement)) {
    if (typed_stored_value_has_useful_info(&value)) typed_state_set_base_slot(state, base_reg, base_displacement,
      &value);
    else typed_state_clear_base_slot(state, base_reg, base_displacement);
    if (!allow_lookup_storage || !state->memory_base_regs[base_reg].known) return 0;
  }
  if (!allow_lookup_storage) return 0;
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
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_MEMORY_WRITE) continue;
    if (operand_is_stack_displacement_local(operand, &stack_displacement)) {
      typed_state_clear_stack_slot(state, stack_displacement);
    }
    if (operand_is_address_memory_local(operand, &base_reg, &base_displacement) && base_reg < 8U &&
        base_reg != 7U && !render_state_operand_uses_app_base(platform_state, base_reg, base_displacement)) {
      typed_state_clear_base_slot(state, base_reg, base_displacement);
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

static void typed_state_update_after_instruction(M68kRenderTypedState *state, const M68kRenderLookup *lookup,
    const M68kRenderPlatformState *platform_state, size_t section_index, const M68kInstructionIR *instruction,
    const M68kDecodeCandidate *candidate, const AmigaOsLibraryVectorInfo *vector, uint32_t offset) {
  const M68kSimFormMetadata *move_metadata = NULL;
  const AmigaOsCallOutputInfo *source_output = NULL;
  uint16_t source_struct_id = AMIGA_OS_STRUCT_ID_NONE;
  M68kRenderTypedStorageOrigin source_origin;
  M68kRenderTypedProvenance source_provenance;
  M68kRenderTypedMemoryBaseValue source_memory_base;
  size_t operand_index, source_index = 0U, dest_index = 0U;
  uint8_t dest_reg = 0U, bit;
  uint8_t source_addr_reg = 0U;
  uint8_t source_alias_reg = 0U;
  int16_t source_app_displacement = 0;
  int source_is_app_address = 0;
  int source_has_memory_base = 0;
  int source_is_direct_addr_reg = 0;
  int source_tracks_plain_addr_alias = 0;
  if (state == NULL || instruction == NULL) return;
  typed_origin_clear(&source_origin);
  typed_provenance_clear(&source_provenance);
  typed_memory_base_clear(&source_memory_base);
  if (instruction_has_call_flow_local(instruction)) {
    if (vector != NULL) typed_state_apply_platform_call_clobbers(state);
    else typed_state_clear_all(state);
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    for (bit = 0U; bit < 8U; ++bit) {
      if ((instruction->operands[1].value.value & (1UL << bit)) != 0U) typed_state_clear_reg(state, 1U, bit);
      if ((instruction->operands[1].value.value & (1UL << (8U + bit))) != 0U) typed_state_clear_reg(state, 2U, bit);
    }
  } else if (instruction_move_operand_indices_from_metadata(instruction, &source_index, &dest_index,
      &move_metadata)) {
    M68kRenderTypedStoredValue stored_value;
    const M68kOperandIR *source_operand = &instruction->operands[source_index];
    const M68kOperandIR *dest_operand = &instruction->operands[dest_index];
    typed_stored_value_clear(&stored_value);
    source_output = typed_state_output_for_operand(state, source_operand, NULL, NULL);
    source_struct_id = typed_state_struct_id_for_operand(state, source_operand);
    source_is_app_address = typed_state_copy_app_address(state, source_operand, &source_app_displacement);
    source_has_memory_base = typed_state_copy_memory_base(state, source_operand, &source_memory_base);
    (void)typed_state_origin_for_operand(state, source_operand, &source_origin);
    source_provenance = typed_stored_value_for_operand(state, source_operand).provenance;
    if (source_struct_id == AMIGA_OS_STRUCT_ID_NONE && move_metadata != NULL &&
        move_metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
        typed_value_for_memory_read_operand(lookup, state, platform_state, section_index, source_operand,
          move_metadata->operand_access_kinds[source_index], &stored_value, &source_origin)) {
      source_output = stored_value.output;
      source_struct_id = stored_value.struct_id;
      source_is_app_address = stored_value.app_address_known;
      source_app_displacement = stored_value.app_displacement;
      source_provenance = stored_value.provenance;
    }
    if (source_struct_id == AMIGA_OS_STRUCT_ID_NONE && move_metadata != NULL &&
        move_metadata->operand_access_kinds[source_index] == M68K_SIM_ACCESS_MEMORY_READ &&
        instruction->size_suffix == 'l') {
      if (typed_stored_value_from_field_pointer_read(&stored_value, state, source_operand, section_index, offset)) {
        source_struct_id = stored_value.struct_id;
        source_provenance = stored_value.provenance;
      }
    }
    if (source_struct_id == AMIGA_OS_STRUCT_ID_NONE) {
      source_struct_id = typed_struct_id_for_base_slot_operand(lookup, platform_state, source_operand);
      if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE)
        source_provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_BASE_SLOT, section_index, offset);
    }
    source_is_direct_addr_reg = operand_address_register_index_local(source_operand, &source_addr_reg);
    source_alias_reg = source_addr_reg;
    if (source_is_direct_addr_reg && source_addr_reg < 8U &&
        m68k_bitset_u32_has(state->addr_reg_alias_known, source_addr_reg)) {
      source_alias_reg = state->addr_reg_alias_source[source_addr_reg];
    }
    source_tracks_plain_addr_alias =
      source_is_direct_addr_reg && source_alias_reg < 8U && source_output == NULL &&
      source_struct_id == AMIGA_OS_STRUCT_ID_NONE && source_is_app_address == 0 && source_has_memory_base == 0 &&
      !state->addr_regs[source_addr_reg].known && !state->app_addr_regs[source_addr_reg].known &&
      !state->memory_base_regs[source_addr_reg].known;
    if (operand_is_data_register_local(dest_operand, &dest_reg)) {
      typed_state_clear_reg(state, 1U, dest_reg);
      if (source_output != NULL &&
          (source_struct_id == AMIGA_OS_STRUCT_ID_NONE || source_output->struct_id != AMIGA_OS_STRUCT_ID_NONE)) {
        typed_state_set_reg(state, 1U, dest_reg, source_output, &source_provenance);
      } else if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
        typed_state_set_reg_struct_id(state, 1U, dest_reg, source_struct_id, &source_provenance);
      }
      if (source_is_app_address) typed_state_set_data_app_address(state, dest_reg, source_app_displacement);
      if (source_has_memory_base)
        typed_state_set_memory_base(state, 1U, dest_reg, source_memory_base.section_index, source_memory_base.offset);
      typed_state_set_reg_origin(state, 1U, dest_reg, &source_origin);
    } else if (operand_address_register_index_local(dest_operand, &dest_reg)) {
      typed_state_clear_reg(state, 2U, dest_reg);
      if (source_is_app_address) typed_state_set_app_address(state, dest_reg, source_app_displacement,
        source_struct_id, &source_provenance);
      else if (source_output != NULL &&
          (source_struct_id == AMIGA_OS_STRUCT_ID_NONE || source_output->struct_id != AMIGA_OS_STRUCT_ID_NONE)) {
        typed_state_set_reg(state, 2U, dest_reg, source_output, &source_provenance);
      } else if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
        typed_state_set_reg_struct_id(state, 2U, dest_reg, source_struct_id, &source_provenance);
      }
      if (source_has_memory_base)
        typed_state_set_memory_base(state, 2U, dest_reg, source_memory_base.section_index, source_memory_base.offset);
      typed_state_set_reg_origin(state, 2U, dest_reg, &source_origin);
      if (source_tracks_plain_addr_alias && dest_reg != source_alias_reg)
        typed_state_set_addr_alias(state, dest_reg, source_alias_reg);
    }
  } else if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U) {
    if (operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
      uint8_t source_base_reg = 0U;
      int16_t source_displacement = 0;
      size_t target_section_index = 0U;
      uint32_t target_offset = 0U;
      typed_state_clear_reg(state, 2U, dest_reg);
      source_struct_id = AMIGA_OS_STRUCT_ID_NONE;
      if (typed_app_address_operand_info(lookup, platform_state, &instruction->operands[0],
          &source_app_displacement, &source_struct_id)) {
        M68kRenderTypedProvenance app_provenance =
          typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_APP_SLOT, section_index, offset);
        typed_state_set_app_address(state, dest_reg, source_app_displacement, source_struct_id, &app_provenance);
      } else if (operand_is_address_memory_local(&instruction->operands[0], &source_base_reg,
          &source_displacement) && source_base_reg < 8U && state->addr_regs[source_base_reg].known) {
        if (source_displacement == 0) {
          source_struct_id = state->addr_regs[source_base_reg].struct_id;
          if (state->app_addr_regs[source_base_reg].known) {
            typed_state_set_app_address(state, dest_reg, state->app_addr_regs[source_base_reg].displacement,
              source_struct_id, &state->addr_regs[source_base_reg].provenance);
          } else if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
            typed_state_set_reg_struct_id(state, 2U, dest_reg, source_struct_id,
              &state->addr_regs[source_base_reg].provenance);
            typed_state_set_reg_origin(state, 2U, dest_reg, &state->addr_regs[source_base_reg].origin);
          }
        } else {
          source_struct_id = typed_nested_struct_id_for_field_address(state, &instruction->operands[0]);
          if (source_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
            M68kRenderTypedProvenance field_provenance =
              typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_FIELD_ADDRESS, section_index, offset);
            typed_state_set_reg_struct_id(state, 2U, dest_reg, source_struct_id, &field_provenance);
          }
        }
      }
      if (candidate_loads_data_target_to_address_reg(candidate, instruction, &target_section_index, &target_offset,
          &dest_reg) ||
          candidate_loads_runtime_address_ref_target_to_address_reg(lookup, section_index, candidate, instruction,
            &target_section_index, &target_offset, &dest_reg)) {
        typed_state_set_memory_base(state, 2U, dest_reg, target_section_index, target_offset);
      } else if (operand_is_address_memory_local(&instruction->operands[0], &source_base_reg,
          &source_displacement) && source_base_reg < 8U && state->memory_base_regs[source_base_reg].known) {
        uint32_t next_offset = 0U;
        if (typed_memory_base_offset_add(state->memory_base_regs[source_base_reg].offset, source_displacement,
            &next_offset)) {
          typed_state_set_memory_base(state, 2U, dest_reg, state->memory_base_regs[source_base_reg].section_index,
            next_offset);
        }
      } else if (operand_is_address_memory_local(&instruction->operands[0], &source_base_reg,
          &source_displacement) && source_base_reg < 8U && source_displacement == 0 &&
          !state->addr_regs[source_base_reg].known && !state->app_addr_regs[source_base_reg].known &&
          !state->memory_base_regs[source_base_reg].known) {
        source_alias_reg = m68k_bitset_u32_has(state->addr_reg_alias_known, source_base_reg) ?
          state->addr_reg_alias_source[source_base_reg] : source_base_reg;
        if (source_alias_reg < 8U && dest_reg != source_alias_reg)
          typed_state_set_addr_alias(state, dest_reg, source_alias_reg);
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
  if (instruction_may_update_stack_pointer_from_metadata(instruction)) typed_state_clear_stack_slots(state);
  if (vector != NULL && amiga_output_has_typed_info(&vector->output)) {
    M68kRenderTypedProvenance api_provenance =
      typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_API_OUTPUT, section_index, offset);
    typed_state_set_reg(state, vector->output.reg_kind, vector->output.reg_index, &vector->output, &api_provenance);
  }
}

static int typed_reg_values_equal(const M68kRenderTypedRegValue *left,
    const M68kRenderTypedRegValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->output == right->output && left->struct_id == right->struct_id &&
    typed_origins_equal(&left->origin, &right->origin) &&
    typed_provenances_equal(&left->provenance, &right->provenance);
}

static int typed_stored_values_equal(const M68kRenderTypedStoredValue *left,
    const M68kRenderTypedStoredValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->output == right->output && left->struct_id == right->struct_id &&
    left->app_address_known == right->app_address_known && left->app_displacement == right->app_displacement &&
    typed_provenances_equal(&left->provenance, &right->provenance);
}

static int typed_app_addresses_equal(const M68kRenderTypedAppAddressValue *left,
    const M68kRenderTypedAppAddressValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->displacement == right->displacement;
}

static int typed_memory_bases_equal(const M68kRenderTypedMemoryBaseValue *left,
    const M68kRenderTypedMemoryBaseValue *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->section_index == right->section_index && left->offset == right->offset;
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
  return left->known == right->known && left->displacement == right->displacement &&
    typed_stored_values_equal(&left->value, &right->value);
}

static int typed_base_slots_equal(const M68kRenderTypedBaseSlot *left,
    const M68kRenderTypedBaseSlot *right) {
  if (left == NULL || right == NULL) return 0;
  return left->known == right->known && left->base_reg == right->base_reg &&
    left->displacement == right->displacement && typed_stored_values_equal(&left->value, &right->value);
}

static int typed_base_slot_sets_equal(const M68kRenderTypedState *left, const M68kRenderTypedState *right) {
  size_t index;
  if (left == NULL || right == NULL || left->base_slot_count != right->base_slot_count) return 0;
  for (index = 0U; index < left->base_slot_count; ++index) {
    const M68kRenderTypedBaseSlot *left_slot = &left->base_slots[index];
    const M68kRenderTypedBaseSlot *right_slot = typed_state_base_slot_entry(right, left_slot->base_reg,
      left_slot->displacement);
    if (!typed_base_slots_equal(left_slot, right_slot)) return 0;
  }
  return 1;
}

static int typed_state_equal(const M68kRenderTypedState *left, const M68kRenderTypedState *right) {
  size_t index;
  if (left == NULL || right == NULL || left->stack_slot_count != right->stack_slot_count ||
      left->base_slot_count != right->base_slot_count) {
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
  return 1;
}

static int platform_states_equal(const M68kRenderPlatformState *left, const M68kRenderPlatformState *right) {
  if (left == NULL || right == NULL) return 0;
  return memcmp(left, right, sizeof(*left)) == 0;
}

static int typed_reg_merge(M68kRenderTypedRegValue *dest, const M68kRenderTypedRegValue *source) {
  M68kRenderTypedRegValue old_value;
  if (dest == NULL || source == NULL) return 0;
  old_value = *dest;
  if (dest->known == 0U || source->known == 0U) {
    typed_reg_value_clear(dest);
    return !typed_reg_values_equal(dest, &old_value);
  }
  if (dest->output == source->output && dest->struct_id == source->struct_id) {
    if (!typed_origins_equal(&dest->origin, &source->origin)) typed_origin_clear(&dest->origin);
    typed_provenance_merge(&dest->provenance, &source->provenance);
    return !typed_reg_values_equal(dest, &old_value);
  }
  {
    uint16_t common_struct_id = typed_struct_id_common_merge(dest->struct_id, source->struct_id);
    if (common_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
      dest->struct_id = common_struct_id;
      dest->output = NULL;
      if (!typed_origins_equal(&dest->origin, &source->origin)) typed_origin_clear(&dest->origin);
      typed_provenance_merge(&dest->provenance, &source->provenance);
      return !typed_reg_values_equal(dest, &old_value);
    }
  }
  if (dest->struct_id != AMIGA_OS_STRUCT_ID_NONE && dest->struct_id == source->struct_id) {
    dest->output = NULL;
    return !typed_reg_values_equal(dest, &old_value);
  }
  typed_reg_value_clear(dest);
  return !typed_reg_values_equal(dest, &old_value);
}

static int typed_stored_value_merge(M68kRenderTypedStoredValue *dest,
    const M68kRenderTypedStoredValue *source) {
  M68kRenderTypedStoredValue old_value;
  if (dest == NULL || source == NULL) return 0;
  old_value = *dest;
  if (!typed_stored_value_has_useful_info(dest) || !typed_stored_value_has_useful_info(source)) {
    typed_stored_value_clear(dest);
    return !typed_stored_values_equal(dest, &old_value);
  }
  if (dest->app_address_known != source->app_address_known ||
      dest->app_displacement != source->app_displacement) {
    dest->app_address_known = 0U;
    dest->app_displacement = 0;
  }
  if (dest->output != source->output) dest->output = NULL;
  typed_provenance_merge(&dest->provenance, &source->provenance);
  dest->struct_id = typed_struct_id_common_merge(dest->struct_id, source->struct_id);
  if (dest->output != NULL && dest->struct_id != AMIGA_OS_STRUCT_ID_NONE &&
      dest->output->struct_id != dest->struct_id) {
    dest->output = NULL;
  }
  typed_stored_value_update_known(dest);
  return !typed_stored_values_equal(dest, &old_value);
}

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
          source->stack_slots[source_index].displacement == dest_slot->displacement) {
        source_slot = &source->stack_slots[source_index];
        break;
      }
    }
    if (source_slot == NULL || typed_stored_value_merge(&dest_slot->value, &source_slot->value) ||
        !typed_stored_value_has_useful_info(&dest_slot->value)) {
      if (source_slot == NULL || !typed_stored_value_has_useful_info(&dest_slot->value)) {
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
    const M68kRenderTypedBaseSlot *source_slot = typed_state_base_slot_entry(source, dest_slot->base_reg,
      dest_slot->displacement);
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

static int typed_state_merge_into(M68kRenderTypedState *dest, const M68kRenderTypedState *source) {
  size_t index;
  int changed = 0;
  if (dest == NULL || source == NULL) return 0;
  for (index = 0U; index < 8U; ++index) {
    M68kRenderTypedAppAddressValue old_data_app = dest->data_app_addr_regs[index];
    M68kRenderTypedAppAddressValue old_app = dest->app_addr_regs[index];
    M68kRenderTypedMemoryBaseValue old_data_memory_base = dest->data_memory_base_regs[index];
    M68kRenderTypedMemoryBaseValue old_memory_base = dest->memory_base_regs[index];
    M68kRenderIoRequestSetup old_io_request_setup = dest->io_request_setups[index];
    int old_alias_known = m68k_bitset_u32_has(dest->addr_reg_alias_known, (uint8_t)index);
    uint8_t old_alias_source = dest->addr_reg_alias_source[index];
    changed |= typed_reg_merge(&dest->data_regs[index], &source->data_regs[index]);
    changed |= typed_reg_merge(&dest->addr_regs[index], &source->addr_regs[index]);
    if (dest->data_app_addr_regs[index].known == 0U || source->data_app_addr_regs[index].known == 0U ||
        dest->data_app_addr_regs[index].displacement != source->data_app_addr_regs[index].displacement) {
      dest->data_app_addr_regs[index].known = 0U;
      dest->data_app_addr_regs[index].displacement = 0;
    }
    if (!typed_app_addresses_equal(&old_data_app, &dest->data_app_addr_regs[index])) changed = 1;
    if (dest->app_addr_regs[index].known == 0U || source->app_addr_regs[index].known == 0U ||
        dest->app_addr_regs[index].displacement != source->app_addr_regs[index].displacement) {
      dest->app_addr_regs[index].known = 0U;
      dest->app_addr_regs[index].displacement = 0;
    }
    if (!typed_app_addresses_equal(&old_app, &dest->app_addr_regs[index])) changed = 1;
    if (dest->data_memory_base_regs[index].known == 0U || source->data_memory_base_regs[index].known == 0U ||
        dest->data_memory_base_regs[index].section_index != source->data_memory_base_regs[index].section_index ||
        dest->data_memory_base_regs[index].offset != source->data_memory_base_regs[index].offset) {
      typed_memory_base_clear(&dest->data_memory_base_regs[index]);
    }
    if (!typed_memory_bases_equal(&old_data_memory_base, &dest->data_memory_base_regs[index])) changed = 1;
    if (dest->memory_base_regs[index].known == 0U || source->memory_base_regs[index].known == 0U ||
        dest->memory_base_regs[index].section_index != source->memory_base_regs[index].section_index ||
        dest->memory_base_regs[index].offset != source->memory_base_regs[index].offset) {
      typed_memory_base_clear(&dest->memory_base_regs[index]);
    }
    if (!typed_memory_bases_equal(&old_memory_base, &dest->memory_base_regs[index])) changed = 1;
    if (!typed_io_request_setups_equal(&dest->io_request_setups[index], &source->io_request_setups[index])) {
      memset(&dest->io_request_setups[index], 0, sizeof(dest->io_request_setups[index]));
    }
    if (!typed_io_request_setups_equal(&old_io_request_setup, &dest->io_request_setups[index])) changed = 1;
    if (!m68k_bitset_u32_has(dest->addr_reg_alias_known, (uint8_t)index) ||
        !m68k_bitset_u32_has(source->addr_reg_alias_known, (uint8_t)index) ||
        dest->addr_reg_alias_source[index] != source->addr_reg_alias_source[index]) {
      m68k_bitset_u32_clear(&dest->addr_reg_alias_known, (uint8_t)index);
      dest->addr_reg_alias_source[index] = 0U;
    }
    if (old_alias_known != m68k_bitset_u32_has(dest->addr_reg_alias_known, (uint8_t)index) ||
        (m68k_bitset_u32_has(dest->addr_reg_alias_known, (uint8_t)index) &&
          old_alias_source != dest->addr_reg_alias_source[index])) {
      changed = 1;
    }
  }
  if (typed_state_merge_stack_slots(dest, source)) changed = 1;
  if (typed_state_merge_base_slots(dest, source)) changed = 1;
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

static int platform_state_merge_into(M68kRenderPlatformState *dest, const M68kRenderPlatformState *source) {
  M68kRenderPlatformState old_state;
  size_t index;
  int changed = 0;
  if (dest == NULL || source == NULL) return 0;
  old_state = *dest;
  for (index = 0U; index < 8U; ++index) {
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

static int typed_flow_successors_for_candidate(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
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

static int typed_flow_infer_local_helper_output_reg_at(const M68kRenderLookup *lookup,
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
    typed_state_update_after_instruction(&typed_state, lookup, &platform_state, section->section_index,
      &instruction, candidate, vector, candidate->offset);
    if (nested_resolution.output_reg_known && nested_resolution.vector != NULL &&
        amiga_output_has_typed_info(&nested_resolution.vector->output)) {
      M68kRenderTypedProvenance api_provenance =
        typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_API_OUTPUT, section->section_index, candidate->offset);
      typed_state_set_reg(&typed_state, nested_resolution.output_reg_kind, nested_resolution.output_reg_index,
        &nested_resolution.vector->output, &api_provenance);
    }
    platform_state_update_data_lvo_after_instruction(&platform_state, &instruction);
    platform_state_update_after_instruction(&platform_state, lookup, &instruction);
    platform_state_note_call_result_after_instruction(&platform_state, &instruction, vector);
    if (!candidate_has_local_helper_summary_fallthrough(candidate))
      break;
    cursor += candidate->byte_count;
  }
  return 0;
}

static const AmigaOsLibraryVectorInfo *typed_flow_resolve_vector(const M68kRenderLookup *lookup,
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

static int typed_flow_process_node(M68kRenderLookup *lookup, const M68kDecodeIR *decode, uint8_t **accepted_start,
    const M68kDecodeSectionIR *section, const M68kRenderTypedFlowNode *node, int allow_lookup_storage,
    int record_typed_accesses, M68kRenderTypedState *out_typed_state, M68kRenderPlatformState *out_platform_state,
    int *io_changed) {
  M68kInstructionIR instruction;
  const AmigaOsLibraryVectorInfo *chosen_vector;
  M68kTypedFlowCallResolution call_resolution;
  const AmigaOsCallOutputInfo *stored_output = NULL;
  int16_t slot_displacement = 0;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || section == NULL || node == NULL ||
      out_typed_state == NULL || out_platform_state == NULL || node->candidate == NULL) {
    return -1;
  }
  *out_typed_state = node->typed_in;
  *out_platform_state = node->platform_in;
  typed_state_apply_policy_register_seeds(out_typed_state, lookup->policy, section->section_index,
    node->candidate->offset);
  platform_state_apply_policy_register_seeds(out_platform_state, lookup->policy, section->section_index,
    node->candidate->offset);
  if (m68k_decode_candidate_to_instruction(node->candidate, &instruction) != 0) return -1;
  attach_known_instruction_relocations(lookup, section->section_index, node->candidate, &instruction);
  typed_flow_call_resolution_init(&call_resolution);
  chosen_vector = typed_flow_resolve_vector(lookup, decode, accepted_start, section, node->candidate,
    out_platform_state, &instruction, &call_resolution);
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
  if (!record_typed_accesses &&
      typed_flow_apply_call_input_type_refs(lookup, section->section_index,
      node->candidate->offset, out_typed_state, chosen_vector, allow_lookup_storage, io_changed) != 0) {
    return -1;
  }
  if (render_lookup_record_typed_storage_store(lookup, out_typed_state, out_platform_state, section->section_index,
      &instruction, node->candidate->offset, allow_lookup_storage, io_changed) != 0) {
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
  typed_state_update_after_instruction(out_typed_state, lookup, out_platform_state, section->section_index,
    &instruction, node->candidate, chosen_vector, node->candidate->offset);
  if (call_resolution.output_reg_known && call_resolution.vector != NULL &&
      amiga_output_has_typed_info(&call_resolution.vector->output)) {
    M68kRenderTypedProvenance api_provenance =
      typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_API_OUTPUT, section->section_index,
        node->candidate->offset);
    typed_state_set_reg(out_typed_state, call_resolution.output_reg_kind, call_resolution.output_reg_index,
      &call_resolution.vector->output, &api_provenance);
  }
  platform_state_update_data_lvo_after_instruction(out_platform_state, &instruction);
  platform_state_update_after_instruction(out_platform_state, lookup, &instruction);
  platform_state_note_call_result_after_instruction(out_platform_state, &instruction, chosen_vector);
  if (candidate_terminates_a6_state(node->candidate)) typed_state_clear_all(out_typed_state);
  return 0;
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
  nodes = (M68kRenderTypedFlowNode *)arena_calloc(arena,
    section->candidate_count != 0U ? section->candidate_count : 1U, sizeof(*nodes));
  node_by_offset = (size_t *)arena_alloc(arena, ((size_t)render_extent + 1U) * sizeof(*node_by_offset));
  if (nodes == NULL || node_by_offset == NULL) goto oom;
  for (candidate_index = 0U; candidate_index <= (size_t)render_extent; ++candidate_index)
    node_by_offset[candidate_index] = SIZE_MAX;
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
} M68kRenderTypedFlowGraph;

static void typed_flow_graph_destroy(M68kRenderTypedFlowGraph *graph) {
  if (graph == NULL) return;
  memset(graph, 0, sizeof(*graph));
}

static void typed_flow_build_successors_for_nodes(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    M68kRenderTypedFlowNode *nodes, size_t node_count, const size_t *node_by_offset,
    uint32_t node_by_offset_count) {
  size_t node_index;
  if (section == NULL || accepted_start == NULL || nodes == NULL || node_by_offset == NULL) return;
  for (node_index = 0U; node_index < node_count; ++node_index) {
    int successor_count = typed_flow_successors_for_candidate(section, accepted_start, node_by_offset,
      node_by_offset_count, nodes[node_index].candidate, nodes[node_index].successors,
      sizeof(nodes[node_index].successors) / sizeof(nodes[node_index].successors[0]));
    nodes[node_index].successor_count = (uint8_t)(successor_count > 0 ? successor_count : 0);
  }
}

static int typed_flow_mark_roots(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    M68kRenderTypedFlowNode *nodes, size_t node_count, const size_t *node_by_offset,
    uint32_t node_by_offset_count, Arena *arena) {
  uint16_t *incoming_counts = NULL;
  ArenaMark mark;
  size_t node_index;
  int seeded_root = 0;
  (void)section;
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
    if (nodes[node_index].is_root) {
      nodes[node_index].has_in = 1U;
    }
  }
}

static int typed_flow_initialize_roots(const M68kDecodeSectionIR *section, const uint8_t *accepted_start,
    M68kRenderTypedFlowNode *nodes, size_t node_count, const size_t *node_by_offset,
    uint32_t node_by_offset_count, Arena *arena) {
  if (typed_flow_mark_roots(section, accepted_start, nodes, node_count, node_by_offset,
      node_by_offset_count, arena) != 0) {
    return -1;
  }
  typed_flow_reset_roots(nodes, node_count);
  return 0;
}

static int typed_flow_graph_build(M68kRenderTypedFlowGraph *graph, const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, Arena *arena) {
  if (graph == NULL) return -1;
  memset(graph, 0, sizeof(*graph));
  if (typed_flow_build_nodes(section, accepted_start, &graph->nodes, &graph->node_count,
      &graph->node_by_offset, &graph->node_by_offset_count, arena) != 0) {
    return -1;
  }
  typed_flow_build_successors_for_nodes(section, accepted_start, graph->nodes, graph->node_count,
    graph->node_by_offset, graph->node_by_offset_count);
  if (typed_flow_initialize_roots(section, accepted_start, graph->nodes, graph->node_count,
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

static int render_lookup_analyze_amiga_typed_refs_for_section(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, const M68kDecodeSectionIR *section, M68kRenderTypedFlowGraph *graph,
    int final_pass, int *io_changed, Arena *arena) {
  size_t iteration_limit = typed_flow_limit_from_env("AMIGA_REVERSING_TYPED_FLOW_MAX_ITERATIONS",
    M68K_RENDER_TYPED_FLOW_DEFAULT_ITERATION_LIMIT);
  size_t node_visit_limit = typed_flow_limit_from_env("AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS",
    M68K_RENDER_TYPED_FLOW_DEFAULT_NODE_VISIT_LIMIT);
  size_t max_visits, node_visit_count = 0U, queue_head = 0U, queue_count = 0U, node_index;
  size_t *queue = NULL;
  uint8_t *queued = NULL;
  ArenaMark mark;
  int result = -1;
  if (graph == NULL || arena == NULL) return -1;
  typed_flow_reinitialize_roots(graph->nodes, graph->node_count);
  if (graph->node_count == 0U) return 0;
  mark = arena_mark(arena);
  queue = (size_t *)arena_alloc(arena, graph->node_count * sizeof(*queue));
  queued = (uint8_t *)arena_calloc(arena, graph->node_count, sizeof(*queued));
  if (queue == NULL || queued == NULL) goto cleanup;
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
    if (!typed_state_equal(&node->typed_out, &next_typed_state) ||
        !platform_states_equal(&node->platform_out, &next_platform_state)) {
      node->typed_out = next_typed_state;
      node->platform_out = next_platform_state;
    }
    for (successor_index = 0U; successor_index < node->successor_count; ++successor_index) {
      size_t successor = node->successors[successor_index];
      if (successor >= graph->node_count) continue;
      if (typed_flow_merge_input(&graph->nodes[successor], &next_typed_state, &next_platform_state)) {
        if (typed_flow_enqueue_node(queue, queued, graph->node_count, &queue_head, &queue_count, successor) != 0)
          goto cleanup;
      }
    }
  }
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
  }
  result = 0;

cleanup:
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
  if (inputs == NULL) return 0;
  for (index = 0U; index < input_count; ++index) {
    if (inputs[index].struct_id != AMIGA_OS_STRUCT_ID_NONE) return 1;
  }
  return 0;
}

static int policy_has_typed_flow_metadata(const M68kAnalysisPolicy *policy) {
  if (policy == NULL) return 0;
  return policy->register_seed_count != 0U || policy->rsset_layout_region_count != 0U ||
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
  for (index = 0U; index < lookup->global_base_slot_count; ++index) {
    if (lookup->global_base_slots[index].has_library_id != 0U &&
        lookup->global_base_slots[index].conflicted == 0U) return 1;
  }
  for (index = 0U; index < lookup->recovered_local_call_summary_count; ++index) {
    if (amiga_vector_has_typed_flow_info(lookup->recovered_local_call_summaries[index].vector)) return 1;
  }
  return 0;
}

static int render_lookup_analyze_amiga_typed_refs(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  Arena *workflow_arena = NULL;
  M68kRenderTypedFlowGraph *graphs = NULL;
  int pass;
  int changed = 0;
  size_t section_index;
  int result = -1;
  if (lookup == NULL || decode == NULL || accepted_start == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  if (!render_lookup_has_typed_flow_sources(lookup, decode, accepted_start)) return 0;
  workflow_arena = arena_create(4096U);
  if (workflow_arena == NULL) return -1;
  graphs = (M68kRenderTypedFlowGraph *)arena_calloc(workflow_arena,
    decode->section_count != 0U ? decode->section_count : 1U,
    sizeof(*graphs));
  if (graphs == NULL) goto cleanup;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    if (typed_flow_graph_build(&graphs[section_index], &decode->sections[section_index],
        accepted_start[section_index], workflow_arena) != 0) {
      goto cleanup;
    }
  }
  for (pass = 0; pass < 5; ++pass) {
    int final_pass = pass == 4;
    changed = 0;
    if (final_pass) lookup->typed_access_count = 0U;
    for (section_index = 0U; section_index < decode->section_count; ++section_index) {
      if (render_lookup_analyze_amiga_typed_refs_for_section(lookup, decode, accepted_start,
          &decode->sections[section_index], &graphs[section_index], final_pass,
          final_pass ? NULL : &changed, workflow_arena) != 0) {
        goto cleanup;
      }
    }
    if (!final_pass && !changed) pass = 3;
  }
  result = 0;

cleanup:
  if (graphs != NULL) {
    for (section_index = 0U; section_index < decode->section_count; ++section_index)
      typed_flow_graph_destroy(&graphs[section_index]);
  }
  arena_destroy(workflow_arena);
  return result;
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
        provenance = typed_provenance_make(M68K_RENDER_TYPED_PROVENANCE_APP_SLOT, section->section_index,
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

static void data_pointer_state_clear_all(M68kRenderDataPointerState *state) {
  if (state == NULL) return;
  memset(state, 0, sizeof(*state));
}

static void data_pointer_state_clear_reg(M68kRenderDataPointerState *state, uint8_t reg_kind, uint8_t reg_index) {
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == AMIGA_OS_REGISTER_DATA) {
    state->data_regs[reg_index].known = 0U;
    state->data_scalars[reg_index].known = 0U;
  }
  else if (reg_kind == AMIGA_OS_REGISTER_ADDRESS) state->addr_regs[reg_index].known = 0U;
}

static void data_pointer_state_set_reg_with_exact(M68kRenderDataPointerState *state, uint8_t reg_kind,
    uint8_t reg_index, size_t section_index, uint32_t offset, uint8_t exact) {
  M68kRenderDataPointerValue *value;
  if (state == NULL || reg_index >= 8U) return;
  if (reg_kind == AMIGA_OS_REGISTER_DATA) value = &state->data_regs[reg_index];
  else if (reg_kind == AMIGA_OS_REGISTER_ADDRESS) value = &state->addr_regs[reg_index];
  else return;
  value->known = 1U;
  value->exact = exact != 0U;
  value->dynamic_offset_known = 0U;
  value->section_index = section_index;
  value->offset = offset;
  value->dynamic_offset_section_index = 0U;
  value->dynamic_offset_offset = 0U;
  if (reg_kind == AMIGA_OS_REGISTER_DATA) state->data_scalars[reg_index].known = 0U;
}

static void data_pointer_state_set_reg(M68kRenderDataPointerState *state, uint8_t reg_kind, uint8_t reg_index,
    size_t section_index, uint32_t offset) {
  data_pointer_state_set_reg_with_exact(state, reg_kind, reg_index, section_index, offset, 1U);
}

static void data_pointer_state_copy_reg(M68kRenderDataPointerState *state, uint8_t reg_kind, uint8_t reg_index,
    const M68kRenderDataPointerValue *source) {
  M68kRenderDataPointerValue *dest;
  if (state == NULL || source == NULL || reg_index >= 8U) return;
  if (reg_kind == AMIGA_OS_REGISTER_DATA) dest = &state->data_regs[reg_index];
  else if (reg_kind == AMIGA_OS_REGISTER_ADDRESS) dest = &state->addr_regs[reg_index];
  else return;
  *dest = *source;
  if (reg_kind == AMIGA_OS_REGISTER_DATA) state->data_scalars[reg_index].known = 0U;
}

static void data_pointer_state_set_data_scalar(M68kRenderDataPointerState *state, uint8_t reg_index,
    uint32_t value) {
  if (state == NULL || reg_index >= 8U) return;
  state->data_regs[reg_index].known = 0U;
  state->data_scalars[reg_index].known = 1U;
  state->data_scalars[reg_index].value = value;
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

static int data_pointer_value_with_signed_displacement(const M68kRenderDataPointerValue *base,
    int32_t displacement, size_t *out_section_index, uint32_t *out_offset) {
  int64_t offset;
  if (out_section_index != NULL) *out_section_index = 0U;
  if (out_offset != NULL) *out_offset = 0U;
  if (base == NULL || !base->known || out_section_index == NULL || out_offset == NULL) return 0;
  offset = (int64_t)(uint64_t)base->offset + (int64_t)displacement;
  if (offset < 0 || offset > (int64_t)(uint64_t)UINT32_MAX) return 0;
  *out_section_index = base->section_index;
  *out_offset = (uint32_t)offset;
  return 1;
}

static void data_pointer_state_mark_address_reg_dynamic(M68kRenderDataPointerState *state, uint8_t reg_index,
    const M68kDecodeCandidate *candidate) {
  size_t table_section_index = 0U;
  uint32_t table_offset = 0U;
  if (state == NULL || reg_index >= 8U || !state->addr_regs[reg_index].known) return;
  state->addr_regs[reg_index].exact = 0U;
  if (candidate_data_target_for_operand(candidate, 0U, &table_section_index, &table_offset)) {
    state->addr_regs[reg_index].dynamic_offset_known = 1U;
    state->addr_regs[reg_index].dynamic_offset_section_index = table_section_index;
    state->addr_regs[reg_index].dynamic_offset_offset = table_offset;
  }
}

static const M68kRenderDataPointerValue *data_pointer_state_value_for_operand(
    const M68kRenderDataPointerState *state, const M68kOperandIR *operand) {
  uint8_t reg = 0U;
  if (state == NULL || operand == NULL) return NULL;
  if (operand_is_data_register_local(operand, &reg)) return state->data_regs[reg].known ? &state->data_regs[reg] : NULL;
  if (operand_address_register_index_local(operand, &reg)) return state->addr_regs[reg].known ? &state->addr_regs[reg] : NULL;
  return NULL;
}

static int candidate_loads_data_target_to_address_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg) {
  uint8_t dest_reg = 0U;
  if (candidate == NULL || instruction == NULL || out_section_index == NULL || out_offset == NULL ||
      out_reg == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA || instruction->operand_count != 2U ||
      !operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
    return 0;
  }
  if (candidate_data_target_for_operand(candidate, 0U, out_section_index, out_offset)) {
    *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static int candidate_moves_data_target_to_data_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, size_t *out_section_index, uint32_t *out_offset, uint8_t *out_reg) {
  uint8_t dest_reg = 0U;
  if (candidate == NULL || instruction == NULL || out_section_index == NULL || out_offset == NULL ||
      out_reg == NULL || instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE ||
      instruction->size_suffix != 'l' || instruction->operand_count != 2U ||
      !operand_is_data_register_local(&instruction->operands[1], &dest_reg)) {
    return 0;
  }
  if (candidate_data_target_for_operand(candidate, 0U, out_section_index, out_offset)) {
    *out_reg = dest_reg;
    return 1;
  }
  return 0;
}

static int candidate_loads_relocated_data_target_to_address_reg(const M68kRenderLookup *lookup,
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
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_LEA || instruction->operand_count != 2U ||
      !operand_address_register_index_local(&instruction->operands[1], &dest_reg) ||
      candidate->byte_count > section->size || candidate->offset > section->size - candidate->byte_count) {
    return 0;
  }
  relocation_end = candidate->offset + candidate->byte_count;
  for (relocation_offset = candidate->offset + 2U; relocation_offset < relocation_end; ++relocation_offset) {
    const M68kFact *relocation = lookup_relocation_at(lookup, section->section_index, relocation_offset);
    if (relocation == NULL || relocation->size != 4U ||
        relocation->target_section_index >= lookup->section_count) {
      continue;
    }
    *out_section_index = relocation->target_section_index;
    *out_offset = relocation->target_offset;
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

static int candidate_moves_relocated_immediate_target_to_data_reg(const M68kRenderLookup *lookup,
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
      candidate->byte_count > section->size || candidate->offset > section->size - candidate->byte_count ||
      candidate->mnemonic_id != M68K_ASM_MNEMONIC_MOVE || candidate->operand_count != 2U ||
      instruction->operand_count != 2U || !candidate_operand_is_immediate_form(candidate, 0U) ||
      !operand_is_data_register_local(&instruction->operands[1], &dest_reg)) {
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

static int candidate_moves_immediate_scalar_to_data_reg(const M68kDecodeCandidate *candidate,
    const M68kInstructionIR *instruction, uint8_t *out_reg, uint32_t *out_value) {
  uint8_t dest_reg = 0U;
  uint32_t value = 0U;
  if (out_reg != NULL) *out_reg = 0U;
  if (out_value != NULL) *out_value = 0U;
  if (candidate == NULL || instruction == NULL || out_reg == NULL || out_value == NULL ||
      instruction->operand_count != 2U || !operand_is_data_register_local(&instruction->operands[1], &dest_reg) ||
      !m68k_ir_operand_immediate_value(&instruction->operands[0], &value)) {
    return 0;
  }
  if (instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVE &&
      instruction->mnemonic_id != M68K_ASM_MNEMONIC_MOVEQ) {
    return 0;
  }
  *out_reg = dest_reg;
  *out_value = value;
  return 1;
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

static int lookup_runtime_address_to_source_offset_local(const M68kRenderLookup *lookup,
    size_t section_index, uint32_t section_size, uint32_t runtime_address, uint32_t *out_source_offset) {
  size_t range_index;
  if (out_source_offset != NULL) *out_source_offset = 0U;
  if (lookup == NULL || out_source_offset == NULL) return 0;
  if (runtime_address < section_size) {
    uint32_t logical_address = 0U;
    if (lookup_source_logical_address(lookup, section_index, runtime_address, &logical_address) &&
        logical_address == runtime_address) {
      *out_source_offset = runtime_address;
      return 1;
    }
  }
  for (range_index = 0U; range_index < lookup->runtime_address_range_count; ++range_index) {
    const M68kFact *range = lookup->runtime_address_ranges[range_index].fact;
    uint32_t delta;
    uint32_t source_offset;
    if (range == NULL || range->section_index != section_index || !range->has_runtime_address ||
        runtime_address < range->runtime_address) {
      continue;
    }
    delta = runtime_address - range->runtime_address;
    if (delta >= range->size || range->offset > UINT32_MAX - delta) continue;
    source_offset = range->offset + delta;
    if (source_offset >= section_size) continue;
    if (!lookup_source_has_materialized_runtime_address(lookup, section_index, source_offset, runtime_address))
      continue;
    *out_source_offset = source_offset;
    return 1;
  }
  return 0;
}

static void data_pointer_state_update_after_instruction_ex(M68kRenderDataPointerState *state,
    const M68kRenderLookup *lookup, const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction, uint8_t prefer_local_absolute) {
  const M68kRenderDataPointerValue *source_value = NULL;
  size_t target_section_index = 0U;
  uint32_t target_offset = 0U, absolute_offset = 0U, scalar_value = 0U;
  uint8_t dest_reg = 0U, source_reg = 0U;
  int16_t displacement = 0;
  size_t operand_index;
  if (state == NULL || instruction == NULL) return;
  if (instruction_has_call_flow_local(instruction)) {
    data_pointer_state_clear_all(state);
    return;
  }
  if (candidate_loads_data_target_to_address_reg(candidate, instruction, &target_section_index, &target_offset,
      &dest_reg)) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, target_section_index, target_offset);
    return;
  }
  if (candidate_moves_data_target_to_data_reg(candidate, instruction, &target_section_index, &target_offset,
      &dest_reg)) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg, target_section_index, target_offset);
    return;
  }
  if (prefer_local_absolute && section != NULL && instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      instruction->operand_count == 2U &&
      operand_address_register_index_local(&instruction->operands[1], &dest_reg) &&
      operand_absolute_offset_local(&instruction->operands[0], &absolute_offset) &&
      absolute_offset < section->size) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, section->section_index,
      absolute_offset);
    return;
  }
  if (candidate_loads_runtime_address_ref_target_to_address_reg(lookup, section != NULL ? section->section_index : 0U,
      candidate, instruction, &target_section_index, &target_offset, &dest_reg) ||
      candidate_loads_relocated_data_target_to_address_reg(lookup, section, candidate, instruction,
        &target_section_index, &target_offset, &dest_reg)) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, target_section_index, target_offset);
    return;
  }
  if (candidate_moves_relocated_immediate_target_to_data_reg(lookup, section, candidate, instruction,
      &target_section_index, &target_offset, &dest_reg)) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg, target_section_index, target_offset);
    return;
  }
  if (candidate_moves_immediate_scalar_to_data_reg(candidate, instruction, &dest_reg, &scalar_value)) {
    data_pointer_state_set_data_scalar(state, dest_reg, scalar_value);
    return;
  }
  if (!prefer_local_absolute && section != NULL && instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      instruction->operand_count == 2U &&
      operand_address_register_index_local(&instruction->operands[1], &dest_reg) &&
      operand_absolute_offset_local(&instruction->operands[0], &absolute_offset) &&
      lookup_runtime_address_to_source_offset_local(lookup, section->section_index, section->size,
        absolute_offset, &target_offset)) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, section->section_index,
      target_offset);
    return;
  }
  if (!prefer_local_absolute && section != NULL && instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA &&
      instruction->operand_count == 2U &&
      operand_address_register_index_local(&instruction->operands[1], &dest_reg) &&
      operand_absolute_offset_local(&instruction->operands[0], &absolute_offset) &&
      absolute_offset < section->size) {
    data_pointer_state_set_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, section->section_index,
      absolute_offset);
    return;
  }
  if (section != NULL && instruction->mnemonic_id == M68K_ASM_MNEMONIC_LEA && instruction->operand_count == 2U &&
      operand_address_register_index_local(&instruction->operands[1], &dest_reg) &&
      operand_is_address_displacement_local(&instruction->operands[0], &source_reg, &displacement) &&
      source_reg < 8U && state->addr_regs[source_reg].known &&
      state->addr_regs[source_reg].section_index == section->section_index) {
    int64_t adjusted_offset = (int64_t)state->addr_regs[source_reg].offset + (int64_t)displacement;
    if (adjusted_offset >= 0 && (uint64_t)adjusted_offset < (uint64_t)section->size) {
      M68kRenderDataPointerValue adjusted = state->addr_regs[source_reg];
      adjusted.offset = (uint32_t)adjusted_offset;
      data_pointer_state_copy_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, &adjusted);
      return;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_ADDA && instruction->operand_count == 2U &&
      operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
    data_pointer_state_mark_address_reg_dynamic(state, dest_reg, candidate);
    return;
  }
  if ((instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVE ||
       instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEA) &&
      instruction->operand_count == 2U) {
    source_value = data_pointer_state_value_for_operand(state, &instruction->operands[0]);
    if (operand_is_data_register_local(&instruction->operands[1], &dest_reg)) {
      M68kRenderDataScalarValue source_scalar;
      uint8_t has_source_scalar = 0U;
      memset(&source_scalar, 0, sizeof(source_scalar));
      if (operand_is_data_register_local(&instruction->operands[0], &source_reg)) {
        source_scalar = state->data_scalars[source_reg];
        has_source_scalar = source_scalar.known;
      }
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg);
      if (source_value != NULL)
        data_pointer_state_copy_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg, source_value);
      else if (has_source_scalar) {
        state->data_regs[dest_reg].known = 0U;
        state->data_scalars[dest_reg] = source_scalar;
      }
      return;
    }
    if (operand_address_register_index_local(&instruction->operands[1], &dest_reg)) {
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg);
      if (source_value != NULL)
        data_pointer_state_copy_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg, source_value);
      return;
    }
  }
  if (instruction->mnemonic_id == M68K_ASM_MNEMONIC_MOVEM && instruction->operand_count >= 2U &&
      instruction->operands[1].kind == M68K_ASM_OPERAND_REGLIST) {
    uint8_t bit;
    for (bit = 0U; bit < 8U; ++bit) {
      if ((instruction->operands[1].value.value & (1UL << bit)) != 0U)
        data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_DATA, bit);
      if ((instruction->operands[1].value.value & (1UL << (8U + bit))) != 0U)
        data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_ADDRESS, bit);
    }
    return;
  }
  for (operand_index = 0U; operand_index < instruction->operand_count; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    if (!instruction_operand_writes_register_from_metadata(instruction, operand_index)) continue;
    if (operand_is_data_register_local(operand, &dest_reg))
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_DATA, dest_reg);
    else if (operand_address_register_index_local(operand, &dest_reg))
      data_pointer_state_clear_reg(state, AMIGA_OS_REGISTER_ADDRESS, dest_reg);
  }
}

static int append_render_lookup_recovered_local_call_summaries_for_section(const M68kRenderLookup *lookup,
    M68kSectionAnalysisIR *section_analysis) {
  size_t index;
  if (lookup == NULL || section_analysis == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK) {
    return 0;
  }
  for (index = 0U; index < lookup->recovered_local_call_summary_count; ++index) {
    const M68kRenderRecoveredLocalCallSummary *summary = &lookup->recovered_local_call_summaries[index];
    const AmigaOsCallOutputInfo *output;
    const char *symbol_name;
    const char *type_name;
    const char *semantic_kind;
    const char *value_domain_name;
    if (summary->section_index != section_analysis->section_index || summary->vector == NULL) continue;
    output = &summary->vector->output;
    if (output->reg_kind == AMIGA_OS_REGISTER_NONE || output->reg_index >= 8U) continue;
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
    if (m68k_ir_section_analysis_append_recovered_local_call_summary(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, summary->target_offset, M68K_PLATFORM_EFFECT_SET_TYPED_REG,
        output->reg_kind, output->reg_index, 0U, 0U, 0U, 0, NULL, symbol_name, type_name, semantic_kind,
        value_domain_name, 0U, 0) != 0) {
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
    const AmigaOsCallInputInfo *input = arg->input;
    const char *symbol_name;
    const char *type_name;
    const char *semantic_kind;
    const char *value_domain_name;
    if (arg->section_index != section_analysis->section_index || input == NULL) continue;
    symbol_name = amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, input->input_id);
    type_name = amiga_input_type_or_struct_name(input);
    semantic_kind = amiga_os_name(M68K_PLATFORM_NAME_SEMANTIC_KIND, input->semantic_kind_id);
    value_domain_name = amiga_os_name(M68K_PLATFORM_NAME_VALUE_DOMAIN, input->value_domain_id);
    if (m68k_ir_section_analysis_append_recovered_function_arg(section_analysis,
        M68K_PLATFORM_BACKEND_AMIGA_HUNK, arg->function_offset, arg->stack_offset, arg->reg_kind, arg->reg_index,
        NULL, symbol_name, type_name, semantic_kind, value_domain_name, 0U, 0, 0U, 0U, 0U, 0U, 0) != 0) {
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
        access->displacement, access->field_offset, access->struct_size, access->field_size,
        access->root_struct_name, access->owner_struct_name, access->field_name, access->field_expr,
        access->inherited, access->nested, access->provenance.kind, access->provenance.section_index,
        access->provenance.offset) != 0) {
      return -1;
    }
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
        access->displacement, access->struct_size, access->root_struct_name, access->classification,
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
    library_name = amiga_os_name(M68K_PLATFORM_NAME_LIBRARY, vector->library_id);
    base_name = amiga_os_find_library_base_name(library_name);
    if (library_name == NULL || base_name == NULL) continue;
    if (!library_has_all_observed_lvos(base_name, observation)) continue;
    if (matched_library_id != 0U && matched_library_id != vector->library_id) return NULL;
    matched_library_id = vector->library_id;
  }
  return matched_library_id != 0U ? amiga_os_name(M68K_PLATFORM_NAME_LIBRARY, matched_library_id) : NULL;
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
  library_id = amiga_os_name_id(M68K_PLATFORM_NAME_LIBRARY, library_name);
  canonical_library_name = library_id != 0U ? amiga_os_name(M68K_PLATFORM_NAME_LIBRARY, library_id) : NULL;
  if (canonical_library_name == NULL || canonical_library_name[0] == '\0' ||
      amiga_os_find_library_base_name(canonical_library_name) == NULL) {
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
    if (slot_library_name[0] == '\0' || amiga_os_find_library_base_name(slot_library_name) == NULL) return 0;
    has_slot_library_id = 1U;
    slot_library_id = amiga_os_name_id(M68K_PLATFORM_NAME_LIBRARY, slot_library_name);
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
    if (slot->symbol[0] == '\0' || slot->offset > 0x7FFFU) continue;
    if (render_lookup_add_named_layout_field_slot(lookup, base_symbol, (int16_t)slot->offset, slot->symbol, SIZE_MAX,
        UINT32_MAX) != 0) {
      return -1;
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
    uint8_t observed_access_size, int add_renderable_slot) {
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
    const M68kRenderAppSlotRef *existing = &lookup->app_slot_refs[index];
    if (existing->section_index == section_index && existing->ref.offset == offset &&
        existing->ref.displacement == displacement && existing->ref.base_reg == base_reg &&
        existing->ref.operand_index == operand_index && existing->ref.access_kind == access_kind) {
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

static int render_lookup_add_auto_structured_data_item(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint32_t size, uint32_t semantic_role_flags, uint8_t kind) {
  M68kAnalysisStructuredDataItem *grown;
  M68kAnalysisStructuredDataItem *item;
  M68kRenderRangeOwnershipView existing_range;
  const char *semantic_role;
  size_t next_capacity;
  size_t index;
  if (lookup == NULL || semantic_role_flags == 0U || size == 0U) return 0;
  if (lookup_range_ownership_at_offset(lookup, section_index, offset, &existing_range) &&
      !structured_data_item_is_untyped_bytes_placeholder_local(existing_range.structured_item))
    return 0;
  semantic_role = m68k_analysis_structured_data_role_name_for_flags(semantic_role_flags);
  if (semantic_role == NULL || semantic_role[0] == '\0') return 0;
  for (index = 0U; index < lookup->auto_structured_data_item_count; ++index) {
    const M68kAnalysisStructuredDataItem *existing = &lookup->auto_structured_data_items[index];
    uint32_t existing_role_flags = existing->semantic_role_flags;
    if (existing->section_index == (uint32_t)section_index && existing->offset == offset &&
        existing->size == size && existing_role_flags == semantic_role_flags) {
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
  memset(item, 0, sizeof(*item));
  item->has_section_index = 1U;
  item->section_index = (uint32_t)section_index;
  item->offset = offset;
  item->size = size;
  item->kind = kind;
  item->entry_count_proof_id = M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_STRUCTURED_RANGE;
  m68k_analysis_structured_data_item_set_semantic_role_flags(item, semantic_role_flags);
  ++lookup->auto_structured_data_item_count;
  if (render_lookup_add_range_ownership_for_structured_item(lookup, section_index,
      M68K_RENDER_RANGE_STRUCTURED_ITEM_AUTO, lookup->auto_structured_data_item_count - 1U, item) != 0) {
    return -1;
  }
  render_lookup_mark_boundary_flag(lookup, section_index, offset, M68K_RENDER_BOUNDARY_STRUCTURED_DATA);
  if (section_index < lookup->section_count && lookup->auto_structured_data_item_indices != NULL &&
      lookup->auto_structured_data_item_index_extents != NULL &&
      offset <= lookup->auto_structured_data_item_index_extents[section_index] &&
      lookup->auto_structured_data_item_indices[section_index] != NULL) {
    lookup->auto_structured_data_item_indices[section_index][offset] = lookup->auto_structured_data_item_count;
  }
  return 0;
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
    if (stored->section_index != section_index || stored->start_offset != source_item->offset) continue;
    if (!lookup_range_ownership_at_index(lookup, index, &existing_range)) continue;
    if (structured_data_item_is_untyped_bytes_placeholder_local(existing_range.structured_item)) continue;
    if (existing_range.structured_item_source == M68K_RENDER_RANGE_STRUCTURED_ITEM_POLICY) return 0;
  }
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

static void render_lookup_set_auto_structured_data_item_target(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, size_t target_section_index, uint32_t target_offset) {
  size_t index;
  if (lookup == NULL) return;
  for (index = 0U; index < lookup->auto_structured_data_item_count; ++index) {
    M68kAnalysisStructuredDataItem *item = &lookup->auto_structured_data_items[index];
    if (item->has_section_index && item->section_index == (uint32_t)section_index &&
        item->offset == offset) {
      item->has_target = 1U;
      item->target_section = (uint32_t)target_section_index;
      item->target_offset = target_offset;
      m68k_analysis_structured_data_item_refresh_table_metadata(item);
    }
  }
}

static void render_lookup_set_auto_structured_data_item_consumer(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, size_t consumer_section_index, uint32_t consumer_offset) {
  size_t index;
  if (lookup == NULL) return;
  for (index = 0U; index < lookup->auto_structured_data_item_count; ++index) {
    M68kAnalysisStructuredDataItem *item = &lookup->auto_structured_data_items[index];
    if (item->has_section_index && item->section_index == (uint32_t)section_index &&
        item->offset == offset) {
      item->has_consumer = 1U;
      item->consumer_section = (uint32_t)consumer_section_index;
      item->consumer_offset = consumer_offset;
    }
  }
}

static void render_lookup_set_auto_structured_data_item_consumer_registers(M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset, uint8_t has_index_register, uint8_t index_register_kind,
    uint8_t index_register, uint8_t has_target_register, uint8_t target_register_kind, uint8_t target_register) {
  size_t index;
  if (lookup == NULL) return;
  for (index = 0U; index < lookup->auto_structured_data_item_count; ++index) {
    M68kAnalysisStructuredDataItem *item = &lookup->auto_structured_data_items[index];
    if (item->has_section_index && item->section_index == (uint32_t)section_index && item->offset == offset) {
      if (has_index_register) {
        item->has_index_register = 1U;
        item->index_register_kind = index_register_kind;
        item->index_register = index_register;
      }
      if (has_target_register) {
        item->has_target_register = 1U;
        item->target_register_kind = target_register_kind;
        item->target_register = target_register;
      }
    }
  }
}

static uint8_t render_lookup_table_entry_count_proof_rank(uint8_t proof_id) {
  switch (proof_id) {
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_UNKNOWN:
      return 0U;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_STRUCTURED_RANGE:
      return 1U;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_CONSUMER_STRUCTURAL_SCAN:
      return 2U;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_INDEX_MASK_DOMAIN:
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_INDEX_COMPARE_DOMAIN:
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_LOOP_LIMIT:
      return 3U;
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_RELOCATION_RECORD:
    case M68K_ANALYSIS_TABLE_ENTRY_COUNT_PROOF_PLATFORM_RECORD:
      return 4U;
    default:
      return 0U;
  }
}

static void render_lookup_set_entry_count_proof_if_stronger(M68kAnalysisStructuredDataItem *item, uint8_t proof_id) {
  if (item == NULL) return;
  if (render_lookup_table_entry_count_proof_rank(proof_id) >=
      render_lookup_table_entry_count_proof_rank(item->entry_count_proof_id)) {
    item->entry_count_proof_id = proof_id;
    item->table_stop_reason_id = m68k_analysis_table_stop_reason_for_entry_count_proof(proof_id);
  }
}

static uint8_t render_lookup_structured_data_source_pattern_rank(uint8_t source_pattern_id) {
  switch (source_pattern_id) {
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_UNKNOWN:
      return 0U;
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_READ:
      return 1U;
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_WORD_DISPATCH:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_PC_RELATIVE_INDEXED_INDIRECT_DISPATCH:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_RELOCATION_POINTER_TABLE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MACOS_SYMBOL_RECORD:
      return 4U;
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_LOCAL_POINTER_READ:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_INDEXED_LOCAL_SCALAR_READ:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_POSTINCREMENT_READ_SEQUENCE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_KEYED_LONG_RELATIVE_DISPATCH:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_STRING_TABLE_SEQUENCE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_POINTER_STRING_TABLE:
    case M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_WORD_OFFSET_STRING_TABLE:
      return 3U;
    default:
      return 2U;
  }
}

static void render_lookup_set_auto_structured_data_item_source_pattern(M68kRenderLookup *lookup,
    size_t section_index, uint32_t offset, uint8_t source_pattern_id) {
  size_t index;
  const char *source_pattern = m68k_analysis_structured_data_source_pattern_name(source_pattern_id);
  if (lookup == NULL || source_pattern == NULL || source_pattern[0] == '\0') return;
  for (index = 0U; index < lookup->auto_structured_data_item_count; ++index) {
    M68kAnalysisStructuredDataItem *item = &lookup->auto_structured_data_items[index];
    if (item->has_section_index && item->section_index == (uint32_t)section_index &&
        item->offset == offset) {
      if (render_lookup_structured_data_source_pattern_rank(item->source_pattern_id) >
          render_lookup_structured_data_source_pattern_rank(source_pattern_id)) {
        continue;
      }
      item->source_pattern_id = source_pattern_id;
      render_lookup_set_entry_count_proof_if_stronger(item,
        m68k_analysis_table_entry_count_proof_for_source_pattern(source_pattern_id));
      (void)m68k_analysis_structured_data_item_set_text(item,
        M68K_ANALYSIS_STRUCTURED_DATA_TEXT_SOURCE_PATTERN, source_pattern, strlen(source_pattern));
      m68k_analysis_structured_data_item_refresh_table_metadata(item);
    }
  }
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
  if (amiga_os_find_library_base_name(library_name) == NULL) return 0;
  library_id = amiga_os_name_id(M68K_PLATFORM_NAME_LIBRARY, library_name);
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
    const AmigaOsCallInputInfo *input) {
  size_t index;
  M68kRenderRecoveredFunctionArg *grown;
  size_t next_capacity;
  if (lookup == NULL || input == NULL || stack_offset == 0U || reg_kind == 0U || reg_index >= 8U) return 0;
  for (index = 0U; index < lookup->recovered_function_arg_count; ++index) {
    M68kRenderRecoveredFunctionArg *entry = &lookup->recovered_function_args[index];
    if (entry->section_index == section_index && entry->function_offset == function_offset &&
        entry->stack_offset == stack_offset && entry->reg_kind == reg_kind && entry->reg_index == reg_index) {
      if (entry->input != input) entry->input = NULL;
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
  lookup->recovered_function_args[lookup->recovered_function_arg_count].input = input;
  ++lookup->recovered_function_arg_count;
  return 0;
}

int render_lookup_add_recovered_local_call_summary(M68kRenderLookup *lookup, size_t section_index,
    uint32_t target_offset, const AmigaOsLibraryVectorInfo *vector) {
  size_t index;
  M68kRenderRecoveredLocalCallSummary *grown;
  size_t next_capacity;
  if (lookup == NULL || vector == NULL) return 0;
  for (index = 0U; index < lookup->recovered_local_call_summary_count; ++index) {
    M68kRenderRecoveredLocalCallSummary *entry = &lookup->recovered_local_call_summaries[index];
    if (entry->section_index == section_index && entry->target_offset == target_offset) {
      if (entry->vector != vector) entry->vector = NULL;
      return 0;
    }
  }
  if (lookup->recovered_local_call_summary_count == lookup->recovered_local_call_summary_capacity) {
    next_capacity = lookup->recovered_local_call_summary_capacity == 0U ? 16U :
      lookup->recovered_local_call_summary_capacity * 2U;
    grown = (M68kRenderRecoveredLocalCallSummary *)render_lookup_grow_array(lookup,
      lookup->recovered_local_call_summaries, lookup->recovered_local_call_summary_count, sizeof(*grown),
      next_capacity);
    if (grown == NULL) return -1;
    lookup->recovered_local_call_summaries = grown;
    lookup->recovered_local_call_summary_capacity = next_capacity;
  }
  memset(&lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count], 0,
    sizeof(lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count]));
  lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count].section_index = section_index;
  lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count].target_offset = target_offset;
  lookup->recovered_local_call_summaries[lookup->recovered_local_call_summary_count].vector = vector;
  ++lookup->recovered_local_call_summary_count;
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
      changed = 1;
    }
  }
  if (slot->conflicted != 0U) {
    slot->conflicted = 1U;
    slot->value.known = 0U;
    slot->value.output = NULL;
    changed = 1;
  } else {
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
    if (value->app_address_known) {
      if (!slot->value.app_address_known) {
        slot->value.app_address_known = 1U;
        slot->value.app_displacement = value->app_displacement;
        changed = 1;
      } else if (slot->value.app_displacement != value->app_displacement) {
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
    const M68kRenderResolvedStructField *field, const M68kRenderTypedProvenance *provenance) {
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
  lookup->typed_accesses[lookup->typed_access_count].inherited = field->inherited;
  lookup->typed_accesses[lookup->typed_access_count].nested = field->nested;
  if (provenance != NULL) {
    lookup->typed_accesses[lookup->typed_access_count].provenance = *provenance;
  }
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
    displacement, amiga_struct_size_for_struct_id(root_struct_id), &resolved, provenance);
}

static int render_lookup_add_unresolved_typed_access_by_names(M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint8_t operand_index, uint8_t base_reg, int16_t displacement, const char *root_struct_name,
    uint16_t struct_size, uint8_t classification, uint16_t container_candidate_count,
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
    uint8_t operand_index, uint8_t base_reg, int16_t displacement, uint16_t root_struct_id,
    uint16_t struct_size, uint8_t refinement_applied, uint16_t refined_struct_id,
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
  classify_unresolved_typed_access(root_struct_id, displacement, struct_size, 0U, &classification,
    &container_candidate_count, container_struct_name, sizeof(container_struct_name), container_field_expr,
    sizeof(container_field_expr), NULL);
  if (refinement_applied != 0U && refined_struct_id != AMIGA_OS_STRUCT_ID_NONE) {
    refined_struct_name = amiga_os_name(M68K_PLATFORM_NAME_STRUCT, refined_struct_id);
    if (refined_struct_name == NULL || refined_struct_name[0] == '\0') {
      refinement_applied = 0U;
      refined_struct_id = AMIGA_OS_STRUCT_ID_NONE;
    } else {
      classification = M68K_PLATFORM_UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION;
      snprintf(container_struct_name, sizeof(container_struct_name), "%s", refined_struct_name);
      (void)amiga_os_resolve_struct_field_symbol_expr_by_struct_id(refined_struct_id, displacement, 0,
        container_field_expr, sizeof(container_field_expr));
    }
  }
  return render_lookup_add_unresolved_typed_access_by_names(lookup, section_index, offset, operand_index, base_reg,
    displacement, root_struct_name, struct_size, classification, container_candidate_count, container_struct_name,
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
  base_name = amiga_os_find_library_base_name(library_name);
  return base_name != NULL && base_name[0] != '\0' ? base_name : NULL;
}

static const char *amiga_library_base_name_for_render_effect_id(uint16_t library_id) {
  const char *library_name = library_id != 0U ? amiga_os_name(M68K_PLATFORM_NAME_LIBRARY, library_id) : NULL;
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

static int candidate_local_call_target(const M68kDecodeSectionIR *section, const M68kDecodeCandidate *candidate,
    uint32_t *out_target_offset) {
  size_t target_index;
  if (out_target_offset != NULL) *out_target_offset = 0U;
  if (section == NULL || candidate == NULL || out_target_offset == NULL) return 0;
  for (target_index = 0U; target_index < candidate->target_count; ++target_index) {
    const M68kDecodeTarget *target = &candidate->targets[target_index];
    if (target->kind == M68K_DECODE_TARGET_CALL && target->has_section &&
        target->section_index == section->section_index && target->offset < section->size) {
      *out_target_offset = target->offset;
      return 1;
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

static int instruction_writes_address_register_mask_local(const M68kInstructionIR *instruction, uint8_t mask) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  uint8_t operand_reg = 0U;
  if (instruction == NULL || mask == 0U) return 1;
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 1;
  for (operand_index = 0U; operand_index < instruction->operand_count && operand_index < 4U; ++operand_index) {
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_WRITE &&
        operand_address_register_index_local(&instruction->operands[operand_index], &operand_reg) &&
        operand_reg < 8U && (mask & (uint8_t)(1U << operand_reg)) != 0U) {
      return 1;
    }
    if (metadata->operand_access_kinds[operand_index] == M68K_SIM_ACCESS_REGISTER_LIST_WRITE) {
      uint8_t reg;
      for (reg = 0U; reg < 8U; ++reg) {
        if ((mask & (uint8_t)(1U << reg)) != 0U &&
            reglist_contains_address_register_local(&instruction->operands[operand_index], reg)) {
          return 1;
        }
      }
    }
    if (metadata->operand_ea_register_updates[operand_index] != M68K_SIM_EA_UPDATE_NONE &&
        operand_is_address_memory_local(&instruction->operands[operand_index], &operand_reg, NULL) &&
        operand_reg < 8U && (mask & (uint8_t)(1U << operand_reg)) != 0U) {
      return 1;
    }
  }
  return 0;
}

static int local_callee_preserves_address_register_mask_with_depth(const M68kDecodeSectionIR *section,
    const uint8_t *accepted_start, uint32_t target_offset, uint8_t mask, uint8_t depth) {
  uint32_t worklist[64];
  uint32_t visited[64];
  uint8_t work_count = 0U;
  uint8_t visited_count = 0U;
  uint8_t visited_any = 0U;
  if (section == NULL || accepted_start == NULL || target_offset >= section->size || mask == 0U || depth > 4U)
    return 0;
  worklist[work_count++] = target_offset;
  while (work_count != 0U) {
    uint32_t cursor = worklist[--work_count];
    uint8_t step;
    for (step = 0U; step < 32U && cursor < section->size && accepted_start[cursor] != 0U; ++step) {
      const M68kDecodeCandidate *candidate;
      M68kInstructionIR instruction;
      const M68kSimFormMetadata *metadata;
      uint32_t target = 0U;
      uint8_t seen = 0U;
      uint8_t index;
      for (index = 0U; index < visited_count; ++index) {
        if (visited[index] == cursor) {
          seen = 1U;
          break;
        }
      }
      if (seen) break;
      if (visited_count >= (uint8_t)(sizeof(visited) / sizeof(visited[0]))) return 0;
      visited[visited_count++] = cursor;
      visited_any = 1U;
      candidate = find_candidate_at_offset_local(section, cursor);
      if (candidate == NULL || candidate->byte_count == 0U ||
          m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) {
        return 0;
      }
      metadata = m68k_sim_metadata_for_instruction(&instruction);
      if (metadata == NULL || instruction_writes_address_register_mask_local(&instruction, mask)) return 0;
      if (metadata->flow_kind == M68K_SIM_FLOW_CALL) {
        if (!candidate_local_call_target(section, candidate, &target) ||
            !local_callee_preserves_address_register_mask_with_depth(section, accepted_start, target, mask,
              (uint8_t)(depth + 1U))) {
          return 0;
        }
      } else if (candidate_first_local_control_target(section, candidate, &target)) {
        if (metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
            (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U)) {
          cursor = target;
          continue;
        }
        if (work_count >= (uint8_t)(sizeof(worklist) / sizeof(worklist[0]))) return 0;
        worklist[work_count++] = target;
      }
      if (metadata->flow_kind == M68K_SIM_FLOW_RETURN) break;
      if (metadata->flow_kind == M68K_SIM_FLOW_JUMP ||
          (metadata->flow_kind == M68K_SIM_FLOW_BRANCH && metadata->flow_conditional == 0U) ||
          metadata->flow_kind == M68K_SIM_FLOW_TRAP) {
        break;
      }
      if (candidate->byte_count > section->size - cursor) break;
      cursor += candidate->byte_count;
    }
  }
  return visited_any != 0U;
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

static uint32_t render_lookup_structured_item_role_flags_local(const M68kAnalysisStructuredDataItem *item) {
  if (item == NULL) return 0U;
  return item->semantic_role_flags;
}

static int render_lookup_structured_item_is_long_label_table_local(const M68kAnalysisStructuredDataItem *item) {
  uint32_t role_flags = render_lookup_structured_item_role_flags_local(item);
  return item != NULL && item->kind == M68K_ANALYSIS_STRUCTURED_DATA_LONGS &&
    (role_flags & (M68K_ANALYSIS_STRUCTURED_DATA_ROLE_POINTER_TABLE |
      M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LOOKUP_TABLE)) != 0U;
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

static int render_lookup_add_pointer_table_target_labels_for_item(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, uint8_t **accepted_bytes,
    const M68kAnalysisStructuredDataItem *item) {
  const M68kDecodeSectionIR *section;
  size_t section_index;
  uint32_t cursor;
  uint32_t available;
  if (lookup == NULL || decode == NULL || accepted_bytes == NULL ||
      !render_lookup_structured_item_is_long_label_table_local(item)) {
    return 0;
  }
  section_index = item->has_section_index ? (size_t)item->section_index : 0U;
  if (section_index >= decode->section_count) return 0;
  section = &decode->sections[section_index];
  if (section->data == NULL || item->offset >= section->size) return 0;
  available = section->size - item->offset;
  if (available > item->size) available = item->size;
  for (cursor = 0U; cursor + 4U <= available; cursor += 4U) {
    uint32_t value = m68k_read_u32be(section->data + item->offset + cursor);
    uint32_t target_offset = 0U;
    if (value == 0U) continue;
    if (!render_lookup_pointer_value_to_source_offset(lookup, section, value, &target_offset)) continue;
    if (!render_lookup_pointer_table_target_can_take_auto_label(lookup, section, accepted_start[section_index],
        accepted_bytes[section_index], target_offset)) {
      continue;
    }
    render_lookup_mark_label(lookup, section_index, target_offset);
    render_lookup_mark_label_target_ref(lookup, section_index, target_offset);
  }
  return 0;
}

static int render_lookup_add_pointer_table_target_labels(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start, uint8_t **accepted_bytes) {
  size_t index;
  if (lookup == NULL || decode == NULL || accepted_bytes == NULL) return 0;
  for (index = 0U; index < lookup->range_ownership_count; ++index) {
    M68kRenderRangeOwnershipView range;
    if (!lookup_range_ownership_at_index(lookup, index, &range)) continue;
    if (range.kind != M68K_RANGE_OWNERSHIP_TABLE || range.structured_item == NULL) continue;
    if (render_lookup_add_pointer_table_target_labels_for_item(lookup, decode, accepted_start, accepted_bytes,
        range.structured_item) != 0) {
      return -1;
    }
  }
  return 0;
}

static int auto_string_terminator_byte(uint8_t value) {
  return value == 0U || value == 0xffU;
}

static int auto_string_start_byte(uint8_t value) {
  return (value >= 'A' && value <= 'Z') || (value >= 'a' && value <= 'z') ||
    (value >= '0' && value <= '9') || value == '$' || value == '.' || value == '#';
}

static int auto_string_candidate_start(const M68kDecodeSectionIR *section, uint32_t offset) {
  uint8_t value;
  if (section == NULL || section->data == NULL || offset >= section->size) return 0;
  value = section->data[offset];
  if (m68k_ir_byte_is_quoted_string_safe(value) && auto_string_start_byte(value)) return 1;
  return value >= 4U && value <= 80U && offset + 1U < section->size &&
    auto_string_start_byte(section->data[offset + 1U]);
}

static int auto_string_lowercase_byte(uint8_t value) {
  return value >= 'a' && value <= 'z';
}

static int auto_string_alpha_byte(uint8_t value) {
  return (value >= 'A' && value <= 'Z') || (value >= 'a' && value <= 'z');
}

static int lookup_has_anchor_local(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  return lookup != NULL && section_index < lookup->section_count && lookup->anchors != NULL &&
    lookup->anchor_extents != NULL && offset < lookup->anchor_extents[section_index] &&
    lookup->anchors[section_index] != NULL && lookup->anchors[section_index][offset] != NULL;
}

static int auto_string_interior_clear(const M68kRenderLookup *lookup, size_t section_index, uint32_t offset) {
  M68kRenderRangeOwnershipView range;
  if (lookup == NULL) return 0;
  return !lookup_has_label(lookup, section_index, offset) &&
    lookup_relocation_at(lookup, section_index, offset) == NULL &&
    !lookup_has_anchor_local(lookup, section_index, offset) &&
    !lookup_range_ownership_covering_offset(lookup, section_index, offset, &range);
}

static int auto_string_interior_clear_for_refined_span_start(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t span_start, uint32_t offset) {
  M68kRenderRangeOwnershipView range;
  const M68kAnalysisStructuredDataItem *item = NULL;
  if (lookup == NULL) return 0;
  if (lookup_range_ownership_covering_offset(lookup, section_index, offset, &range)) {
    item = range.structured_item;
  }
  if (item != NULL &&
      !(range.start_offset == span_start && structured_data_item_is_untyped_bytes_placeholder_local(item))) {
    return 0;
  }
  return !lookup_has_label(lookup, section_index, offset) &&
    lookup_relocation_at(lookup, section_index, offset) == NULL &&
    !lookup_has_anchor_local(lookup, section_index, offset);
}

static int auto_string_range_has_code_byte(const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes,
    uint32_t offset, uint32_t size) {
  uint32_t cursor;
  if (section == NULL || offset > section->size || size > section->size - offset) return 1;
  if (accepted_bytes == NULL) return section->kind == M68K_SECTION_CODE;
  for (cursor = 0U; cursor < size; ++cursor) {
    if (accepted_bytes[offset + cursor] != 0U) return 1;
  }
  return 0;
}

static int auto_macos_symbol_string_record_span(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset,
    uint32_t *out_span) {
  uint32_t length;
  uint32_t cursor;
  uint32_t padding_count = 0U;
  if (out_span != NULL) *out_span = 0U;
  if (lookup == NULL || lookup->object == NULL ||
      lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_MACOS ||
      section == NULL || section->data == NULL || accepted_bytes == NULL || out_span == NULL ||
      offset >= section->size || (section->data[offset] & 0x80U) == 0U) {
    return 0;
  }
  length = section->data[offset] & 0x7FU;
  if (length < 3U || offset + 1U > section->size || length > section->size - offset - 1U)
    return 0;
  if (!auto_string_start_byte(section->data[offset + 1U])) return 0;
  {
    M68kRenderRangeOwnershipView range;
    if (lookup_relocation_at(lookup, section->section_index, offset) != NULL ||
        lookup_has_anchor_local(lookup, section->section_index, offset) ||
        lookup_range_ownership_covering_offset(lookup, section->section_index, offset, &range)) {
      return 0;
    }
  }
  for (cursor = 0U; cursor < length; ++cursor) {
    uint32_t payload_offset = offset + 1U + cursor;
    if (!m68k_ir_byte_is_quoted_string_safe(section->data[payload_offset])) return 0;
    if (!auto_string_interior_clear(lookup, section->section_index, payload_offset)) return 0;
  }
  cursor = offset + 1U + length;
  while (cursor < section->size && section->data[cursor] == 0U && padding_count < 3U &&
      auto_string_interior_clear(lookup, section->section_index, cursor)) {
    ++cursor;
    ++padding_count;
  }
  if (auto_string_range_has_code_byte(section, accepted_bytes, offset, cursor - offset)) return 0;
  *out_span = cursor - offset;
  return 1;
}

static int render_lookup_maybe_add_macos_symbol_string(M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset,
    uint32_t *out_size) {
  uint32_t span = 0U;
  if (out_size != NULL) *out_size = 0U;
  if (lookup == NULL || section == NULL || out_size == NULL) return 0;
  if (!auto_macos_symbol_string_record_span(lookup, section, accepted_bytes, offset, &span)) return 0;
  if (render_lookup_add_auto_structured_data_item(lookup, section->section_index, offset, span,
      M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING |
        M68K_ANALYSIS_STRUCTURED_DATA_ROLE_LENGTH_PREFIXED_STRING |
        M68K_ANALYSIS_STRUCTURED_DATA_ROLE_MACOS_SYMBOL_STRING,
      M68K_ANALYSIS_STRUCTURED_DATA_STRING) != 0) {
    return -1;
  }
  render_lookup_set_auto_structured_data_item_source_pattern(lookup, section->section_index, offset,
    M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MACOS_SYMBOL_RECORD);
  *out_size = span;
  return 0;
}

static int auto_string_looks_length_prefixed(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t offset, uint32_t text_size) {
  if (lookup == NULL || section == NULL || section->data == NULL || offset == 0U || text_size > 255U) return 0;
  if (lookup_has_label(lookup, section->section_index, offset)) return 0;
  return section->data[offset - 1U] == (uint8_t)text_size;
}

static int auto_string_looks_length_prefixed_sequence(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t offset, uint32_t text_end) {
  uint32_t cursor;
  uint32_t record_count = 0U;
  if (lookup == NULL || section == NULL || section->data == NULL || offset == 0U || text_end > section->size) return 0;
  if (lookup_has_label(lookup, section->section_index, offset)) return 0;
  cursor = offset - 1U;
  while (cursor < text_end) {
    uint32_t length = section->data[cursor];
    uint32_t payload = cursor + 1U;
    uint32_t index;
    if (length < 4U || payload > text_end || length > text_end - payload) return 0;
    if (!auto_string_start_byte(section->data[payload])) return 0;
    for (index = 0U; index < length; ++index) {
      if (!m68k_ir_byte_is_quoted_string_safe(section->data[payload + index])) return 0;
    }
    cursor = payload + length;
    ++record_count;
  }
  return cursor == text_end && record_count > 1U;
}

enum {
  AUTO_STRING_RECORD_CONTEXT_NONE = 0,
  AUTO_STRING_RECORD_CONTEXT_ADJACENT_TABLE = 1,
  AUTO_STRING_RECORD_CONTEXT_CONTROL_STREAM = 2
};

static int auto_string_record_sequence_context_kind(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t offset) {
  size_t index;
  uint32_t prior_count = 0U;
  uint32_t nearest_end = 0U;
  if (lookup == NULL || section == NULL || section->data == NULL || offset == 0U) return 0;
  for (index = 0U; index < lookup->range_ownership_count; ++index) {
    M68kRenderRangeOwnershipView range;
    const M68kAnalysisStructuredDataItem *item;
    uint32_t item_end;
    if (!lookup_range_ownership_at_index(lookup, index, &range)) continue;
    if (range.kind != M68K_RANGE_OWNERSHIP_TEXT || range.section_index != section->section_index) continue;
    item = range.structured_item;
    if (item == NULL ||
        (item->semantic_role_flags & M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING) == 0U ||
        item->offset > offset || item->size == 0U || item->size > offset - item->offset) {
      continue;
    }
    item_end = item->offset + item->size;
    if (item_end > offset || offset - item_end > 192U) continue;
    ++prior_count;
    if (item_end > nearest_end) nearest_end = item_end;
  }
  if (prior_count < 2U || nearest_end == 0U || nearest_end > offset || offset - nearest_end > 8U) return 0;
  if (nearest_end == offset) return AUTO_STRING_RECORD_CONTEXT_ADJACENT_TABLE;
  for (index = nearest_end; index < offset; ++index) {
    if (!m68k_ir_byte_is_quoted_string_safe(section->data[index]) || auto_string_terminator_byte(section->data[index])) {
      return AUTO_STRING_RECORD_CONTEXT_CONTROL_STREAM;
    }
  }
  return AUTO_STRING_RECORD_CONTEXT_NONE;
}

static int auto_string_has_record_sequence_context(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, uint32_t offset) {
  return auto_string_record_sequence_context_kind(lookup, section, offset) != AUTO_STRING_RECORD_CONTEXT_NONE;
}

static int auto_string_has_nearby_terminal_code_context(const M68kDecodeSectionIR *section, uint32_t offset) {
  uint32_t start;
  uint32_t cursor;
  uint32_t immediate_store_terminal_count = 0U;
  int has_epilogue_context = 0;
  if (section == NULL || section->data == NULL || section->kind != M68K_SECTION_CODE || offset < 2U) return 0;
  start = offset > 64U ? offset - 64U : 0U;
  for (cursor = start; cursor + 1U < offset; ++cursor) {
    if (section->data[cursor] == 0x4eU && section->data[cursor + 1U] == 0x75U) {
      if (cursor >= start + 8U && section->data[cursor - 8U] == 0x2dU && section->data[cursor - 7U] == 0x7cU) {
        ++immediate_store_terminal_count;
      }
    }
    if (cursor + 3U < offset && section->data[cursor] == 0x4cU && section->data[cursor + 1U] == 0xdfU) {
      has_epilogue_context = 1;
    }
  }
  return immediate_store_terminal_count >= 1U || has_epilogue_context;
}

static uint32_t auto_renderable_string_span_with_options(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset,
    uint32_t min_text_size, int require_space) {
  uint32_t cursor;
  uint32_t text_size = 0U;
  int has_space = 0;
  int has_lowercase = 0;
  int has_record_sequence_context;
  if (lookup == NULL || section == NULL || section->data == NULL || offset >= section->size ||
      !m68k_ir_byte_is_quoted_string_safe(section->data[offset]) || !auto_string_start_byte(section->data[offset])) {
    return 0U;
  }
  has_record_sequence_context = auto_string_has_record_sequence_context(lookup, section, offset);
  if (offset > 0U && m68k_ir_byte_is_quoted_string_safe(section->data[offset - 1U]) &&
      !lookup_has_label(lookup, section->section_index, offset) &&
      !has_record_sequence_context) {
    return 0U;
  }
  if (!lookup_has_label(lookup, section->section_index, offset) &&
      !lookup_has_anchor_local(lookup, section->section_index, offset) &&
      auto_string_has_nearby_terminal_code_context(section, offset)) {
    return 0U;
  }
  cursor = offset;
  while (cursor < section->size && m68k_ir_byte_is_quoted_string_safe(section->data[cursor])) {
    if (cursor != offset && !auto_string_interior_clear(lookup, section->section_index, cursor)) return 0U;
    if (section->data[cursor] == ' ') has_space = 1;
    if (auto_string_lowercase_byte(section->data[cursor])) has_lowercase = 1;
    ++cursor;
    ++text_size;
  }
  if (cursor >= section->size || !auto_string_terminator_byte(section->data[cursor]) ||
      text_size < min_text_size || (require_space && !has_space && !has_record_sequence_context))
    return 0U;
  if (auto_string_looks_length_prefixed(lookup, section, offset, text_size)) return 0U;
  if (auto_string_looks_length_prefixed_sequence(lookup, section, offset, cursor)) return 0U;
  if (section->data[cursor] == 0xffU && has_lowercase) return 0U;
  if (!auto_string_interior_clear(lookup, section->section_index, cursor)) return 0U;
  if (auto_string_range_has_code_byte(section, accepted_bytes, offset, text_size + 1U)) return 0U;
  return text_size + 1U;
}

static uint32_t auto_renderable_string_span(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset) {
  return auto_renderable_string_span_with_options(lookup, section, accepted_bytes, offset, 8U, 1);
}

static int auto_string_line_break_byte(uint8_t value) {
  return value == 0x0dU || value == 0x0aU;
}

static uint32_t auto_renderable_line_terminated_string_span(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset,
    uint32_t min_text_size, int require_space, int record_context_kind) {
  uint32_t cursor;
  uint32_t text_size = 0U;
  uint32_t break_count = 0U;
  int has_space = 0;
  int has_lowercase = 0;
  int has_boundary_evidence;
  if (lookup == NULL || section == NULL || section->data == NULL || offset >= section->size ||
      !m68k_ir_byte_is_quoted_string_safe(section->data[offset]) || !auto_string_start_byte(section->data[offset])) {
    return 0U;
  }
  has_boundary_evidence = record_context_kind == AUTO_STRING_RECORD_CONTEXT_ADJACENT_TABLE ||
    lookup_has_label(lookup, section->section_index, offset) ||
    lookup_has_anchor_local(lookup, section->section_index, offset);
  if (!has_boundary_evidence) return 0U;
  if (offset > 0U && m68k_ir_byte_is_quoted_string_safe(section->data[offset - 1U]) &&
      !lookup_has_label(lookup, section->section_index, offset) &&
      !lookup_has_anchor_local(lookup, section->section_index, offset)) {
    return 0U;
  }
  if (!lookup_has_label(lookup, section->section_index, offset) &&
      !lookup_has_anchor_local(lookup, section->section_index, offset) &&
      auto_string_has_nearby_terminal_code_context(section, offset)) {
    return 0U;
  }
  cursor = offset;
  while (cursor < section->size && m68k_ir_byte_is_quoted_string_safe(section->data[cursor])) {
    if (cursor != offset && !auto_string_interior_clear(lookup, section->section_index, cursor)) return 0U;
    if (section->data[cursor] == ' ') has_space = 1;
    if (auto_string_lowercase_byte(section->data[cursor])) has_lowercase = 1;
    ++cursor;
    ++text_size;
  }
  while (cursor < section->size && auto_string_line_break_byte(section->data[cursor]) && break_count < 2U) {
    if (!auto_string_interior_clear(lookup, section->section_index, cursor)) return 0U;
    ++cursor;
    ++break_count;
  }
  if (break_count == 0U || cursor >= section->size || !auto_string_terminator_byte(section->data[cursor]) ||
      text_size < min_text_size || (require_space && !has_space && record_context_kind == AUTO_STRING_RECORD_CONTEXT_NONE)) {
    return 0U;
  }
  if (auto_string_looks_length_prefixed(lookup, section, offset, text_size)) return 0U;
  if (auto_string_looks_length_prefixed_sequence(lookup, section, offset, cursor)) return 0U;
  if (section->data[cursor] == 0xffU && has_lowercase) return 0U;
  if (!auto_string_interior_clear(lookup, section->section_index, cursor)) return 0U;
  if (auto_string_range_has_code_byte(section, accepted_bytes, offset, cursor - offset + 1U)) return 0U;
  return cursor - offset + 1U;
}

static int auto_multiline_text_byte(uint8_t value) {
  return m68k_ir_byte_is_quoted_string_safe(value) || value == 0x0dU || value == 0x0aU || value == 0x09U;
}

static int auto_multiline_text_start(const M68kDecodeSectionIR *section, uint32_t offset) {
  uint32_t cursor;
  if (section == NULL || section->data == NULL || offset >= section->size) return 0;
  if (section->data[offset] == 0x0dU) return 1;
  if (!m68k_ir_byte_is_quoted_string_safe(section->data[offset])) return 0;
  cursor = offset;
  while (cursor < section->size && (section->data[cursor] == ' ' || section->data[cursor] == 0x09U)) {
    ++cursor;
  }
  return cursor < section->size && auto_string_start_byte(section->data[cursor]);
}

static int lookup_range_ownership_starts_at(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  M68kRenderRangeOwnershipView range;
  if (lookup == NULL) return 0;
  return lookup_range_ownership_at_offset(lookup, section_index, offset, &range) &&
    range.start_offset == offset;
}

static int auto_multiline_text_boundary_at(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  if (lookup == NULL) return 0;
  return lookup_has_label(lookup, section_index, offset) ||
    lookup_has_anchor_local(lookup, section_index, offset) ||
    lookup_range_ownership_starts_at(lookup, section_index, offset);
}

static int auto_multiline_text_shape_ok(uint32_t text_size, uint32_t alpha_count,
    uint32_t line_break_count, uint32_t text_line_count, int has_space) {
  return text_size >= 24U && alpha_count >= 12U && line_break_count >= 2U &&
    text_line_count >= 2U && has_space;
}

static uint32_t auto_renderable_multiline_string_span(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset) {
  uint32_t cursor;
  uint32_t text_size = 0U;
  uint32_t alpha_count = 0U;
  uint32_t line_break_count = 0U;
  uint32_t text_line_count = 0U;
  int has_space = 0;
  int previous_was_break = 1;
  if (lookup == NULL || section == NULL || section->data == NULL || offset >= section->size ||
      !auto_multiline_text_start(section, offset)) {
    return 0U;
  }
  if (section->kind == M68K_SECTION_CODE &&
      !lookup_has_label(lookup, section->section_index, offset) &&
      !lookup_has_anchor_local(lookup, section->section_index, offset)) {
    return 0U;
  }
  cursor = offset;
  while (cursor < section->size && auto_multiline_text_byte(section->data[cursor])) {
    uint8_t value = section->data[cursor];
    if (cursor != offset &&
        !auto_string_interior_clear_for_refined_span_start(lookup, section->section_index, offset, cursor)) {
      if (auto_multiline_text_boundary_at(lookup, section->section_index, cursor) &&
          auto_multiline_text_shape_ok(text_size, alpha_count, line_break_count, text_line_count, has_space) &&
          !auto_string_range_has_code_byte(section, accepted_bytes, offset, cursor - offset)) {
        return cursor - offset;
      }
      return 0U;
    }
    if (value == 0x0dU || value == 0x0aU) {
      ++line_break_count;
      previous_was_break = 1;
    } else {
      ++text_size;
      if (previous_was_break && m68k_ir_byte_is_quoted_string_safe(value)) ++text_line_count;
      previous_was_break = 0;
      if (value == ' ') has_space = 1;
      if (auto_string_alpha_byte(value)) ++alpha_count;
    }
    ++cursor;
  }
  if (cursor >= section->size || section->data[cursor] != 0U ||
      !auto_multiline_text_shape_ok(text_size, alpha_count, line_break_count, text_line_count, has_space)) {
    return 0U;
  }
  if (!auto_string_interior_clear_for_refined_span_start(lookup, section->section_index, offset, cursor))
    return 0U;
  if (auto_string_range_has_code_byte(section, accepted_bytes, offset, cursor - offset + 1U)) return 0U;
  return cursor - offset + 1U;
}

static int render_lookup_add_auto_string_item(M68kRenderLookup *lookup, size_t section_index, uint32_t offset,
    uint32_t span, uint32_t role_flags, uint8_t source_pattern_id) {
  if (render_lookup_add_auto_structured_data_item(lookup, section_index, offset, span, role_flags,
      M68K_ANALYSIS_STRUCTURED_DATA_STRING) != 0) {
    return -1;
  }
  render_lookup_set_auto_structured_data_item_source_pattern(lookup, section_index, offset, source_pattern_id);
  return 0;
}

static uint8_t source_pattern_for_string_record_context(int context_kind, uint8_t fallback_pattern_id) {
  if (context_kind == AUTO_STRING_RECORD_CONTEXT_CONTROL_STREAM)
    return M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_CONTROL_STRING_STREAM;
  if (context_kind == AUTO_STRING_RECORD_CONTEXT_ADJACENT_TABLE)
    return M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_STRING_TABLE_SEQUENCE;
  return fallback_pattern_id;
}

static uint32_t role_flags_for_string_record_context(int context_kind) {
  uint32_t role_flags = M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING;
  if (context_kind == AUTO_STRING_RECORD_CONTEXT_CONTROL_STREAM)
    role_flags |= M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING_CONTROL_STREAM;
  return role_flags;
}

static int auto_bounded_string_has_text_shape(const M68kDecodeSectionIR *section, uint32_t offset,
    uint32_t size) {
  uint32_t cursor;
  uint32_t text_size = size;
  uint32_t alpha_count = 0U;
  int has_space = 0;
  int has_dot = 0;
  if (section == NULL || section->data == NULL || size < 6U || size > 64U ||
      offset > section->size || size > section->size - offset) {
    return 0;
  }
  if (auto_string_terminator_byte(section->data[offset + size - 1U])) --text_size;
  if (text_size < 6U) return 0;
  for (cursor = 0U; cursor < text_size; ++cursor) {
    uint8_t value = section->data[offset + cursor];
    if (!m68k_ir_byte_is_quoted_string_safe(value)) return 0;
    if ((value >= 'A' && value <= 'Z') || (value >= 'a' && value <= 'z')) ++alpha_count;
    if (value == ' ') has_space = 1;
    if (value == '.') has_dot = 1;
  }
  return alpha_count >= 4U && (has_space || has_dot || alpha_count == text_size);
}

static uint32_t auto_renderable_bounded_string_span(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset) {
  uint32_t cursor;
  uint32_t span;
  if (lookup == NULL || section == NULL || section->data == NULL || offset >= section->size ||
      !(lookup_has_label(lookup, section->section_index, offset) ||
        lookup_has_anchor_local(lookup, section->section_index, offset))) {
    return 0U;
  }
  cursor = offset;
  while (cursor < section->size && m68k_ir_byte_is_quoted_string_safe(section->data[cursor]) &&
      accepted_range_has_code_byte(accepted_bytes, section->size, cursor, 1U) == 0 &&
      lookup_relocation_at(lookup, section->section_index, cursor) == NULL &&
      (cursor == offset || !lookup_has_label(lookup, section->section_index, cursor)) &&
      (cursor == offset || !lookup_has_anchor_local(lookup, section->section_index, cursor))) {
    M68kRenderRangeOwnershipView range;
    if (lookup_range_ownership_covering_offset(lookup, section->section_index, cursor, &range)) break;
    ++cursor;
  }
  span = cursor - offset;
  if (cursor < section->size && auto_string_terminator_byte(section->data[cursor]) &&
      auto_string_interior_clear(lookup, section->section_index, cursor) &&
      accepted_range_has_code_byte(accepted_bytes, section->size, cursor, 1U) == 0) {
    ++span;
  }
  if (!auto_bounded_string_has_text_shape(section, offset, span)) return 0U;
  if (!auto_string_has_record_sequence_context(lookup, section, offset) &&
      auto_string_has_nearby_terminal_code_context(section, offset)) {
    return 0U;
  }
  return span;
}

int m68k_analysis_render_lookup_materialize_pointer_table_targets(M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start, uint8_t **accepted_bytes) {
  return render_lookup_add_pointer_table_target_labels(lookup, decode, accepted_start, accepted_bytes);
}

static int auto_structured_data_item_blocks_candidate_start(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset) {
  M68kRenderRangeOwnershipView range;
  const M68kAnalysisStructuredDataItem *item = NULL;
  if (lookup == NULL) return 1;
  if (lookup_range_ownership_covering_offset(lookup, section_index, offset, &range)) {
    item = range.structured_item;
  }
  return item != NULL &&
    !(range.start_offset == offset && structured_data_item_is_untyped_bytes_placeholder_local(item));
}

static int render_lookup_infer_data_strings(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_bytes) {
  size_t section_index;
  if (lookup == NULL || decode == NULL || accepted_bytes == NULL) return 0;
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    uint32_t offset = 0U;
    if (section->data == NULL) continue;
    while (offset < section->size) {
      uint32_t span;
      int record_context_kind;
      if ((accepted_bytes[section_index] == NULL || accepted_bytes[section_index][offset] == 0U) &&
          !auto_structured_data_item_blocks_candidate_start(lookup, section_index, offset)) {
        if (render_lookup_maybe_add_macos_symbol_string(lookup, section, accepted_bytes[section_index], offset,
            &span) != 0) {
          return -1;
        }
      if (span != 0U) {
        offset += span;
        continue;
      }
      span = auto_renderable_multiline_string_span(lookup, section, accepted_bytes[section_index], offset);
      if (span != 0U) {
        if (render_lookup_add_auto_string_item(lookup, section_index, offset, span,
            M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING,
            M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MULTILINE_TEXT) != 0) {
          return -1;
        }
        offset += span;
        continue;
      }
    }
    int candidate_start = auto_string_candidate_start(section, offset) ||
      (m68k_ir_byte_is_quoted_string_safe(section->data[offset]) &&
          (lookup_has_label(lookup, section_index, offset) ||
           lookup_has_anchor_local(lookup, section_index, offset)));
      if ((accepted_bytes[section_index] != NULL && accepted_bytes[section_index][offset] != 0U) ||
          !candidate_start ||
          auto_structured_data_item_blocks_candidate_start(lookup, section_index, offset)) {
        ++offset;
        continue;
      }
      record_context_kind = auto_string_record_sequence_context_kind(lookup, section, offset);
      if ((span = auto_renderable_string_span(lookup, section, accepted_bytes[section_index], offset)) != 0U) {
        if (render_lookup_add_auto_string_item(lookup, section_index, offset, span,
            role_flags_for_string_record_context(record_context_kind),
            source_pattern_for_string_record_context(record_context_kind,
              M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_TERMINATED_TEXT)) != 0) {
          return -1;
        }
        offset += span;
      } else if ((span = auto_renderable_line_terminated_string_span(lookup, section,
          accepted_bytes[section_index], offset, 8U, 1, record_context_kind)) != 0U) {
        if (render_lookup_add_auto_string_item(lookup, section_index, offset, span,
            role_flags_for_string_record_context(record_context_kind),
            source_pattern_for_string_record_context(record_context_kind,
              M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_TERMINATED_TEXT)) != 0) {
          return -1;
        }
        offset += span;
      } else if ((span = auto_renderable_bounded_string_span(lookup, section, accepted_bytes[section_index],
          offset)) != 0U) {
        if (render_lookup_add_auto_string_item(lookup, section_index, offset, span,
            role_flags_for_string_record_context(record_context_kind),
            source_pattern_for_string_record_context(record_context_kind,
              M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_BOUNDED_TEXT)) != 0) {
          return -1;
        }
        offset += span;
      } else {
        ++offset;
      }
    }
  }
  return 0;
}

static int structured_data_kind_for_candidate_size(const M68kDecodeCandidate *candidate, uint32_t *out_size,
    uint8_t *out_kind) {
  if (out_size != NULL) *out_size = 0U;
  if (out_kind != NULL) *out_kind = 0U;
  if (candidate == NULL || out_size == NULL || out_kind == NULL) return 0;
  if (candidate->size_suffix == 'b') {
    *out_size = 1U;
    *out_kind = M68K_ANALYSIS_STRUCTURED_DATA_BYTES;
    return 1;
  }
  if (candidate->size_suffix == 'w') {
    *out_size = 2U;
    *out_kind = M68K_ANALYSIS_STRUCTURED_DATA_WORDS;
    return 1;
  }
  if (candidate->size_suffix == 'l') {
    *out_size = 4U;
    *out_kind = M68K_ANALYSIS_STRUCTURED_DATA_LONGS;
    return 1;
  }
  return 0;
}

static int lookup_range_has_interior_label(const M68kRenderLookup *lookup, size_t section_index,
    uint32_t offset, uint32_t size) {
  uint32_t cursor;
  if (lookup == NULL || size == 0U) return 0;
  for (cursor = offset + 1U; cursor < offset + size; ++cursor) {
    if (lookup_has_label(lookup, section_index, cursor)) return 1;
  }
  return 0;
}

static uint32_t pc_relative_lookup_table_span(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *section, const uint8_t *accepted_bytes, uint32_t offset,
    uint32_t item_size) {
  uint32_t cursor;
  if (lookup == NULL || section == NULL || accepted_bytes == NULL || item_size == 0U ||
      offset > section->size || item_size > section->size - offset) {
    return 0U;
  }
  cursor = offset + item_size;
  while (cursor + item_size <= section->size &&
      !lookup_has_label(lookup, section->section_index, cursor) &&
      !lookup_range_has_interior_label(lookup, section->section_index, cursor, item_size) &&
      !accepted_range_has_code_byte(accepted_bytes, section->size, cursor, item_size)) {
    M68kRenderRangeOwnershipView range;
    if (lookup_range_ownership_covering_offset(lookup, section->section_index, cursor, &range)) break;
    cursor += item_size;
  }
  return cursor - offset;
}

static uint32_t scan_indexed_word_relative_data_table_span(const M68kRenderLookup *lookup,
    const M68kDecodeSectionIR *table_section, const uint8_t *accepted_bytes,
    uint32_t table_offset, const M68kDecodeSectionIR *target_section,
    uint32_t target_base_offset) {
  uint32_t cursor;
  if (lookup == NULL || table_section == NULL || target_section == NULL ||
      table_section->data == NULL || accepted_bytes == NULL ||
      table_offset > table_section->size || 2U > table_section->size - table_offset ||
      target_base_offset >= target_section->size) {
    return 0U;
  }
  for (cursor = table_offset; cursor + 2U <= table_section->size; cursor += 2U) {
    int32_t displacement = (int32_t)(int16_t)m68k_read_u16be(table_section->data + cursor);
    int64_t target_offset_signed = (int64_t)target_base_offset + displacement;
    uint32_t target_offset;
    M68kRenderRangeOwnershipView range;
    if (cursor != table_offset && lookup_has_label(lookup, table_section->section_index, cursor)) break;
    if (lookup_range_has_interior_label(lookup, table_section->section_index, cursor, 2U)) break;
    if (lookup_range_ownership_covering_offset(lookup, table_section->section_index, cursor, &range)) break;
    if (accepted_range_has_code_byte(accepted_bytes, table_section->size, cursor, 2U)) break;
    if (target_offset_signed < 0 || target_offset_signed > UINT32_MAX) break;
    target_offset = (uint32_t)target_offset_signed;
    if (target_offset < target_base_offset || target_offset >= target_section->size) break;
    if (table_section->section_index == target_section->section_index) {
      if (target_base_offset < table_offset && target_offset >= table_offset) break;
      if (table_offset < target_base_offset && cursor >= target_base_offset) break;
    }
  }
  return cursor - table_offset;
}

static int candidate_indexed_read_from_known_local_base(const M68kDecodeSectionIR *section,
    const M68kDecodeCandidate *candidate, const M68kInstructionIR *instruction,
    const M68kRenderDataPointerState *state, size_t *out_section_index, uint32_t *out_offset,
    uint8_t *out_index_register_kind, uint8_t *out_index_register) {
  const M68kSimFormMetadata *metadata;
  size_t operand_index;
  if (out_index_register_kind != NULL) *out_index_register_kind = M68K_ANALYSIS_REGISTER_NONE;
  if (out_index_register != NULL) *out_index_register = 0U;
  if (section == NULL || candidate == NULL || instruction == NULL || state == NULL ||
      out_section_index == NULL || out_offset == NULL) {
    return 0;
  }
  metadata = m68k_sim_metadata_for_instruction(instruction);
  if (metadata == NULL) return 0;
  for (operand_index = 0U; operand_index < candidate->operand_count && operand_index < instruction->operand_count &&
       operand_index < 4U; ++operand_index) {
    const M68kOperandIR *operand = &instruction->operands[operand_index];
    const M68kRenderDataPointerValue *base;
    int32_t displacement;
    if (metadata->operand_access_kinds[operand_index] != M68K_SIM_ACCESS_MEMORY_READ ||
        !(metadata->operand_ea_uses_index[operand_index] ||
          metadata->operand_ea_address_shapes[operand_index] == M68K_SIM_EA_SHAPE_INDEX ||
          m68k_instruction_operand_decoded_ea_shape(operand) == M68K_SIM_EA_SHAPE_INDEX) ||
        operand->kind != M68K_ASM_OPERAND_EA || operand->value.ea_reg >= 8U ||
        operand->value.index_reg >= 8U) {
      continue;
    }
    base = &state->addr_regs[operand->value.ea_reg];
    displacement = (int32_t)operand->value.value;
    if (data_pointer_value_with_signed_displacement(base, displacement, out_section_index, out_offset)) {
      if (out_index_register_kind != NULL) {
        *out_index_register_kind = operand->value.index_is_address ? M68K_ANALYSIS_REGISTER_ADDRESS :
          M68K_ANALYSIS_REGISTER_DATA;
      }
      if (out_index_register != NULL) *out_index_register = operand->value.index_reg;
      return 1;
    }
  }
  return 0;
}

static int source_analysis_append_auto_structured_data_policy(M68kSourceAnalysisIR *source_analysis,
    const M68kRenderLookup *lookup) {
  size_t index;
  if (source_analysis == NULL || lookup == NULL) return 0;
  for (index = 0U; index < lookup->range_ownership_count; ++index) {
    M68kRenderRangeOwnershipView range;
    size_t existing_index;
    int exists = 0;
    if (!lookup_range_ownership_at_index(lookup, index, &range)) continue;
    if (range.structured_item_source != M68K_RENDER_RANGE_STRUCTURED_ITEM_AUTO ||
        range.structured_item == NULL) {
      continue;
    }
    for (existing_index = 0U; existing_index < source_analysis->structured_data_item_count; ++existing_index) {
      const M68kAnalysisStructuredDataItem *existing = &source_analysis->structured_data_items[existing_index];
      if (existing->has_section_index == range.structured_item->has_section_index &&
          existing->section_index == range.structured_item->section_index &&
          existing->offset == range.structured_item->offset &&
          existing->size == range.structured_item->size &&
          existing->kind == range.structured_item->kind &&
          existing->semantic_role_flags == range.structured_item->semantic_role_flags) {
        exists = 1;
        break;
      }
    }
    if (exists) continue;
    if (m68k_ir_source_analysis_append_structured_data_item(source_analysis, range.structured_item) != 0)
      return -1;
  }
  return 0;
}

static uint16_t trace_base_id_from_name(const char *name) {
  uint16_t base_id;
  const char *library_name;
  const char *base_name;
  if (name == NULL || name[0] == '\0') return AMIGA_OS_BASE_ID_NONE;
  base_id = amiga_os_name_id(M68K_PLATFORM_NAME_BASE, name);
  if (base_id != AMIGA_OS_BASE_ID_NONE) return base_id;
  base_name = amiga_os_find_library_base_name(name);
  if (base_name != NULL && base_name[0] != '\0') {
    base_id = amiga_os_name_id(M68K_PLATFORM_NAME_BASE, base_name);
    if (base_id != AMIGA_OS_BASE_ID_NONE) return base_id;
  }
  library_name = amiga_library_name_from_base_symbol_name(name);
  if (library_name == NULL || library_name[0] == '\0') return AMIGA_OS_BASE_ID_NONE;
  base_name = amiga_os_find_library_base_name(library_name);
  return base_name != NULL ? amiga_os_name_id(M68K_PLATFORM_NAME_BASE, base_name) : AMIGA_OS_BASE_ID_NONE;
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
  return amiga_os_find_library_name_by_base_id(reg->base_id);
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
    if (library_name != NULL && amiga_os_find_library_base_name(library_name) != NULL) return library_name;
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
      return slot->base_id != AMIGA_OS_BASE_ID_NONE ? amiga_os_find_library_name_by_base_id(slot->base_id) : NULL;
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
      return index != 0U && amiga_os_find_library_base_name(out_name) != NULL;
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
      return index != 0U && amiga_os_find_library_base_name(out_name) != NULL;
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

static const AmigaOsCallInputInfo *open_device_iorequest_input_info(void) {
  const AmigaOsLibraryVectorInfo *open_device =
    amiga_os_find_library_vector_by_symbol_id(AMIGA_OS_SYMBOL_ID_LVOOPENDEVICE);
  const AmigaOsCallInputInfo *inputs;
  size_t count = 0U;
  size_t index;
  if (open_device == NULL) return NULL;
  inputs = amiga_os_library_vector_inputs(open_device, &count);
  if (inputs == NULL) return NULL;
  for (index = 0U; index < count; ++index) {
    const AmigaOsCallInputInfo *input = &inputs[index];
    if (input->reg_kind == AMIGA_OS_REGISTER_ADDRESS && input->reg_index == 1U &&
        input->struct_id == AMIGA_OS_STRUCT_ID_IO) {
      return input;
    }
  }
  return NULL;
}

static int amiga_vector_iorequest_address_register(const AmigaOsLibraryVectorInfo *vector, uint8_t *out_reg) {
  const AmigaOsCallInputInfo *inputs;
  size_t count = 0U;
  size_t index;
  if (out_reg != NULL) *out_reg = 0U;
  if (vector == NULL) return 0;
  inputs = amiga_os_library_vector_inputs(vector, &count);
  if (inputs == NULL) return 0;
  for (index = 0U; index < count; ++index) {
    const AmigaOsCallInputInfo *input = &inputs[index];
    if (input->reg_kind == AMIGA_OS_REGISTER_ADDRESS && input->reg_index < 8U &&
        input->struct_id == AMIGA_OS_STRUCT_ID_IO) {
      if (out_reg != NULL) *out_reg = input->reg_index;
      return 1;
    }
  }
  return 0;
}

static int format_open_device_app_iorequest_slot_name(const char *device_name, char *symbol_name,
    size_t symbol_name_size) {
  const AmigaOsCallInputInfo *input = open_device_iorequest_input_info();
  const char *input_name = input != NULL ? amiga_os_name(M68K_PLATFORM_NAME_SYMBOL, input->input_id) : NULL;
  char device_part[48];
  char input_part[32];
  int written;
  if (symbol_name == NULL || symbol_name_size == 0U) return 0;
  symbol_name[0] = '\0';
  if (!format_lower_symbol_component(device_name, device_part, sizeof(device_part)) ||
      !format_lower_symbol_component(input_name, input_part, sizeof(input_part))) {
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
  const AmigaOsLibraryVectorInfo *open_library;
  const AmigaOsLibraryVectorInfo *old_open_library;
  if (state == NULL || !state->addr_regs[6].known ||
      state->addr_regs[6].base_id != AMIGA_OS_BASE_ID_SYSBASE) {
    return 0;
  }
  if (!candidate_calls_a6_lvo(candidate, &lvo)) return 0;
  open_library = amiga_os_find_library_vector_by_symbol_id(AMIGA_OS_SYMBOL_ID_LVOOPENLIBRARY);
  old_open_library = amiga_os_find_library_vector_by_symbol_id(AMIGA_OS_SYMBOL_ID_LVOOLDOPENLIBRARY);
  return (open_library != NULL && open_library->lvo == lvo) ||
    (old_open_library != NULL && old_open_library->lvo == lvo);
}

static int amiga_vector_is_open_library(const AmigaOsLibraryVectorInfo *vector) {
  if (vector == NULL) return 0;
  return vector->function_id == AMIGA_OS_FUNCTION_ID_OPENLIBRARY ||
    vector->function_id == AMIGA_OS_FUNCTION_ID_OLDOPENLIBRARY;
}

static int candidate_is_exec_open_device_call(const M68kRenderBaseTraceState *state,
    const M68kDecodeCandidate *candidate) {
  int16_t lvo = 0;
  const AmigaOsLibraryVectorInfo *open_device;
  if (state == NULL || !state->addr_regs[6].known ||
      state->addr_regs[6].base_id != AMIGA_OS_BASE_ID_SYSBASE) {
    return 0;
  }
  if (!candidate_calls_a6_lvo(candidate, &lvo)) return 0;
  open_device = amiga_os_find_library_vector_by_symbol_id(AMIGA_OS_SYMBOL_ID_LVOOPENDEVICE);
  return open_device != NULL && open_device->lvo == lvo;
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
  if (library_name == NULL || amiga_os_find_library_base_name(library_name) == NULL) return 0;
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
  if (library_name == NULL || amiga_os_find_library_base_name(library_name) == NULL) return 0;
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
  if (library_name == NULL || amiga_os_find_library_base_name(library_name) == NULL) return 0;
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
  if (amiga_os_find_library_base_name(source_name) != NULL ||
      amiga_os_find_library_name_by_base_name(source_name) != NULL) {
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

static uint8_t app_slot_access_size_from_instruction(const M68kInstructionIR *instruction, uint8_t access_kind) {
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
            app_slot_access_size_from_instruction(&instruction, access_kind), 0) != 0) {
          return -1;
        }
      }
    }
  }
  return 0;
}

static int displacement_is_custom_hardware_offset(int16_t displacement) {
  uint32_t offset;
  if (displacement < 0) return 0;
  offset = (uint32_t)(uint16_t)displacement;
  return amiga_os_find_hardware_register_by_base_id_offset(AMIGA_OS_HARDWARE_BASE_ID_CUSTOM, offset) != NULL ||
    amiga_os_find_hardware_register_field_by_base_id_offset(AMIGA_OS_HARDWARE_BASE_ID_CUSTOM, offset) != NULL ||
    amiga_os_find_hardware_register_range_by_base_id_offset(AMIGA_OS_HARDWARE_BASE_ID_CUSTOM, offset) != NULL;
}

int render_state_operand_uses_app_base(const M68kRenderPlatformState *state, uint8_t base_reg,
    int16_t displacement) {
  if (state == NULL || base_reg >= 8U) return 0;
  if (m68k_bitset_u32_has(state->address_hardware_base_known, base_reg)) return 0;
  if (m68k_bitset_u32_has(state->address_app_base_known, base_reg)) return 1;
  if (m68k_bitset_u32_has(state->address_base_known, base_reg))
    return library_base_can_use_app_extension_slot(state->address_base_library[base_reg], displacement);
  return base_reg == 6U && !displacement_is_custom_hardware_offset(displacement);
}

static int render_lookup_analyze_amiga_app_state_slots(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  size_t section_index;
  int32_t min_app_displacement = 0;
  if (lookup == NULL || decode == NULL || accepted_start == NULL) return -1;
  if (lookup->object == NULL || lookup->object->platform_backend_kind != M68K_PLATFORM_BACKEND_AMIGA_HUNK)
    return 0;
  if (lookup_has_amiga_resident_library_context(lookup) &&
      !render_amiga_constant_value_by_symbol_id(AMIGA_OS_SYMBOL_ID_LIB_SIZE, &min_app_displacement)) {
    return 0;
  }
  for (section_index = 0U; section_index < decode->section_count; ++section_index) {
    const M68kDecodeSectionIR *section = &decode->sections[section_index];
    M68kRenderPlatformState state;
    size_t candidate_index;
    memset(&state, 0, sizeof(state));
    for (candidate_index = 0U; candidate_index < section->candidate_count; ++candidate_index) {
      const M68kDecodeCandidate *candidate = &section->candidates[candidate_index];
      M68kInstructionIR instruction;
      size_t operand_index;
      if (!candidate_is_accepted_start(section, accepted_start[section_index], candidate)) continue;
      platform_state_apply_policy_register_seeds(&state, lookup->policy, section->section_index,
        candidate->offset);
      if (m68k_decode_candidate_to_instruction(candidate, &instruction) != 0) continue;
      for (operand_index = 0U; operand_index < instruction.operand_count && operand_index < 4U; ++operand_index) {
        uint8_t base_reg = 0U;
        int16_t displacement = 0;
        uint8_t access_kind;
        if (!operand_is_address_displacement_local(&instruction.operands[operand_index], &base_reg,
            &displacement)) {
          continue;
        }
        if ((int32_t)displacement < min_app_displacement) continue;
        if (!render_state_operand_uses_app_base(&state, base_reg, displacement)) continue;
        access_kind = app_slot_access_kind_from_instruction(&instruction, operand_index);
        if (access_kind == M68K_APP_SLOT_ACCESS_NONE) continue;
        if (render_lookup_add_app_access_ref(lookup, section->section_index, candidate->offset, base_reg,
            displacement, (uint8_t)operand_index, access_kind,
            app_slot_access_size_from_instruction(&instruction, access_kind), 1) != 0) {
          return -1;
        }
      }
      platform_state_update_after_instruction(&state, lookup, &instruction);
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
        const AmigaOsCallInputInfo *iorequest_input = open_device_iorequest_input_info();
        int typed_slot_added = 0;
        int32_t device_base_displacement = (int32_t)trace_state.app_addresses[1].displacement +
          (int32_t)AMIGA_OS_STRUCT_IO_FIELD_IO_DEVICE_OFFSET;
        if (render_lookup_add_device_instance(lookup, trace_state.app_addresses[1].displacement,
            trace_state.addr_regs[0].name) != 0 ||
            render_lookup_add_device_call(lookup, section->section_index, candidate->offset,
            trace_state.addr_regs[0].name) != 0) {
          goto cleanup;
        }
        if (iorequest_input != NULL && iorequest_input->struct_id != AMIGA_OS_STRUCT_ID_NONE &&
            render_lookup_add_typed_app_slot_region(lookup, trace_state.app_addresses[1].displacement,
              iorequest_input->struct_id, section->section_index, candidate->offset, &typed_slot_added) != 0) {
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
  pass_start = clock();
  if (stats != NULL) memset(stats, 0, sizeof(*stats));
  start = clock();
  if (render_lookup_seed_policy_rsset_layout_regions(lookup) != 0) return -1;
  if (render_lookup_infer_global_base_slots(lookup, decode, accepted_start) != 0) return -1;
  end = clock();
  if (stats != NULL) stats->base_slot_seconds = elapsed_seconds_local(start, end);
  start = clock();
  if (render_lookup_infer_amiga_recovered_local_call_summaries(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_infer_amiga_recovered_function_args(lookup, decode, accepted_start) != 0) return -1;
  end = clock();
  if (stats != NULL) stats->call_summary_seconds = elapsed_seconds_local(start, end);
  start = clock();
  if (render_lookup_analyze_amiga_app_state_slots(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_seed_policy_rsset_use_site_app_refs(lookup, decode, accepted_start) != 0) return -1;
  end = clock();
  if (stats != NULL) stats->app_slot_seconds = elapsed_seconds_local(start, end);
  start = clock();
  if (render_lookup_analyze_amiga_typed_refs(lookup, decode, accepted_start) != 0) return -1;
  if (render_lookup_record_typed_app_slot_pointer_accesses(lookup, decode, accepted_start) != 0) return -1;
  end = clock();
  if (stats != NULL) stats->typed_ref_seconds = elapsed_seconds_local(start, end);
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
  if (render_lookup_infer_data_strings(lookup, decode, accepted_bytes) != 0) return -1;
  if (render_lookup_add_pointer_table_target_labels(lookup, decode, accepted_start, accepted_bytes) != 0) return -1;
  end = clock();
  if (stats != NULL) {
    stats->generic_data_seconds = elapsed_seconds_local(start, end);
    stats->pass_seconds = elapsed_seconds_local(pass_start, end);
  }
  return 0;
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
    library_name = amiga_os_name(M68K_PLATFORM_NAME_LIBRARY, vector->library_id);
    note_base_name = amiga_os_find_library_base_name(library_name);
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
            0U, access_size, arg->pointee_type_name, arg->pointee_type_name, arg->field_name,
            "", 0U, 0U, M68K_PLATFORM_TYPE_PROVENANCE_API_OUTPUT, section->section_index, call_offset) != 0) {
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
                dest_displacement, 0, 0U, access_size, arg->pointee_type_name, arg->pointee_type_name,
                arg->field_name, "", 0U, 0U, M68K_PLATFORM_TYPE_PROVENANCE_API_OUTPUT, section->section_index,
                call_offset) != 0) {
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
            0U, 0U, param->type_name, param->type_name, param->name != NULL ? param->name : "",
            "", 0U, 0U, M68K_PLATFORM_TYPE_PROVENANCE_API_INPUT, section->section_index, call_offset) != 0) {
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

int m68k_analysis_render_lookup_append_auto_policy(M68kSourceAnalysisIR *source_analysis,
    M68kRenderLookup *lookup) {
  return source_analysis_append_auto_structured_data_policy(source_analysis, lookup);
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

int m68k_analysis_render_lookup_append_section(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    M68kSectionAnalysisIR *section_analysis) {
  if (append_render_lookup_platform_effects_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_app_slot_refs_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_runtime_views_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_runtime_address_refs_for_section(lookup, decode, section_analysis) != 0) return -1;
  if (append_render_lookup_code_start_refs_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_violations_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_recovered_local_call_summaries_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_recovered_function_args_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_typed_accesses_for_section(lookup, section_analysis) != 0) return -1;
  if (append_render_lookup_unresolved_typed_accesses_for_section(lookup, section_analysis) != 0) return -1;
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
  if (m68k_analysis_render_lookup_append_auto_policy(source_analysis, lookup) != 0) goto fail;
  if (m68k_analysis_render_lookup_append_base_layout_fields(scratch_arena, lookup, decode, source_analysis) != 0)
    goto fail;
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

