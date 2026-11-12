"""Scan-local ownership reuse must match canonical first-declaration lookup."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_owner_cursor_matches_overlaps_mutations_and_sparse_queries(tmp_path):
    root=Path(__file__).resolve().parents[1];cc=shutil.which('cc')
    backend=Path(os.environ.get('AMIGA_TEST_BACKEND',root/'src/build/libamiga_backend.so'))
    if not cc or not backend.exists():pytest.skip('host compiler and backend required')
    source=tmp_path/'owner-cursor.c'
    source.write_text(r'''#include "m68k_source_quality.c"
#include <assert.h>
static void check(M68kSourceAnalysisIR *a,SourceQualityOwnerCursor *c,uint32_t sec,uint32_t off) {
  assert(source_quality_covering_item_at_cursor(a,sec,off,c)==
    source_quality_structured_data_item_covering_offset(a,sec,off));
}
int main(int argc,char **argv) {
  (void)argv;
  M68kSourceAnalysisIR a={0};SourceQualityOwnerCursor cursor={0};
  size_t n=argc>1?17029U:128U;
  a.structured_data_items=calloc(n,sizeof(*a.structured_data_items));assert(a.structured_data_items);
  a.structured_data_item_count=n;
  uint32_t random=0x8261631U;
  for(size_t i=0;i<n;++i) {
    M68kAnalysisStructuredDataItem *v=&a.structured_data_items[i];
    random=random*1664525U+1013904223U;
    v->has_section_index=(i%11)!=0;v->section_index=i%3;
    v->offset=(random>>9)%1024;v->size=(random>>20)%257;
    if(i%17==0)v->offset=UINT32_MAX-3U; /* overflow ranges are ignored */
  }
  for(unsigned sec=0;sec<4;++sec) {
    for(uint32_t off=0;off<1300;++off)check(&a,&cursor,sec,off);
    for(int32_t off=1300;off>=0;off-=7)check(&a,&cursor,sec,(uint32_t)off);
    check(&a,&cursor,sec,UINT32_MAX);check(&a,&cursor,sec,UINT32_MAX-2U);
  }
  /* A later broad owner must stop at an earlier declaration's future start,
   * including a weaker placeholder. Priority is not union or shortest range. */
  memset(a.structured_data_items,0,n*sizeof(*a.structured_data_items));
  a.structured_data_items[0]=(M68kAnalysisStructuredDataItem){.has_section_index=1,.offset=20,.size=10};
  a.structured_data_items[1]=(M68kAnalysisStructuredDataItem){.has_section_index=1,.offset=0,.size=100};
  cursor.valid=0;
  for(uint32_t off=0;off<=100;++off)check(&a,&cursor,0,off);
  /* In-place replacement and count-preserving deletion invalidate the cursor,
   * exactly as both string-promotion callers do after their mutation. */
  a.structured_data_items[0].offset=4;a.structured_data_items[0].size=3;cursor.valid=0;
  for(uint32_t off=0;off<=100;++off)check(&a,&cursor,0,off);
  memmove(a.structured_data_items,a.structured_data_items+1,(n-1)*sizeof(*a.structured_data_items));
  --a.structured_data_item_count;cursor.valid=0;
  for(uint32_t off=0;off<=100;++off)check(&a,&cursor,0,off);
  /* Many earlier future declarations with a final covering owner reproduce
   * the expensive repeated linear scan without a timing-sensitive assertion. */
  a.structured_data_item_count=n;
  for(size_t i=0;i<n;++i)a.structured_data_items[i]=(M68kAnalysisStructuredDataItem){
    .has_section_index=1,.offset=60000,.size=1};
  a.structured_data_items[n-1].offset=0;a.structured_data_items[n-1].size=65536;
  uint32_t queries=argc>1?54227U:8192U;volatile size_t sum=0;
  clock_t started=clock();
  for(uint32_t off=0;off<queries;++off)sum+=(size_t)(source_quality_structured_data_item_covering_offset(&a,0,off)-a.structured_data_items);
  double legacy=(double)(clock()-started)/CLOCKS_PER_SEC;
  cursor=(SourceQualityOwnerCursor){0};started=clock();
  for(uint32_t off=0;off<queries;++off)sum+=(size_t)(source_quality_covering_item_at_cursor(&a,0,off,&cursor)-a.structured_data_items);
  double cached=(double)(clock()-started)/CLOCKS_PER_SEC;
  assert(cursor.cache_hits==queries-1 && cursor.scanned_items<=2*n);
  assert(sum==(size_t)2*queries*(n-1));
  printf("owners=%zu queries=%u legacy=%.6f cursor=%.6f inspected=%zu hits=%zu\n",n,queries,legacy,cached,cursor.scanned_items,cursor.cache_hits);
  free(a.structured_data_items);return 0;
}
''')
    exe=tmp_path/'owner-cursor'
    built=subprocess.run([cc,'-Isrc','-Isrc/generated','-w','-O2',str(source),str(backend),
        f'-Wl,-rpath,{backend.parent}','-lm','-o',str(exe)],cwd=root,text=True,capture_output=True,timeout=60)
    assert built.returncode==0,built.stderr
    result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr
    print(result.stdout,end='')
