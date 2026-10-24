"""Native canonical-IR relative-edge guards, including numeric record indices.

These call the production guard on canonical facts directly; they do not claim
bootstrap reachability or use a fixture's earlier bootstrap refusal as a pass.
"""
import subprocess
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def probe(tmp_path_factory):
    out=tmp_path_factory.mktemp('relative-image');source=out/'probe.c';executable=out/'probe'
    source.write_text(r'''
#include "m68k_object.h"
#include "m68k_ir.h"
#include "m68k_render_plan.h"
#include <stdio.h>
#include <stdlib.h>
static uint16_t m68k_read_u16be(const uint8_t *p) {return ((uint16_t)p[0]<<8)|p[1];}
#include "m68k_source_image_relations.inc"
int main(int argc,char **argv) {
 if(argc!=5)return 1;
 uint32_t storage=atoi(argv[1]),base=atoi(argv[2]),target=atoi(argv[3]),scale=atoi(argv[4]);
 if(storage>126 || !scale)return 2;
 unsigned char bytes[128]={0},checked[64]={0};
 uint16_t raw=(uint16_t)(((int32_t)target-(int32_t)base)/(int32_t)scale);
 bytes[storage]=raw>>8;bytes[storage+1]=raw;
 M68kDataReferenceIR ref={.source_offset=storage,.has_base=1,.base_offset=base,.target_offset=target,
  .reference_kind=scale==1 ? M68K_DATA_REFERENCE_KIND_BASE_DISPLACEMENT:M68K_DATA_REFERENCE_KIND_BASE_DISPLACEMENT_RANGE,
  .raw_value_width=2,.raw_value=raw,.raw_value_signed=scale==1,.value_scale=scale};
 M68kSectionAnalysisIR section={.section_index=0,.data_references=&ref,.data_reference_count=1};
 M68kSourceAnalysisIR analysis={.sections=&section,.section_count=1};
 M68kSection object_section={.data=bytes,.data_size=128,.size=128};
 M68kObject object={.sections=&object_section,.section_count=1};
 M68kRenderPlan plan={0};M68kMemoryRegionIR image={.size=64};
 const M68kRenderPlannedExpression *refused=NULL;
 const char *reason=mr_image_relative_data_guard(&analysis,&object,&plan,&image,checked,&refused);
 printf("%s %u\n",reason ? reason:"allowed",storage<64 ? checked[storage]:0);return 0;
}
''')
    subprocess.run(['cc','-Isrc',str(source),'-Lsrc/build','-lamiga_backend',
        f'-Wl,-rpath,{ROOT}/src/build','-o',str(executable)],cwd=ROOT,check=True,capture_output=True)
    return executable


@pytest.mark.parametrize('storage,base,target,scale,result',[
    (16,24,28,1,'allowed 1'),
    (16,24,80,1,'cross_owner_relative_image_reference 0'),
    (80,80,24,1,'cross_owner_relative_image_reference 0'),
    (16,80,88,1,'cross_owner_relative_image_reference 0'),
    (80,24,28,1,'cross_owner_relative_image_reference 0'),
    (80,88,96,1,'allowed 0'),
    (16,24,28,4,'allowed 1'),
    (16,24,80,4,'cross_owner_relative_image_reference 0'),
])
def test_storage_base_and_target_in_both_directions(probe,storage,base,target,scale,result):
    assert subprocess.check_output([str(probe),*map(str,(storage,base,target,scale))],text=True).strip()==result
