/* A read-only complement to the typed/app catalogues. Configured A6 fallback
 * is a hypothesis, not register provenance or permission to promote a slot.
 * Temporary sorted evidence and coverage indices avoid per-operand full scans;
 * no analysis state, names, ownership or source rendering are changed. */
typedef struct BaseCandidateEvidence {
  size_t section;
  uint32_t offset, operand;
  const M68kAppSlotRefIR *app_ref;
} BaseCandidateEvidence;
typedef struct BaseCandidateInterval { int64_t start, end; } BaseCandidateInterval;
typedef struct BaseCandidateIndex {
  BaseCandidateEvidence *evidence;
  BaseCandidateInterval *regions;
  size_t evidence_count, evidence_capacity, region_count;
} BaseCandidateIndex;

static int base_candidate_evidence_compare(const void *aa, const void *bb) {
  const BaseCandidateEvidence *a=aa, *b=bb;
  if (a->section != b->section) return a->section < b->section ? -1 : 1;
  if (a->offset != b->offset) return a->offset < b->offset ? -1 : 1;
  return (a->operand > b->operand) - (a->operand < b->operand);
}
static int base_candidate_interval_compare(const void *aa, const void *bb) {
  const BaseCandidateInterval *a=aa, *b=bb;
  if (a->start != b->start) return a->start < b->start ? -1 : 1;
  return (a->end > b->end) - (a->end < b->end);
}
static int base_candidate_evidence_add(BaseCandidateIndex *index, size_t section,
    uint32_t offset, uint32_t operand, const M68kAppSlotRefIR *app_ref) {
  if (index->evidence_count == index->evidence_capacity) {
    size_t capacity=index->evidence_capacity ? index->evidence_capacity*2U : 64U;
    BaseCandidateEvidence *grown;
    if (capacity < index->evidence_capacity || capacity > SIZE_MAX/sizeof(*grown)) return -1;
    grown=realloc(index->evidence,capacity*sizeof(*grown)); if (!grown) return -1;
    index->evidence=grown; index->evidence_capacity=capacity;
  }
  index->evidence[index->evidence_count++]=(BaseCandidateEvidence){section,offset,operand,app_ref};
  return 0;
}
static void base_candidate_index_destroy(BaseCandidateIndex *index) {
  free(index->evidence); free(index->regions); memset(index,0,sizeof(*index));
}
static int base_candidate_index_build(BaseCandidateIndex *index, const M68kSourceAnalysisIR *source) {
  const M68kAnalysisPolicy *policy=&source->policy;
  size_t i,j,merged=0U;
  if (policy->rsset_layout_region_count) {
    index->regions=calloc(policy->rsset_layout_region_count,sizeof(*index->regions));
    if (!index->regions) return -1;
  }
  for (i=0;i<policy->rsset_layout_region_count;++i) {
    const M68kAnalysisRssetLayoutRegion *r=&policy->rsset_layout_regions[i];
    if (!r->size || (r->base_symbol[0] && strcmp(r->base_symbol,M68K_APP_BASE_SYMBOL)) ||
        (!r->base_symbol[0] && strcmp(r->layout_name,"app"))) continue;
    index->regions[index->region_count++]=(BaseCandidateInterval){r->offset,(int64_t)r->offset+r->size};
  }
  if (!index->region_count) return 0; /* An arbitrary A6 is not an app namespace. */
  qsort(index->regions,index->region_count,sizeof(*index->regions),base_candidate_interval_compare);
  for (i=0;i<index->region_count;++i) {
    BaseCandidateInterval next=index->regions[i];
    if (merged && next.start<=index->regions[merged-1U].end) {
      if (next.end>index->regions[merged-1U].end) index->regions[merged-1U].end=next.end;
    } else index->regions[merged++]=next;
  }
  index->region_count=merged; /* Coverage union, never a shared-owner inference. */
#define BLOCK(row) do { if(base_candidate_evidence_add(index,s->section_index,(row)->offset,(row)->operand_index,NULL)) return -1; } while(0)
  for (i=0;i<source->section_count;++i) {
    const M68kSectionAnalysisIR *s=&source->sections[i];
    for(j=0;j<s->app_slot_ref_count;++j) {
      const M68kAppSlotRefIR *r=&s->app_slot_refs[j];
      if(base_candidate_evidence_add(index,s->section_index,r->offset,r->operand_index,r)) return -1;
    }
    for(j=0;j<s->recovered_platform_typed_access_count;++j) BLOCK(&s->recovered_platform_typed_accesses[j]);
    for(j=0;j<s->recovered_platform_unresolved_typed_access_count;++j) BLOCK(&s->recovered_platform_unresolved_typed_accesses[j]);
    for(j=0;j<s->platform_address_use_count;++j) BLOCK(&s->platform_address_uses[j]);
    for(j=0;j<s->address_observation_count;++j) {
      const M68kAddressObservationIR *r=&s->address_observations[j];
      if (r->has_address && !r->conflicted &&
          r->owner_kind!=M68K_ABSOLUTE_MEMORY_OWNER_UNKNOWN) BLOCK(r);
    }
  }
#undef BLOCK
  if(index->evidence_count) qsort(index->evidence,index->evidence_count,
      sizeof(*index->evidence),base_candidate_evidence_compare);
  return 0;
}
/* Full memory spans are half-open. Address formation can name one-past,
 * without claiming even one byte of storage at that endpoint. */
static const char *base_candidate_coverage(const BaseCandidateIndex *index, int32_t displacement,
    uint8_t span, int address_only, int span_known) {
  size_t lo=0U,hi=index->region_count;
  int64_t start=displacement,end=start+span;
  if (!span_known) return "unknown_footprint";
  while(lo<hi) {size_t mid=lo+(hi-lo)/2U;
    if(index->regions[mid].start<=start)lo=mid+1U;else hi=mid;}
  if(lo) {
    const BaseCandidateInterval *r=&index->regions[lo-1U];
    if ((address_only && start<=r->end) || (!address_only && end<=r->end)) return NULL;
    if(r->end>start) return "partially_declared";
  }
  if(!address_only && lo<index->region_count && index->regions[lo].start<end) return "partially_declared";
  return "undeclared";
}
