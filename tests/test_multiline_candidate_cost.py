"""Cheap necessary predicates precede ownership scans without changing admission."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
import pytest


def test_multiline_matches_legacy_scan_with_bounded_owner_queries(tmp_path):
    root = Path(__file__).resolve().parents[1]
    cc = shutil.which('cc')
    backend = Path(os.environ.get('AMIGA_TEST_BACKEND', root/'src/build/libamiga_backend.so'))
    if not cc or not backend.exists():
        pytest.skip('native compiler and backend required')
    source = tmp_path/'multiline.c'
    source.write_text(r'''#include "m68k_source_quality.c"
#include "util_arena.h"
#include <assert.h>
/* Reference: the prior published scan order. Test-only; no second production
 * engine, changed text predicate, ownership union or convergence cap. */
static int legacy_scan(M68kSourceAnalysisIR *a, const M68kDecodeSectionIR *s,
    M68kSectionAnalysisIR *sa, const M68kFactIR *facts, const uint8_t *code, size_t *lookups) {
 uint32_t offset=0;
 while(offset<s->size) {
  ++*lookups;
  const M68kAnalysisStructuredDataItem *item=source_quality_structured_data_item_covering_offset(a,0,offset);
  if(item && !source_quality_structured_data_item_is_weak_generic_text(item) &&
      !(item->offset==offset && source_quality_structured_data_item_is_untyped_bytes_placeholder(item))) {++offset;continue;}
  uint32_t span=source_quality_auto_multiline_string_span(a,s,sa,facts,code,offset);
  if(span) {
   if(append_source_quality_multiline_string_item(a,0,offset,span)) return -1;
   offset+=span;continue;
  }
  ++offset;
 }
 return 0;
}
static M68kSourceAnalysisIR *make_analysis(unsigned mode) {
 M68kSourceAnalysisIR *a=calloc(1,sizeof(*a));assert(a);
 a->arena=arena_create(65536);assert(a->arena);
 M68kAnalysisStructuredDataItem item={0};item.has_section_index=1;item.kind=M68K_ANALYSIS_STRUCTURED_DATA_BYTES;
 if(mode==1 || mode==3 || mode==4) {
  item.offset=128;item.size=128;
  if(mode==3) {item.kind=M68K_ANALYSIS_STRUCTURED_DATA_STRING;
   item.source_pattern_id=M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_TERMINATED_TEXT;
   item.semantic_role_flags=M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING;
  } else if(mode==1) item.semantic_role_flags=M68K_ANALYSIS_STRUCTURED_DATA_ROLE_STRING;
  assert(!m68k_ir_source_analysis_append_structured_data_item(a,&item));
 }
 item=(M68kAnalysisStructuredDataItem){0};item.has_section_index=1;item.kind=M68K_ANALYSIS_STRUCTURED_DATA_BYTES;
 for(unsigned i=0;i<1024;++i) {item.offset=8192+i*32;item.size=16;
  assert(!m68k_ir_source_analysis_append_structured_data_item(a,&item));}
 return a;
}
int main(void) {
 uint8_t *data=calloc(65536,1),*code=calloc(65536,1);assert(data && code);
 const char *text="\r\nA LONG SYNTHETIC TEXT LINE\r\nANOTHER SYNTHETIC TEXT LINE\r\n";
 memcpy(data+128,text,strlen(text)+1);
 M68kDecodeSectionIR section={0};section.data=data;section.size=65536;section.kind=M68K_SECTION_DATA;
 M68kSectionAnalysisIR sa={0};sa.section_size=65536;M68kFactIR facts={0};
 setenv("AMIGA_REVERSING_PROFILE_SOURCE_QUALITY","1",1);
 for(unsigned mode=0;mode<5;++mode) {
  memset(code,0,65536);if(mode==2) memset(code+128,1,strlen(text)+1);
  M68kSourceAnalysisIR *before=make_analysis(mode),*after=make_analysis(mode);
  size_t lookups=0;clock_t start=clock();assert(!legacy_scan(before,&section,&sa,&facts,code,&lookups));
  double old_seconds=(double)(clock()-start)/CLOCKS_PER_SEC;start=clock();
  assert(!append_multiline_string_items_for_section(after,&section,&sa,&facts,code));
  double new_seconds=(double)(clock()-start)/CLOCKS_PER_SEC;
  assert(before->structured_data_item_count==after->structured_data_item_count);
  assert(!memcmp(before->structured_data_items,after->structured_data_items,
      before->structured_data_item_count*sizeof(*before->structured_data_items)));
  unsigned found=0;for(size_t i=0;i<after->structured_data_item_count;++i)
   found+=after->structured_data_items[i].source_pattern_id==M68K_ANALYSIS_STRUCTURED_DATA_SOURCE_PATTERN_MULTILINE_TEXT;
  if(mode<3) assert(found==(mode==0?1U:0U));
  printf("{\"mode\":%u,\"legacy_owner_lookups\":%zu,\"legacy_seconds\":%.6f,\"filtered_seconds\":%.6f}\n",mode,lookups,old_seconds,new_seconds);
  m68k_ir_source_analysis_destroy(before);m68k_ir_source_analysis_destroy(after);free(before);free(after);
 }
 free(data);free(code);return 0;
}''')
    executable = tmp_path/'multiline'
    built = subprocess.run([cc, '-Isrc', '-D_POSIX_C_SOURCE=200809L', '-std=c11', '-O1', str(source), str(backend),
        f'-Wl,-rpath,{backend.parent}', '-o', str(executable)], cwd=root, capture_output=True, text=True, timeout=60)
    assert built.returncode == 0, built.stderr
    run = subprocess.run([str(executable)], capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stdout+run.stderr
    measurements = [json.loads(line) for line in run.stdout.splitlines()]
    counts = [int(n) for n in re.findall(r'owner_lookups=(\d+)', run.stderr)]
    assert len(measurements) == len(counts) == 5
    assert all(n < 128 for n in counts)
    assert all(m['legacy_owner_lookups'] > 65000 for m in measurements)
    # Counts, not host timing, are the regression gate. Timings remain useful
    # observations for one reproducible pathological fixture.
    print(json.dumps(dict(measurements=measurements, filtered_owner_lookups=counts)))
