/* Input-sized direct-call graph. CFG successors are shared with typed flow;
 * iterative SCC discovery uses O(V+E) graph storage, never a closure matrix. */
typedef struct M68kDirectCallGraph {
  size_t count, edge_count, edge_capacity, cfg_visits, index_bytes, scc_edge_visits;
  size_t *offsets, *targets, *component, *component_size, *component_anchor, *ordinal;
  size_t component_count;
} M68kDirectCallGraph;

static void direct_call_graph_destroy(M68kDirectCallGraph *graph) {
  free(graph->offsets); free(graph->targets); free(graph->component);
  free(graph->component_size); free(graph->component_anchor); free(graph->ordinal);
  memset(graph, 0, sizeof(*graph));
}

static int direct_call_graph_append(M68kDirectCallGraph *graph, size_t target) {
  if (graph->edge_count == graph->edge_capacity) {
    size_t capacity = graph->edge_capacity ? graph->edge_capacity * 2U : 32U;
    size_t *grown;
    if (capacity < graph->edge_capacity || capacity > SIZE_MAX / sizeof(*grown)) return -1;
    grown = realloc(graph->targets, capacity * sizeof(*grown));
    if (grown == NULL) return -1;
    graph->targets = grown; graph->edge_capacity = capacity;
  }
  graph->targets[graph->edge_count++] = target;
  return 0;
}

/* Calls are edges, not transfers into callee bodies. Direct tail jumps remain
 * part of the enclosing body's CFG, exactly as in the existing body proof. */
typedef struct M68kDirectSectionIndex {
  size_t *by_offset, *queue;
  uint32_t *seen, epoch;
} M68kDirectSectionIndex;

static int direct_call_graph_collect(M68kDirectCallGraph *graph, M68kRenderLookup *lookup,
    const M68kDecodeIR *decode, uint8_t **accepted_start) {
  size_t root, i;
  uint32_t *callees = NULL;
  M68kDirectSectionIndex *indices = NULL;
  int result = -1;
  graph->count = lookup->inferred_function_summary_count;
  if (graph->count >= UINT32_MAX || graph->count > SIZE_MAX / sizeof(size_t) - 1U) return -1;
  graph->offsets = calloc(graph->count + 1U, sizeof(*graph->offsets));
  callees = calloc(graph->count ? graph->count : 1U, sizeof(*callees));
  indices = calloc(decode->section_count ? decode->section_count : 1U, sizeof(*indices));
  if (graph->offsets == NULL || callees == NULL || indices == NULL) goto cleanup;
  for (root = 0U; root < graph->count; ++root) {
    const M68kAnalysisFunctionSummary *summary = &lookup->inferred_function_summaries[root].summary;
    const M68kDecodeSectionIR *section;
    M68kDirectSectionIndex *index;
    size_t head = 0U, tail = 0U, section_index = summary->section_index;
    graph->offsets[root] = graph->edge_count;
    if (summary->callable_kind != M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT ||
        section_index >= decode->section_count) continue;
    section = &decode->sections[section_index]; index = &indices[section_index];
    if (index->by_offset == NULL) {
      if (section->size == UINT32_MAX || (size_t)section->size + 1U > SIZE_MAX / sizeof(size_t) ||
          section->candidate_count > SIZE_MAX / sizeof(size_t)) goto cleanup;
      index->by_offset = malloc(((size_t)section->size + 1U) * sizeof(size_t));
      index->queue = malloc((section->candidate_count ? section->candidate_count : 1U) * sizeof(size_t));
      index->seen = calloc(section->candidate_count ? section->candidate_count : 1U, sizeof(uint32_t));
      if (!index->by_offset || !index->queue || !index->seen) goto cleanup;
      graph->index_bytes += ((size_t)section->size + 1U) * sizeof(size_t) +
        section->candidate_count * (sizeof(size_t) + sizeof(uint32_t));
      for (i = 0U; i <= section->size; ++i) index->by_offset[i] = SIZE_MAX;
      for (i = 0U; i < section->candidate_count; ++i)
        if (section->candidates[i].offset < section->size &&
            candidate_is_accepted_start(section, accepted_start[section_index], &section->candidates[i]))
          index->by_offset[section->candidates[i].offset] = i;
    }
    if (++index->epoch == 0U) { memset(index->seen, 0, section->candidate_count * sizeof(uint32_t)); index->epoch = 1U; }
    if (summary->entry_offset < section->size && index->by_offset[summary->entry_offset] != SIZE_MAX) {
      i = index->by_offset[summary->entry_offset]; index->queue[tail++] = i; index->seen[i] = index->epoch;
    }
    while (head < tail) {
      const M68kDecodeCandidate *candidate = &section->candidates[index->queue[head++]];
      ++graph->cfg_visits;
      size_t callee_section, callee_index, successors[5];
      uint32_t callee_offset;
      int count, successor;
      if (typed_flow_local_call_target(lookup, candidate, &callee_section, &callee_offset) &&
          lookup_configured_direct_function_summary(lookup, callee_section, callee_offset) == NULL) {
        callee_index = lookup_inferred_direct_function_summary_index(lookup, callee_section, callee_offset);
        if (callee_index != SIZE_MAX && callees[callee_index] != root + 1U) {
          callees[callee_index] = (uint32_t)root + 1U;
          if (direct_call_graph_append(graph, callee_index) != 0) goto cleanup;
        }
      }
      const M68kRenderClosedDispatch *closed = lookup_closed_dispatch(lookup, section_index, candidate->offset);
      if (closed) {
        for (size_t t = 0U; t < closed->count; ++t) {
          i = index->by_offset[closed->targets[t]];
          if (i == SIZE_MAX) goto cleanup;
          if (index->seen[i] != index->epoch) {
            index->seen[i] = index->epoch; index->queue[tail++] = i;
          }
        }
        continue;
      }
      count = typed_flow_successors_for_candidate(lookup, section, accepted_start[section_index], index->by_offset,
        section->size + 1U, candidate, successors, 5U);
      for (successor = 0; successor < count; ++successor) {
        i = successors[successor];
        if (index->seen[i] != index->epoch) {
          index->seen[i] = index->epoch; index->queue[tail++] = i;
        }
      }
    }
  }
  graph->offsets[graph->count] = graph->edge_count;
  result = 0;
cleanup:
  if (indices != NULL) for (i = 0U; i < decode->section_count; ++i) {
    free(indices[i].by_offset); free(indices[i].queue); free(indices[i].seen);
  }
  free(indices); free(callees); return result;
}

/* Kosaraju with explicit stacks: no C recursion and no input-depth limit.
 * Components are ordered caller-before-callee, so reverse order is a proof
 * schedule for the acyclic condensation graph. */
static int direct_call_graph_components(M68kDirectCallGraph *graph) {
  size_t n = graph->count, i, used = 0U, count = 0U;
  size_t *stack = NULL, *next = NULL, *finish = NULL, *reverse_offsets = NULL, *reverse = NULL;
  uint8_t *seen = NULL;
  graph->component = malloc((n ? n : 1U) * sizeof(size_t));
  graph->component_size = calloc(n ? n : 1U, sizeof(size_t));
  graph->component_anchor = malloc((n ? n : 1U) * sizeof(size_t));
  graph->ordinal = calloc(n ? n : 1U, sizeof(size_t));
  stack = malloc((n ? n : 1U) * sizeof(size_t)); next = malloc((n ? n : 1U) * sizeof(size_t));
  finish = malloc((n ? n : 1U) * sizeof(size_t)); seen = calloc(n ? n : 1U, 1U);
  reverse_offsets = calloc(n + 1U, sizeof(size_t));
  reverse = malloc((graph->edge_count ? graph->edge_count : 1U) * sizeof(size_t));
  if (!graph->component || !graph->component_size || !graph->component_anchor || !graph->ordinal ||
      !stack || !next || !finish || !seen || !reverse_offsets || !reverse) goto fail;
  for (i = 0U; i < n; ++i) {
    size_t depth = 0U;
    if (seen[i]) continue;
    stack[depth] = i; next[depth++] = graph->offsets[i]; seen[i] = 1U;
    while (depth) {
      size_t node = stack[depth - 1U];
      if (next[depth - 1U] == graph->offsets[node + 1U]) {
        finish[used++] = node; --depth;
      } else {
        size_t target = graph->targets[next[depth - 1U]++];
        ++graph->scc_edge_visits;
        if (!seen[target]) { seen[target] = 1U; stack[depth] = target; next[depth++] = graph->offsets[target]; }
      }
    }
  }
  for (i = 0U; i < graph->edge_count; ++i) {
    ++reverse_offsets[graph->targets[i] + 1U]; ++graph->scc_edge_visits;
  }
  for (i = 1U; i <= n; ++i) reverse_offsets[i] += reverse_offsets[i - 1U];
  memcpy(next, reverse_offsets, n * sizeof(size_t));
  for (i = 0U; i < n; ++i)
    for (size_t e = graph->offsets[i]; e < graph->offsets[i + 1U]; ++e)
      { reverse[next[graph->targets[e]]++] = i; ++graph->scc_edge_visits; }
  memset(seen, 0, n);
  while (used) {
    size_t start = finish[--used], depth = 0U;
    if (seen[start]) continue;
    stack[depth++] = start; seen[start] = 1U;
    while (depth) {
      size_t node = stack[--depth];
      graph->component[node] = count; ++graph->component_size[count];
      for (size_t e = reverse_offsets[node]; e < reverse_offsets[node + 1U]; ++e) {
        size_t target = reverse[e];
        ++graph->scc_edge_visits;
        if (!seen[target]) { seen[target] = 1U; stack[depth++] = target; }
      }
    }
    ++count;
  }
  graph->component_count = count;
  free(stack); free(next); free(finish); free(seen); free(reverse_offsets); free(reverse); return 0;
fail:
  free(stack); free(next); free(finish); free(seen); free(reverse_offsets); free(reverse); return -1;
}
typedef struct M68kDirectNodeOrder {
  size_t node, component, section;
  uint32_t offset;
} M68kDirectNodeOrder;

static int direct_node_order_compare(const void *a, const void *b) {
  const M68kDirectNodeOrder *x = a, *y = b;
  if (x->component != y->component) return x->component < y->component ? -1 : 1;
  if (x->section != y->section) return x->section < y->section ? -1 : 1;
  if (x->offset != y->offset) return x->offset < y->offset ? -1 : 1;
  return x->node < y->node ? -1 : x->node != y->node;
}

static int direct_call_graph_prove(M68kRenderLookup *lookup, const M68kDecodeIR *decode,
    uint8_t **accepted_start) {
  M68kDirectCallGraph graph = {0};
  M68kDirectNodeOrder *order = NULL;
  size_t i;
  int result = -1;
  clock_t started = clock(), collected, components;
  if (lookup->inferred_function_summary_count == 0U) return 0;
  if (direct_call_graph_collect(&graph, lookup, decode, accepted_start) != 0) goto cleanup;
  collected = clock();
  if (direct_call_graph_components(&graph) != 0) goto cleanup;
  components = clock();
  order = calloc(graph.count, sizeof(*order));
  if (order == NULL) goto cleanup;
  for (i = 0U; i < graph.count; ++i) {
    const M68kAnalysisFunctionSummary *s = &lookup->inferred_function_summaries[i].summary;
    order[i].node = i; order[i].component = graph.component[i];
    order[i].section = s->section_index; order[i].offset = s->entry_offset;
  }
  qsort(order, graph.count, sizeof(*order), direct_node_order_compare);
  for (i = 0U; i < graph.count; ++i) {
    size_t node = order[i].node, component = graph.component[node];
    if (i == 0U || order[i - 1U].component != component) graph.component_anchor[component] = node;
    else graph.ordinal[node] = graph.ordinal[order[i - 1U].node] + 1U;
  }
  /* Reject cycles before proving a caller; no conservative seed is silently
   * reinterpreted as recursive preservation. Singleton SCCs need one proof in
   * reverse condensation order, rather than a capped whole-graph iteration. */
  for (i = 0U; i < graph.count; ++i) {
    M68kRenderInferredFunctionSummary *record = &lookup->inferred_function_summaries[i];
    size_t component = graph.component[i], anchor = graph.component_anchor[component];
    int recursive = graph.component_size[component] > 1U;
    for (size_t e = graph.offsets[i]; e < graph.offsets[i + 1U]; ++e)
      if (graph.targets[e] == i) recursive = 1;
    record->direct_scc_anchor_section_index = lookup->inferred_function_summaries[anchor].summary.section_index;
    record->direct_scc_anchor_entry_offset = lookup->inferred_function_summaries[anchor].summary.entry_offset;
    record->direct_scc_size = (uint32_t)graph.component_size[component];
    record->direct_scc_ordinal = (uint32_t)graph.ordinal[i];
    if (recursive) {
      record->summary.effects_invalid = 1U;
      record->summary.register_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_INVALID;
      record->summary.memory_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_INVALID;
      record->summary.escape_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_INVALID;
      record->terminal_reason = M68K_FUNCTION_SUMMARY_TERMINAL_RECURSIVE_DIRECT_GRAPH;
    }
  }
  for (i = graph.count; i > 0U; --i) {
    M68kRenderInferredFunctionSummary *record = &lookup->inferred_function_summaries[order[i - 1U].node];
    M68kAnalysisFunctionSummary next;
    uint8_t limit_hit = 0U;
    if (record->summary.effects_invalid ||
        record->summary.callable_kind != M68K_ANALYSIS_FUNCTION_SUMMARY_CALLABLE_DIRECT) continue;
    if (!typed_flow_local_callee_effect_summary(lookup, decode, accepted_start,
          record->summary.section_index, record->summary.entry_offset, &next, &limit_hit)) {
      record->summary.effects_invalid = 1U;
      record->summary.register_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_INVALID;
      record->summary.memory_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_INVALID;
      record->summary.escape_effect_state = M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_INVALID;
      record->terminal_reason = limit_hit ? M68K_FUNCTION_SUMMARY_TERMINAL_DIRECT_BODY_LIMIT :
        M68K_FUNCTION_SUMMARY_TERMINAL_DIRECT_BODY_UNSUPPORTED;
      continue;
    }
    next.callable_kind = record->summary.callable_kind;
    next.has_section_index = record->summary.has_section_index;
    next.section_index = record->summary.section_index;
    next.entry_offset = record->summary.entry_offset;
    snprintf(next.function_summary_id, sizeof(next.function_summary_id), "%s", record->summary.function_summary_id);
    record->summary = next;
  }
  result = 0;
  if (getenv("AMIGA_REVERSING_DIRECT_GRAPH_TRACE") != NULL)
    fprintf(stderr, "direct-call-graph nodes=%zu edges=%zu cfg_visits=%zu index_bytes=%zu scc_edge_visits=%zu collect_seconds=%.6f scc_seconds=%.6f body_seconds=%.6f\n",
      graph.count, graph.edge_count, graph.cfg_visits, graph.index_bytes, graph.scc_edge_visits,
      elapsed_seconds_local(started, collected), elapsed_seconds_local(collected, components),
      elapsed_seconds_local(components, clock()));
cleanup:
  free(order); direct_call_graph_destroy(&graph); return result;
}
