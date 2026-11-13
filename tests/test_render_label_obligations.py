"""The sparse source-label snapshot agrees with an unordered linear oracle."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_source_label_snapshot_preserves_sections_duplicates_and_endpoints(tmp_path):
    root=Path(__file__).resolve().parents[1]
    cc=shutil.which('cc')
    backend=Path(os.environ.get('AMIGA_TEST_BACKEND',root/'src/build/libamiga_backend.so'))
    if not cc or not backend.exists():pytest.skip('native compiler and backend required')
    source=tmp_path/'labels.c'
    source.write_text(r'''
#include "m68k_render_ir.c"
#include <assert.h>
static int linear(const M68kRenderPlan *p,uint32_t section,uint32_t offset) {
 for(size_t i=0;i<p->declaration_count;i++) {
  const M68kRenderPlannedDeclaration *d=&p->declarations[i];
  if(d->kind==M68K_RENDER_PLANNED_DECLARATION_LABEL && d->has_source_target &&
     d->section_index==section && d->offset==offset)return 1;
 }
 return 0;
}
int main(void) {
 M68kRenderPlan plan={0};M68kRenderPlannedDeclaration declarations[131]={{0}},before[131];
 uint32_t seed=68000;size_t count=0;uint64_t *items=NULL;
 assert(!source_label_obligations_build(&plan,&items,&count) && !count && !items);
 assert(!source_label_obligations_lower_bound(items,count,UINT64_MAX));
 for(size_t i=0;i<128;i++) {
  seed=1664525U*seed+1013904223U;
  declarations[i].section_index=(seed>>16)%10;
  declarations[i].offset=seed%256;
  declarations[i].kind=i%3 ? M68K_RENDER_PLANNED_DECLARATION_LABEL : M68K_RENDER_PLANNED_DECLARATION_EQUATE;
  declarations[i].has_source_target=i%5!=0;
  /* Equal runtime addresses must not collapse different source sections. */
  declarations[i].has_runtime_target=1;declarations[i].runtime_address=0x1000;
 }
 declarations[128]=declarations[1]; /* Duplicate coordinate still denotes one emitted position. */
 declarations[129]=(M68kRenderPlannedDeclaration){.section_index=0,.offset=256,
  .kind=M68K_RENDER_PLANNED_DECLARATION_LABEL,.has_source_target=1};
 declarations[130]=(M68kRenderPlannedDeclaration){.section_index=UINT32_MAX,.offset=UINT32_MAX,
  .kind=M68K_RENDER_PLANNED_DECLARATION_LABEL,.has_source_target=1};
 plan.declarations=declarations;plan.declaration_count=131;memcpy(before,declarations,sizeof before);
 assert(!source_label_obligations_build(&plan,&items,&count));
 assert(!memcmp(before,declarations,sizeof before));
 const uint32_t sections[]={9,0,7,1,8,3,6,5,2,4,10};
 for(size_t s=0;s<sizeof sections/sizeof sections[0];s++) {
  uint32_t section=sections[s];
  size_t cursor=source_label_obligations_lower_bound(items,count,(uint64_t)section<<32);
  for(uint32_t offset=0;offset<=257;offset++) {
   uint64_t key=((uint64_t)section<<32)|offset;
   while(cursor<count && items[cursor]<key)++cursor;
   assert((cursor<count && items[cursor]==key)==linear(&plan,section,offset));
  }
 }
 size_t last=source_label_obligations_lower_bound(items,count,UINT64_MAX);
 assert(last<count && items[last]==UINT64_MAX);
 free(items);
 /* The live plan's label lookup has the same ordered/unordered contract as
  * instruction lookup, including moves and finalized arena storage. */
 M68kRenderPlan labels, moved;
 m68k_render_plan_init(&labels);m68k_render_plan_init(&moved);
 for(uint32_t i=0;i<64;i++) {
  M68kRenderPlannedLabel label={.source_section_index=i/16,.source_offset=(i%16)*4};
  snprintf(label.name,sizeof label.name,"label_%u",i);
  assert(!m68k_render_plan_append_label(&labels,&label));
 }
 assert(labels.labels_source_ordered);
 for(uint32_t i=0;i<64;i++) {
  const M68kRenderPlannedLabel *label=m68k_render_plan_find_label(&labels,i/16,(i%16)*4);
  assert(label && label->source_section_index==i/16 && label->source_offset==(i%16)*4);
  assert(!m68k_render_plan_find_label(&labels,i/16,(i%16)*4+1));
 }
 M68kRenderPlannedLabel duplicate=labels.labels[0];
 assert(m68k_render_plan_append_label(&labels,&duplicate)==-1 && labels.labels_source_ordered);
 assert(!m68k_render_plan_finalize(&labels) && labels.labels_source_ordered);
 assert(m68k_render_plan_find_label(&labels,3,60));
 m68k_render_plan_move(&moved,&labels);
 assert(moved.labels_source_ordered && labels.labels_source_ordered);
 assert(m68k_render_plan_find_label(&moved,0,0));
 m68k_render_plan_destroy(&moved);
 for(uint32_t i=0;i<4;i++) {
  M68kRenderPlannedLabel label={.source_section_index=3-i,.source_offset=i};
  snprintf(label.name,sizeof label.name,"unordered_%u",i);
  assert(!m68k_render_plan_append_label(&labels,&label));
 }
 assert(!labels.labels_source_ordered);
 for(uint32_t i=0;i<4;i++)assert(m68k_render_plan_find_label(&labels,3-i,i));
 duplicate=labels.labels[0];
 assert(m68k_render_plan_append_label(&labels,&duplicate)==-1);
 assert(!m68k_render_plan_finalize(&labels) && !labels.labels_source_ordered);
 for(uint32_t i=0;i<4;i++)assert(m68k_render_plan_find_label(&labels,3-i,i));
 m68k_render_plan_destroy(&labels);return 0;
}
''')
    exe=tmp_path/'labels'
    built=subprocess.run([cc,'-Isrc','-D_POSIX_C_SOURCE=200809L','-std=c11','-O0',str(source),str(backend),
        f'-Wl,-rpath,{backend.parent}','-lm','-o',str(exe)],cwd=root,capture_output=True,text=True,timeout=60)
    assert built.returncode==0,built.stderr
    result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stdout+result.stderr
