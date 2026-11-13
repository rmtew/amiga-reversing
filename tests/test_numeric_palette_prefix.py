"""Explicit numeric prefixes outrank printable-byte guesses without new bounds."""
import pytest

from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_typed_pointer_domains import _assert_vasm_bytes


@pytest.mark.parametrize('bounded',[False,True])
@pytest.mark.parametrize('prefix_size',[23,24])
def test_numeric_byte_prefix_preserves_separate_text_and_unknown_index(tmp_path,bounded,prefix_size):
    guard='andi.w #15,d0'if bounded else 'nop'
    asm=f''' SECTION code,code
 ORG $1000
 lea.l palette(pc),a0
 {guard}
reader: move.b 0(a0,d0.w),d1
 andi.w #255,d1
 lsl.w #4,d1
 lea.l text(pc),a1
 rts
palette: dcb.b 17,$70
 dc.b $60,$50,$40,$30,$20,$10,$00
text: dc.b "actual readable text",0
'''
    raw,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    tagged,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm+' dc.l palette,text,reader\n')
    assert tagged[:-12]==raw
    start,end,reader=[int.from_bytes(tagged[i:i+4],'big')-4096 for i in range(len(raw),len(raw)+12,4)]
    path=tmp_path/'input.bin';path.write_bytes(raw)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=4096,entrypoint=4096,
        code_start_offset=0,display_path=str(path),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[]
    def add(command,params):
        kind,payload=target_catalog_manual_payload(command,params)
        actions.append((ManualActionKind(kind),payload));return payload
    # A shorter declared prefix deliberately leaves the final zero unclaimed.
    layout=add('target.data_block.layout.create',dict(hunk=0,source_start=start,source_end=start+prefix_size,
        name='numeric_palette_prefix',default_unit='byte'))['data_block_layout']['layout_id']
    add('target.data_block.element.set',dict(layout_id=layout,offset=0,width=prefix_size,kind='array',
        name='numeric_palette_prefix',array_count=prefix_size,array_stride=1,representation='hex'))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path)as metadata:
        a=cb.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    try:
        p=a.analysis_payload()[0];s=p['sections'][0];assert not p['incomplete_analysis']
        assert not[r for r in s['range_ownerships']if r['kind_name']=='text'and
            r['start_offset']<start+prefix_size and r['end_offset']>start]
        assert any(r['kind_name']=='text'and r['start_offset']==end for r in s['range_ownerships'])
        # A storage declaration must not turn an unknown WORD index into a
        # complete table-consumer domain or consume the adjacent zero byte.
        declarations=[i for i in p['analysis_policy']['structured_data_items']if i['offset']==start]
        assert declarations and max(i['size']for i in declarations)==prefix_size
        reads=[r for r in s['address_value_consumers']if r['offset']==reader and r['kind']=='indexed_base']
        assert len(reads)==1
        assert bool(reads[0].get('index_word_known_bits',{}).get('mask',0)&0x8000)==bounded
        text=a.inline_source_text_with_profile()[0]
        assert '"pppp'not in text and '"actual readable text"'in text
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw',text)[0]==raw
        _assert_vasm_bytes(tmp_path,text,raw)
    finally:a.close()
