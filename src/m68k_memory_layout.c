#include "m68k_memory_layout.h"
#include <string.h>

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
  out->addresses[i]=(uint32_t)address;state[i]=2;return 0;
}
static int ancestor(const M68kResolvedMemoryLayout *r,int a,int b) {
  for(int i=r->parents[b];i>=0;i=r->parents[i]) if(i==a) return 1;
  return 0;
}
int m68k_memory_layout_resolve(const M68kAnalysisPolicy *p,const M68kMemoryLayoutIR *layout,
    M68kResolvedMemoryLayout *out) {
  uint8_t state[M68K_ANALYSIS_MEMORY_REGION_LIMIT]={0};
  if(!out) return -1;
  memset(out,0,sizeof(*out));out->failed_region=-1;
  for(size_t i=0;i<M68K_ANALYSIS_MEMORY_REGION_LIMIT;i++) out->parents[i]=-1;
  if(!p || !layout || p->memory_region_count>M68K_ANALYSIS_MEMORY_REGION_LIMIT ||
      layout->placement_count>M68K_ANALYSIS_MEMORY_REGION_LIMIT ||
      (layout->chip_bytes!=0x80000 && layout->chip_bytes!=0x100000))
    return fail(out,-1,"unsupported_layout_profile");
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
  }
  for(size_t i=0;i<p->memory_region_count;i++) for(size_t j=0;j<i;j++) {
    if(ancestor(out,(int)i,(int)j) || ancestor(out,(int)j,(int)i)) continue;
    if((uint64_t)out->addresses[i]+p->memory_regions[i].size>out->addresses[j] &&
        (uint64_t)out->addresses[j]+p->memory_regions[j].size>out->addresses[i])
      return fail(out,(int)i,"unrelated_region_overlap");
  }
  return 0;
}
