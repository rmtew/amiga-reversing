"""Indexed typed-region lookup preserves the old finite interval semantics."""
import json
import shutil
import subprocess
from pathlib import Path
import pytest


def test_native_reference_index_alias_boundaries_and_scaling(tmp_path):
    cc=shutil.which('cc')
    if not cc:pytest.skip('Native reference-index probe requires cc')
    root=Path(__file__).resolve().parents[1];source=tmp_path/'index.c';binary=tmp_path/'index'
    source.write_text(r'''
#include "m68k_memory_layout.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int ancestor(const M68kResolvedMemoryLayout *r,int a,int b) {
 for(int i=r->parents[b];i>=0;i=r->parents[i]) if(i==a) return 1;return 0;
}
static int linear(const M68kAnalysisPolicy *p,const M68kResolvedMemoryLayout *r,unsigned address,unsigned width) {
 int selected=-1;unsigned long long end=(unsigned long long)address+(width ? width : 1);
 for(unsigned i=0;i<p->memory_region_count;i++) {
  const M68kMemoryRegionIR *v=&p->memory_regions[i];
  if(address<v->runtime_address || end>(unsigned long long)v->runtime_address+v->size) continue;
  if(selected<0 || ancestor(r,selected,i)) selected=i;
  else if(!ancestor(r,i,selected)) return -1;
 }
 if(selected>=0) return selected+1;
 for(unsigned i=0;i<p->memory_region_count;i++) {
  const M68kMemoryRegionIR *v=&p->memory_regions[i];
  if(r->addresses[i]!=v->runtime_address && address<(unsigned long long)v->runtime_address+v->size && end>v->runtime_address) return -1;
 }
 return 0;
}
static void check(const M68kAnalysisPolicy *p,const M68kResolvedMemoryLayout *r) {
 const unsigned widths[]={0,1,2,8,16,32,0x100000};char expression[128];unsigned placed;
 for(unsigned address=0xfff;address<0x12000;address+=17) for(unsigned w=0;w<7;w++) {
  int wanted=linear(p,r,address,widths[w]);
  int got=m68k_memory_layout_reference(p,r,address,widths[w],expression,sizeof(expression),&placed);
  assert(got==(wanted>0 ? 1 : wanted));
  if(wanted>0) assert(placed==r->addresses[wanted-1]+address-p->memory_regions[wanted-1].runtime_address);
 }
}
int main(void) {
 M68kAnalysisPolicy *p=calloc(1,sizeof(*p));assert(p);
 M68kMemoryLayoutIR l={0};M68kResolvedMemoryLayout r;char expression[128];unsigned placed;size_t steps[3],wide[3];
 for(unsigned batch=0;batch<3;batch++) {
  memset(p,0,sizeof(*p));memset(&l,0,sizeof(l));unsigned n=4U<<batch;
  p->memory_region_count=l.placement_count=n;l.chip_bytes=0x100000;
  for(unsigned i=0;i<n;i++) {
   M68kMemoryRegionIR *v=&p->memory_regions[i];snprintf(v->region_id,96,"r%u",i);snprintf(v->name,96,"r%u_base",i);
   v->runtime_address=0x1000+i*0x1000;v->size=16;v->alignment=2;
   strcpy(l.placements[i].region_id,v->region_id);l.placements[i].runtime_address=0x80000+i*0x1000;
  }
  assert(!m68k_memory_layout_resolve(p,&l,&r));check(p,&r);
  assert(m68k_memory_layout_reference_profiled(p,&r,0x1004+(n-1)*0x1000,1,expression,sizeof(expression),&placed,&steps[batch])==1);
  size_t other;
  assert(m68k_memory_layout_reference_profiled(p,&r,0x1000,0x100000,expression,sizeof(expression),NULL,&wide[batch])==-1);
  assert(m68k_memory_layout_reference_profiled(p,&r,0x1000,0x800000,expression,sizeof(expression),NULL,&other)==-1);
  assert(other==wide[batch]);
 }
 /* Hierarchy plus a range wider than the deepest owner. */
 memset(p,0,sizeof(*p));memset(&l,0,sizeof(l));p->memory_region_count=3;l.chip_bytes=0x100000;l.placement_count=1;
 for(unsigned i=0;i<3;i++) {snprintf(p->memory_regions[i].region_id,96,"r%u",i);snprintf(p->memory_regions[i].name,96,"r%u_base",i);p->memory_regions[i].alignment=2;}
 p->memory_regions[0].runtime_address=0x4000;p->memory_regions[0].size=256;
 p->memory_regions[1].runtime_address=0x4040;p->memory_regions[1].size=32;strcpy(p->memory_regions[1].parent_region_id,"r0");
 p->memory_regions[2].runtime_address=0x4048;p->memory_regions[2].size=8;strcpy(p->memory_regions[2].parent_region_id,"r1");
 strcpy(l.placements[0].region_id,"r0");l.placements[0].runtime_address=0x80000;
 assert(!m68k_memory_layout_resolve(p,&l,&r));check(p,&r);
 assert(m68k_memory_layout_reference(p,&r,0x4049,1,expression,sizeof(expression),&placed)==1 && placed==0x80049);
 assert(!strcmp(expression,"r2_base+$1"));
 /* Unrelated original overlaps can separate at placement; typed ambiguity stays. */
 p->memory_region_count=2;p->memory_regions[0].size=32;p->memory_regions[1].runtime_address=0x4010;p->memory_regions[1].size=32;p->memory_regions[1].parent_region_id[0]=0;
 l.placement_count=2;strcpy(l.placements[1].region_id,"r1");l.placements[1].runtime_address=0x90000;
 assert(!m68k_memory_layout_resolve(p,&l,&r));check(p,&r);
 printf("{\"point_steps\":[%zu,%zu,%zu],\"large_span_steps\":[%zu,%zu,%zu]}",steps[0],steps[1],steps[2],wide[0],wide[1],wide[2]);
 free(p);return 0;
}
''')
    subprocess.run([cc,'-std=c11','-I',str(root/'src'),str(source),'-L',str(root/'src/build'),
        '-lamiga_backend','-Wl,-rpath,'+str(root/'src/build'),'-o',str(binary)],check=True,capture_output=True)
    result=subprocess.run([str(binary)],check=True,capture_output=True,text=True)
    metrics=json.loads(result.stdout)
    assert metrics['point_steps']==[4,5,6]
    assert metrics['large_span_steps']==[7,9,11]
