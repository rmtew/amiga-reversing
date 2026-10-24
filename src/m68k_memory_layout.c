#include "m68k_memory_layout.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
_Static_assert(M68K_ANALYSIS_MEMORY_REGION_LIMIT<=32,"layout membership index uses a bounded bitmap");
static int ancestor(const M68kResolvedMemoryLayout *,int,int);

static int region_index(const M68kAnalysisPolicy *p,const char *id) {
  for(size_t i=0;i<p->memory_region_count;i++) if(!strcmp(p->memory_regions[i].region_id,id)) return (int)i;
  return -1;
}
static int fail(M68kResolvedMemoryLayout *out,int i,const char *reason) {
  out->failed_region=i;out->reason=reason;return -1;
}
static int resolve_region(const M68kAnalysisPolicy *p,const M68kMemoryLayoutIR *layout,
    M68kResolvedMemoryLayout *out,uint8_t *state,int i) {
  const M68kMemoryRegionIR *r=&p->memory_regions[i];uint64_t address=r->runtime_address;
  if(state[i]==2) return 0;
  if(state[i]==1) return fail(out,i,"parent_cycle");
  state[i]=1;
  if(r->parent_region_id[0]) {
    int pi=region_index(p,r->parent_region_id);
    if(pi<0) return fail(out,i,"missing_parent");
    if(resolve_region(p,layout,out,state,pi)) return -1;
    const M68kMemoryRegionIR *parent=&p->memory_regions[pi];
    if(r->runtime_address<parent->runtime_address ||
        (uint64_t)r->runtime_address+r->size>(uint64_t)parent->runtime_address+parent->size)
      return fail(out,i,"outside_original_parent");
    out->parents[i]=(int16_t)pi;
    address=(uint64_t)out->addresses[pi]+r->runtime_address-parent->runtime_address;
  }
  for(size_t j=0;j<layout->placement_count;j++) {
    if(strcmp(layout->placements[j].region_id,r->region_id)) continue;
    if(out->parents[i]>=0 && layout->placements[j].runtime_address!=address)
      return fail(out,i,"independent_child_placement_unsupported");
    address=layout->placements[j].runtime_address;
  }
  if(!r->size || !r->alignment || (r->alignment & (r->alignment-1)) || address%r->alignment)
    return fail(out,i,"invalid_extent_or_alignment");
  if(address+r->size>layout->chip_bytes) return fail(out,i,"outside_declared_chip_ram");
  if(address!=r->runtime_address && address<0x1000) return fail(out,i,"reserved_low_memory");
  out->addresses[i]=(uint32_t)address;
  out->ancestor_bits[i]=(UINT32_C(1)<<i) | (out->parents[i]>=0 ? out->ancestor_bits[out->parents[i]] : 0);
  state[i]=2;return 0;
}
static int ancestor(const M68kResolvedMemoryLayout *r,int a,int b) {
  return a!=b && (r->ancestor_bits[b] & (UINT32_C(1)<<a))!=0;
}

typedef struct LayoutEvent { uint64_t address,moved_end;uint32_t add,remove; } LayoutEvent;
static int event_compare(const void *ap,const void *bp) {
  const LayoutEvent *a=ap,*b=bp;return (a->address>b->address)-(a->address<b->address);
}
static void build_reference_index(const M68kAnalysisPolicy *p,M68kResolvedMemoryLayout *out) {
  LayoutEvent events[2*M68K_ANALYSIS_MEMORY_REGION_LIMIT];uint32_t active=0;uint64_t maximum=0;
  for(size_t i=0;i<p->memory_region_count;i++) {
    uint64_t start=p->memory_regions[i].runtime_address,end=start+p->memory_regions[i].size;
    events[2*i]=(LayoutEvent){start,out->addresses[i]!=start ? end : 0,UINT32_C(1)<<i,0};
    events[2*i+1]=(LayoutEvent){end,0,0,UINT32_C(1)<<i};
  }
  qsort(events,2*p->memory_region_count,sizeof(*events),event_compare);
  for(size_t i=0,j;i<2*p->memory_region_count;i=j) {
    uint32_t add=0,remove=0;
    for(j=i;j<2*p->memory_region_count && events[j].address==events[i].address;j++) {
      add|=events[j].add;remove|=events[j].remove;
      if(events[j].moved_end>maximum) maximum=events[j].moved_end;
    }
    active=(active & ~remove)|add;
    out->points[out->point_count++]=(M68kLayoutPoint){events[i].address,maximum,active};
  }
}
static const M68kLayoutPoint *reference_point(const M68kResolvedMemoryLayout *r,uint64_t address,size_t *steps) {
  size_t lo=0,hi=r->point_count;
  while(lo<hi) {
    size_t mid=lo+(hi-lo)/2;if(steps) ++*steps;
    if(r->points[mid].address<=address) lo=mid+1;else hi=mid;
  }
  return lo ? &r->points[lo-1] : NULL;
}
static unsigned first_bit(uint32_t mask) {
  unsigned i=0;
  if(!(mask & 0xFFFFU)) {i+=16;mask>>=16;}
  if(!(mask & 0xFFU)) {i+=8;mask>>=8;}
  if(!(mask & 0xFU)) {i+=4;mask>>=4;}
  if(!(mask & 3U)) {i+=2;mask>>=2;}
  return i+(!(mask & 1U));
}
int m68k_memory_layout_reference_profiled(const M68kAnalysisPolicy *p,const M68kResolvedMemoryLayout *resolved,
    uint32_t address,uint32_t width,char *expression,size_t capacity,uint32_t *placed_address,size_t *steps) {
  int selected=-1;
  if(steps) *steps=0;
  if(!p || !resolved || resolved->reason || !expression || !capacity ||
      resolved->region_count!=p->memory_region_count) return -1;
  expression[0]='\0';
  uint64_t end=(uint64_t)address+(width ? width : 1);
  const M68kLayoutPoint *start=reference_point(resolved,address,steps);
  const M68kLayoutPoint *last=end-1==address ? start : reference_point(resolved,end-1,steps);
  uint32_t candidates=start && last ? start->containing_regions & last->containing_regions : 0;
  while(candidates) {
    unsigned i=first_bit(candidates);candidates&=candidates-1;
    if(steps) ++*steps;
    if(selected<0 || ancestor(resolved,selected,(int)i)) selected=(int)i;
    else if(!ancestor(resolved,(int)i,selected)) return -1;
  }
  if(selected<0) {
    /* Unaffected fixed addresses may stay numeric. A reference straddling a
     * moved region cannot: falling back would silently retain its old base. */
    if(last && last->prefix_max_moved_end>address) return -1;
    return 0;
  }
  const M68kMemoryRegionIR *r=&p->memory_regions[selected];
  uint32_t offset=address-r->runtime_address;
  int length=offset ? snprintf(expression,capacity,"%s+$%X",r->name,offset) : snprintf(expression,capacity,"%s",r->name);
  if(length<0 || (size_t)length>=capacity) return -1;
  if(placed_address) *placed_address=resolved->addresses[selected]+offset;
  return 1;
}
int m68k_memory_layout_reference(const M68kAnalysisPolicy *p,const M68kResolvedMemoryLayout *resolved,
    uint32_t address,uint32_t width,char *expression,size_t capacity,uint32_t *placed_address) {
  return m68k_memory_layout_reference_profiled(p,resolved,address,width,expression,capacity,placed_address,NULL);
}
int m68k_memory_layout_resolve(const M68kAnalysisPolicy *p,const M68kMemoryLayoutIR *layout,
    M68kResolvedMemoryLayout *out) {
  uint8_t state[M68K_ANALYSIS_MEMORY_REGION_LIMIT]={0};
  if(!out) return -1;
  memset(out,0,sizeof(*out));out->failed_region=-1;
  for(size_t i=0;i<M68K_ANALYSIS_MEMORY_REGION_LIMIT;i++) out->parents[i]=-1;
  if(!p || !layout || p->memory_region_count>M68K_ANALYSIS_MEMORY_REGION_LIMIT ||
      p->bootstrap_contract_count>M68K_MEMORY_LAYOUT_LIMIT ||
      layout->placement_count>M68K_ANALYSIS_MEMORY_REGION_LIMIT ||
      (layout->chip_bytes!=0x80000 && layout->chip_bytes!=0x100000))
    return fail(out,-1,"unsupported_layout_profile");
  if(layout->bootstrap_contract_id[0]) {
    int found=0;
    for(size_t i=0;i<p->bootstrap_contract_count;i++)
      if(!strcmp(layout->bootstrap_contract_id,p->bootstrap_contracts[i].contract_id)) found=1;
    if(!found) return fail(out,-1,"unknown_bootstrap_contract");
  }
  out->region_count=p->memory_region_count;
  for(size_t i=0;i<layout->placement_count;i++) {
    if(region_index(p,layout->placements[i].region_id)<0) return fail(out,-1,"unknown_placement_region");
    for(size_t j=0;j<i;j++) if(!strcmp(layout->placements[i].region_id,layout->placements[j].region_id))
      return fail(out,-1,"duplicate_placement");
  }
  for(size_t i=0;i<p->memory_region_count;i++) {
    for(size_t j=0;j<i;j++) if(!strcmp(p->memory_regions[i].region_id,p->memory_regions[j].region_id))
      return fail(out,(int)i,"duplicate_region_identity");
    if(resolve_region(p,layout,out,state,(int)i)) return -1;
    const M68kMemoryRegionIR *r=&p->memory_regions[i];
    if(r->has_loader_seed) {
      if(!r->loader_seed_size || r->loader_seed_size>0x10000 ||
          (uint64_t)r->loader_seed_region_offset+r->loader_seed_size>r->size)
        return fail(out,(int)i,"invalid_loader_seed_extent");
      const M68kBootstrapContractIR *c=NULL;
      for(size_t bi=0;bi<p->bootstrap_contract_count;bi++)
        if(!strcmp(layout->bootstrap_contract_id,p->bootstrap_contracts[bi].contract_id)) c=&p->bootstrap_contracts[bi];
      if(!c) return fail(out,(int)i,"loader_seed_requires_bootstrap_contract");
      if((uint64_t)r->loader_seed_source_offset+r->loader_seed_size>c->file_size ||
          (uint64_t)r->runtime_address+r->loader_seed_region_offset!=(uint64_t)c->load_address+r->loader_seed_source_offset)
        return fail(out,(int)i,"loader_seed_original_staging_mismatch");
    }
  }
  for(size_t i=0;i<p->memory_region_count;i++) for(size_t j=0;j<i;j++) {
    if(ancestor(out,(int)i,(int)j) || ancestor(out,(int)j,(int)i)) continue;
    if((uint64_t)out->addresses[i]+p->memory_regions[i].size>out->addresses[j] &&
        (uint64_t)out->addresses[j]+p->memory_regions[j].size>out->addresses[i])
      return fail(out,(int)i,"unrelated_region_overlap");
  }
  build_reference_index(p,out);
  return 0;
}

int m68k_memory_layout_validate_source(const M68kAnalysisPolicy *policy,
    M68kResolvedMemoryLayout *resolved,const M68kSourceAnalysisIR *analysis) {
  if(!policy || !resolved || resolved->reason) return -1;
    /* First delivery relocates whole materialized views, not scatter-loaded
     * pieces. Refuse a split before the row walker can mistake original
     * adjacency for contiguous placed PCs and omit a required ORG. */
    if(analysis) for(size_t s=0;s<analysis->section_count;s++) {
      const M68kSectionAnalysisIR *section=&analysis->sections[s];
      for(size_t v=0;v<section->runtime_view_count;v++) {
        const M68kRuntimeViewIR *view=&section->runtime_views[v];
        if(!view->materialized) continue;
        for(size_t r=0;r<policy->memory_region_count;r++) {
          const M68kMemoryRegionIR *region=&policy->memory_regions[r];
          uint64_t end=(uint64_t)region->runtime_address+region->size;
          uint64_t view_end=(uint64_t)view->runtime_address+view->size;
          if(resolved->parents[r]>=0 ||
              resolved->addresses[r]==region->runtime_address) continue;
          if(region->runtime_address<view_end && end>view->runtime_address &&
              (region->runtime_address>view->runtime_address || end<view_end)) {
            resolved->reason="split_materialized_view_unsupported";
            return -1;
          }
        }
      }
    }
    for(size_t e=0;e<policy->target_equate_count;e++) {
      const M68kAnalysisTargetEquate *equate=&policy->target_equates[e];
      char expression[128];
      if(equate->address_domain && m68k_memory_layout_reference(policy,resolved,
          (uint32_t)equate->value,equate->extent_bytes,expression,sizeof(expression),NULL)<0) {
        resolved->reason="partial_or_ambiguous_runtime_reference";
        return -1;
      }
    }
  return 0;
}
