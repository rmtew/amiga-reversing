"""Consecutive signed guards narrow WORDs without asserting caller domains."""
import pytest
from amiga_reversing.disasm import c_backend
from tests.test_base_candidates import candidate_artifact


def array_policy(count=4):
    return dict(custom_structs=[dict(name='Slot',size=4,fields=[
        dict(name='value',type='LONG',offset=0,size=4)])],entry_register_seeds=[
        dict(hunk=0,entry_offset=0,register='A0',kind='struct_ptr',struct_name='Slot',
             array_length=count,note='Supplied four-record array; scalar input unknown')])


def inspect(tmp_path,code,array_count=4):
    with candidate_artifact(tmp_path,code,[],array_policy(array_count))as(a,original):
        payload=a.analysis_payload()[0];assert not payload['incomplete_analysis']
        source=a.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
        return [r for r in payload['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']


@pytest.mark.parametrize('guards',[
    'cmp.w #43,d0\n ble.w done\n cmp.w #47,d0\n bgt.w done',
    'cmp.w #47,d0\n bgt.w done\n cmp.w #43,d0\n ble.w done',
    'cmp.w #43,d0\n bgt.s lower\n rts\nlower:\n cmp.w #47,d0\n ble.s within\n rts\nwithin:',
    'cmp.w #43,d0\n ble.w done\n cmp.w #47,d0\n ble.s within\n moveq.l #47,d0\nwithin:',
])
def test_signed_intersection_and_clamp_bound_the_actual_index(tmp_path,guards):
    refs=inspect(tmp_path,guards+'\n move.w d0,d2\n subi.w #44,d2\n add.w d2,d2\n add.w d2,d2\n move.l 0(a0,d2.w),d3\ndone: rts\n')
    assert len(refs)==1
    assert refs[0]['word_index']['byte_offsets']==[0,4,8,12]


@pytest.mark.parametrize('guards,middle',[
    ('cmp.w #47,d0\n bgt.w done',''),
    ('cmp.w #43,d0\n ble.w done',''),
    ('cmp.b #43,d0\n ble.w done\n cmp.w #47,d0\n bgt.w done',''),
    ('cmp.l #43,d0\n ble.w done\n cmp.w #47,d0\n bgt.w done',''),
    ('cmp.w #43,d0\n tst.w d1\n ble.w done\n cmp.w #47,d0\n bgt.w done',''),
    ('cmp.w #43,d0\n ble.w done\n cmp.w #47,d0\n bgt.w done','move.b d7,d0'),
    ('cmp.w #43,d0\n ble.w done\n cmp.w #47,d0\n bgt.w done','jsr $2000.l'),
    ('tst.w d7\n beq.s within\n cmp.w #43,d0\n ble.w done\n cmp.w #47,d0\n bgt.w done\nwithin:',''),
])
def test_missing_bound_clobber_partial_predicate_call_and_unknown_join_refuse(tmp_path,guards,middle):
    assert not inspect(tmp_path,guards+'\n '+middle+'\n subi.w #44,d0\n lsl.w #2,d0\n move.l 0(a0,d0.w),d3\ndone: rts\n')


@pytest.mark.parametrize('lower,upper',[(-32768,-32765),(-4,-1),(-2,1),(32764,32767)])
def test_signed_extrema_and_zero_crossing_keep_word_wrap(tmp_path,lower,upper):
    refs=inspect(tmp_path,f'cmp.w #{lower},d0\n blt.w done\n cmp.w #{upper},d0\n bgt.w done\n subi.w #{lower},d0\n lsl.w #2,d0\n move.l 0(a0,d0.w),d3\ndone: rts\n')
    assert len(refs)==1 and refs[0]['word_index']['byte_offsets']==[0,4,8,12]


@pytest.mark.parametrize('helper,expected',[
    ('nop',True),('moveq.l #0,d1',True),
    ('move.w d7,d0',False),('move.b d7,d0',False),
    ('tst.w d7\n beq.s helper_done\n move.w d7,d0\nhelper_done:',False),
    ('move.l d0,-(a7)\n moveq.l #0,d0\n move.l (a7)+,d0',True),
])
def test_call_effects_preserve_or_clobber_the_same_packet(tmp_path,helper,expected):
    refs=inspect(tmp_path,'cmp.w #43,d0\n ble.w done\n bsr.w helper\n cmp.w #47,d0\n bgt.w done\n subi.w #44,d0\n lsl.w #2,d0\n move.l 0(a0,d0.w),d3\ndone: rts\nhelper:\n '+helper+'\n rts\n')
    assert bool(refs)==expected


def test_guarded_retry_join_converges_without_expanding_the_value_cap(tmp_path):
    refs=inspect(tmp_path,'moveq.l #3,d7\nagain:\n cmp.w #43,d0\n ble.w done\n cmp.w #47,d0\n bgt.w done\n dbf.w d7,again\n subi.w #44,d0\n lsl.w #2,d0\n move.l 0(a0,d0.w),d3\ndone: rts\n')
    assert len(refs)==1 and refs[0]['word_index']['byte_offsets']==[0,4,8,12]


@pytest.mark.parametrize('prefix,suffix',[
    ('lea.l after_lower(pc),a1\n',''),
    ('','cmp.w #43,d0\n bgt.w done'),
])
def test_independent_entry_and_contradictory_bounds_do_not_gain_values(tmp_path,prefix,suffix):
    refs=inspect(tmp_path,prefix+'cmp.w #43,d0\n ble.w done\nafter_lower:\n cmp.w #47,d0\n bgt.w done\n '+suffix+'\n subi.w #44,d0\n lsl.w #2,d0\n move.l 0(a0,d0.w),d3\ndone: rts\n')
    assert not refs


def test_unmaterialized_range_survives_a_word_register_copy(tmp_path):
    refs=inspect(tmp_path,'cmp.w #43,d0\n ble.w done\n move.w d0,d2\n moveq.l #0,d0\n cmp.w #47,d2\n bgt.w done\n subi.w #44,d2\n lsl.w #2,d2\n move.l 0(a0,d2.w),d3\ndone: rts\n')
    assert len(refs)==1 and refs[0]['word_index']['byte_offsets']==[0,4,8,12]


def test_large_range_does_not_expand_the_finite_value_cap(tmp_path):
    refs=inspect(tmp_path,'cmp.w #0,d0\n blt.w done\n cmp.w #15,d0\n bgt.w done\n lsl.w #2,d0\n move.l 0(a0,d0.w),d3\ndone: rts\n',array_count=16)
    assert not refs


def test_modular_intersections_and_joins_cover_the_mathematical_word_sets(tmp_path):
    import os,shutil,subprocess
    from pathlib import Path
    root=Path(__file__).resolve().parents[1];compiler=shutil.which('cc')
    backend=Path(os.environ.get('AMIGA_TEST_BACKEND',root/'src/build/libamiga_backend.so'))
    if not compiler or not backend.exists():pytest.skip('host compiler and backend required')
    source=tmp_path/'word-bounds.c'
    source.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include <assert.h>
static int arc(uint16_t x,uint16_t lo,uint16_t hi) {return lo<=hi ? x>=lo && x<=hi : x>=lo || x<=hi;}
static int contains(const M68kHardwareWordSet *s,uint16_t x) {
  if(s->count) {for(unsigned i=0;i<s->count;++i)if(s->values[i]==x)return 1;return 0;}
  return (x&s->known_bits_mask)==s->known_bits_value && (!s->has_bounds || arc(x,s->lower_bound,s->upper_bound));
}
int main(void) {
  uint32_t random=0x639AF812U;
  const uint16_t masks[]={0,0x8000,0xFF00,0xFFF0,0x0003,0xFFFF};
  for(unsigned c=0;c<72;++c) {
    uint16_t p[5];for(unsigned k=0;k<5;++k) {random=random*1664525U+1013904223U;p[k]=(uint16_t)(random>>8);}
    M68kHardwareWordSet original={0},result,joined,other={0};
    original.has_bounds=1;original.lower_bound=p[0];original.upper_bound=p[1];
    original.known_bits_mask=masks[c%6];original.known_bits_value=p[4]&original.known_bits_mask;
    original.requires_input_contract=(c%7)==0;
    result=original;int allows=hardware_word_refine_bounds(&result,p[2],p[3]);unsigned actual=0;
    for(uint32_t v=0;v<=UINT16_MAX;++v) {
      int input=original.requires_input_contract || contains(&original,(uint16_t)v);
      if(input && arc((uint16_t)v,p[2],p[3])) {++actual;assert(allows && contains(&result,(uint16_t)v));}
    }
    if(!allows)assert(!actual);
    if(allows && result.count)for(unsigned i=0;i<result.count;++i)
      assert((original.requires_input_contract || contains(&original,result.values[i])) && arc(result.values[i],p[2],p[3]));
    other.has_bounds=1;other.lower_bound=p[2];other.upper_bound=p[3];
    if(c%3==0) {other.lower_bound=original.lower_bound;other.upper_bound=original.upper_bound;}
    original.requires_input_contract=0;joined=original;hardware_word_set_merge(&joined,&other);
    for(uint32_t v=0;v<=UINT16_MAX;++v)
      if(contains(&original,(uint16_t)v)||contains(&other,(uint16_t)v))assert(contains(&joined,(uint16_t)v));
  }
  return 0;
}
''')
    exe=tmp_path/'word-bounds'
    built=subprocess.run([compiler,'-Isrc','-Isrc/generated','-w',str(source),str(backend),
        f'-Wl,-rpath,{backend.parent}','-lm','-o',str(exe)],cwd=root,text=True,capture_output=True,timeout=60)
    assert built.returncode==0,built.stderr
    result=subprocess.run([str(exe)],text=True,capture_output=True,timeout=10)
    assert result.returncode==0,result.stderr
