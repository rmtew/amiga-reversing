"""Known text is positive evidence, not a reason to miss adjacent unknown text."""
import pytest
from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata
from amiga_reversing.disasm.manual_actions import append_manual_actions,ManualActionKind as Kind
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from tests.test_typed_pointer_domains import _assert_vasm_bytes


@pytest.mark.parametrize('mode',['unowned','one_known','two_known','growth','opaque_neighbors','opaque_target','unreferenced','isolated','local_numbers'])
def test_declaring_known_strings_preserves_pointer_pool_discovery(tmp_path,mode):
    asm=''' SECTION code,code
 ORG $1000
 lea.l directory(pc),a0
 movea.l 0(a0,d0.w),a1
 rts
 directory: dc.l first,second,third,0
 first: dc.b "FIRST TEXT",0
 second: dc.b "SECOND TEXT",0
 third: dc.b " If you need this...",0
 finish:
'''
    if mode=='growth':
        entries=['first','second','third']+[f'extra{i}'for i in range(1,70)]+['0']
        asm=asm.replace('directory: dc.l first,second,third,0','directory:\n'+'\n'.join(' dc.l '+','.join(entries[i:i+8])for i in range(0,len(entries),8)))
        asm=asm.replace(' finish:', ''.join(f' extra{i}: dc.b \" If you need option {i}...\",0\n'for i in range(1,70))+' finish:')
    if mode=='isolated':asm=asm.replace(' third:', ' dc.b $80,$81,$82,$83,$84,$85\n third:')
    raw,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    symbols,_=cb.assemble_platform_source_text_with_c_backend('amiga-raw',asm+' dc.l first,second,third,finish\n')
    first,second,third,finish=[int.from_bytes(symbols[i:i+4],'big')-4096 for i in range(len(raw),len(raw)+16,4)]
    if mode in ('unreferenced','local_numbers'):
        data=bytearray(raw)
        if mode=='unreferenced':data[18:22]=(4096+second).to_bytes(4,'big')
        else:
            for pos in (10,14,18):data[pos:pos+4]=(int.from_bytes(data[pos:pos+4],'big')-4096).to_bytes(4,'big')
        raw=bytes(data)
    path=tmp_path/'pool.bin';path.write_bytes(raw)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=path,address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=4096,entrypoint=4096,code_start_offset=0,display_path=str(path),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    seeds=[dict(seed_id='directory',kind='data',mode='required',hunk=0,addr=10,end=first,
                name='text_directory',data_role='pointer_table',unit='long')]
    if mode!='unowned':
        for n,start,end in [('first',first,second),('second',second,third-(6 if mode=='isolated'else 0))]:
            if mode=='one_known'and n=='second':continue
            seeds.append(dict(seed_id=n,kind='data',mode='required',hunk=0,addr=start,end=end,
                name=n+'_known',data_role='raw'if mode=='opaque_neighbors'else'string',unit='byte',encoding='ascii'))
    if mode=='opaque_target':seeds.append(dict(seed_id='target',kind='data',mode='required',hunk=0,addr=third,end=finish,name='opaque',data_role='raw',unit='byte'))
    append_manual_actions(tmp_path,binary_source=source,actions=[(Kind.CREATE_MANUAL_SEED,{'seed':seed})for seed in seeds])
    with effective_metadata_file(tmp_path)as metadata:
        a=cb.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    try:
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        found=[i for i in p['analysis_policy']['structured_data_items']if i.get('offset')==third and i.get('source_pattern')=='pointer_string_table']
        if mode in ('unowned','one_known','two_known','growth'):assert found, f'{mode}: referenced leading-space text was not recovered'
        else:assert not found
        if mode=='growth':
            targets={int.from_bytes(raw[i:i+4],'big')-4096 for i in range(18,18+70*4,4)}
            strings={i['offset']for i in p['analysis_policy']['structured_data_items']if i.get('source_pattern')=='pointer_string_table'}
            assert targets<=strings
        text=a.inline_source_text_with_profile()[0]
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw',text)[0]==raw
        _assert_vasm_bytes(tmp_path,text,raw)
    finally:a.close()
