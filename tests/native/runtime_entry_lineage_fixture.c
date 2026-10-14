/* Private lineage discriminator plus actual native ownership/rebuild checks. */
#include "m68k_analysis_facts_v2.c"
#include "platform_file_lib.h"
#include <assert.h>
#include <stdio.h>

static int code_at(const M68kSourceAnalysisIR *a,uint32_t offset) {
  for(size_t i=0;i<a->sections[0].range_ownership_count;i++) {
    const M68kRangeOwnershipIR *r=&a->sections[0].range_ownerships[i];
    if(r->kind==M68K_RANGE_OWNERSHIP_CODE&&r->start_offset<=offset&&offset<r->end_offset)return 1;
  }return 0;
}
static void check_case(int mode,const char *dir) {
  unsigned char bytes[64]={0x4e,0x75};
  M68kObject object;M68kSection section={0};M68kAnalysisPolicy policy;
  M68kFactsV2Profile profile;M68kSourceAnalysisIR analysis={0};char *source=NULL;
  /* Source root at 16: numeric runtime fallback advances through NOP to JSR. */
  bytes[16]=0x4e;bytes[17]=0x71;bytes[18]=0x4e;bytes[19]=0xb9;
  bytes[22]=(mode==2||mode==3)?0U:1U;bytes[23]=32U;
  bytes[24]=0x4e;bytes[25]=0x75;bytes[32]=0x4e;bytes[33]=0x75;
  if(mode==4) { /* PC-relative BSR is source authoritative. */
    bytes[18]=0x61;bytes[19]=12;bytes[20]=0x4e;bytes[21]=0x75;
  }
  if(mode==7) {unsigned char code[]={0x41,0xfa,0x00,0x0e,0x4e,0xd0};memcpy(bytes+16,code,sizeof(code));}
  if(mode==8) {unsigned char code[]={0x70,0x00,0xd0,0x40,0x4e,0xfb,0x00,0x02,
    0x4e,0x75,0x60,0x06,0x60,0x0a,0x70,0x7f,0x4e,0x75,0x70,0x01,0x4e,0x75,0x70,0x02,0x4e,0x75};
    memcpy(bytes+16,code,sizeof(code));}
  if(mode==9)bytes[22]=0U;
  if(mode==10) {unsigned char code[]={0x20,0x7c,0x00,0x00,0x01,0x20,0x4e,0xd0};memcpy(bytes+16,code,sizeof(code));}
  assert(m68k_object_create(&object)==0);section.kind=M68K_SECTION_CODE;
  section.data=bytes;section.size=section.data_size=sizeof(bytes);
  assert(m68k_object_add_section(&object,&section).ok);m68k_analysis_policy_init_default(&policy);
  if(mode==9) {M68kFixup fixup={0};object.platform_backend_kind=M68K_PLATFORM_BACKEND_AMIGA_HUNK;
    fixup.section_index=0;fixup.offset=20;fixup.kind=M68K_FIXUP_ABS;fixup.width=M68K_FIXUP_WIDTH_32;
    fixup.has_target_section=1;fixup.target_section_index=0;fixup.addend=32;
    assert(m68k_object_add_fixup(&object,&fixup).ok);}

  policy.runtime_range_count=1;policy.runtime_ranges[0].size=sizeof(bytes);
  policy.runtime_ranges[0].runtime_address=mode==2?0U:0x100U;
  if(mode==3) {policy.runtime_ranges[0].use_mask=M68K_ANALYSIS_RUNTIME_RANGE_USE_POINTER_TARGET;
    policy.runtime_range_count=2;policy.runtime_ranges[1].size=sizeof(bytes);}
  policy.entry_point_count=1;policy.entry_points[0].offset=16;
  if(mode==1) {policy.entry_point_count=0;policy.has_entry_offset=1;policy.entry_offset=16;}
  if(mode==5) {policy.entry_point_count=0;policy.runtime_entry_point_count=1;
    policy.runtime_entry_points[0].runtime_address=0x110U;}
  if(mode==6) {policy.entry_point_count=0;policy.runtime_entry_point_count=1;
    policy.runtime_entry_points[0].runtime_address=0x110U;
    policy.runtime_range_count=2;policy.runtime_ranges[1]=policy.runtime_ranges[0];
    policy.runtime_ranges[1].offset=8;policy.runtime_ranges[1].size=56;}
  if(mode==6) {
    M68kRuntimeAddressRange maps[2]={{0}};M68kRuntimeAddressSpace space={0};uint32_t offset;
    maps[0].section_index=maps[1].section_index=0U;maps[0].kind=maps[1].kind=M68K_FACT_RUNTIME_RANGE_KIND_POLICY;
    maps[0].runtime_address=maps[1].runtime_address=0x100U;maps[0].size=64U;maps[1].size=56U;
    maps[1].source_offset=8U;space.ranges=maps;space.count=2U;
    assert(!runtime_policy_entry_is_unique(&space,0U,0x110U,1,&offset));
    m68k_analysis_policy_destroy(&policy);m68k_object_destroy(&object);return;
  }
  if(mode==9) {
    assert(m68k_facts_v2_collect_source_analysis_profile(&object,&policy,&profile,&analysis,m68k_diag_sink(NULL))==0);
    assert(code_at(&analysis,16)&&code_at(&analysis,18)&&code_at(&analysis,32));
    m68k_ir_source_analysis_destroy(&analysis);m68k_analysis_policy_destroy(&policy);m68k_object_destroy(&object);return;
  }
  assert(m68k_facts_v2_render_asm_source_analysis_profile_alloc(&object,&policy,&source,&profile,
    &analysis,1,m68k_diag_sink(NULL))==0);
  fprintf(stderr,"mode=%d target=%d\n",mode,code_at(&analysis,32));
  assert(code_at(&analysis,16));
  if(mode==0)assert(code_at(&analysis,18));
  if(mode==8)assert(code_at(&analysis,24)&&code_at(&analysis,26)&&code_at(&analysis,28)&&code_at(&analysis,34));
  else assert(code_at(&analysis,32)==(mode!=0&&mode!=6&&mode!=10));
  if(mode==6)assert(!code_at(&analysis,16));
  {unsigned char *rebuilt=NULL;size_t n=0;char *p=NULL,*error=NULL;
    assert(platform_file_assemble_source_text_bytes_profile_alloc("amiga-raw","",source,"68000",
      &rebuilt,&n,&p,&error)==0);assert(n==sizeof(bytes)&&!memcmp(bytes,rebuilt,n));
    platform_file_free_bytes(rebuilt);platform_file_free_text(p);platform_file_free_text(error);}
  if(dir) {char path[1024];FILE *f;snprintf(path,sizeof(path),"%s/entry-%d.s",dir,mode);
    f=fopen(path,"wb");assert(f);fwrite(source,1,strlen(source),f);fclose(f);
    snprintf(path,sizeof(path),"%s/entry-%d.bin",dir,mode);f=fopen(path,"wb");assert(f);
    fwrite(bytes,1,sizeof(bytes),f);fclose(f);}
  m68k_facts_v2_free_text(source);m68k_ir_source_analysis_destroy(&analysis);
  m68k_analysis_policy_destroy(&policy);m68k_object_destroy(&object);
}
int main(int argc,char **argv) {
  for(int mode=0;mode<11;mode++)check_case(mode,argc>1?argv[1]:NULL);
  puts("entry lineage fixtures passed");return 0;
}
