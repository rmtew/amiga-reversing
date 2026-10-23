"""Declared embedded records expand as leaves, with one enclosing owner."""
import subprocess

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file, effective_target_metadata
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def fixture(tmp_path, count=1, prefix=0, exception=None, depth=1):
    inner_size, field_size = 6, 8 if exception == 'size' else 6
    outer_size = prefix + field_size + 4
    header = (2 + prefix).to_bytes(4,'big') + bytes.fromhex('1234') + bytes(field_size-inner_size)
    record = bytes.fromhex('cafe') * (prefix // 2) + header + (2 + prefix).to_bytes(4,'big')
    if exception == 'cycle':outer_size=4;record=bytes(4)
    binary=tmp_path/'input.bin';original=bytes.fromhex('4e75')+record*count;binary.write_bytes(original)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,address_model=RawAddressModel.LOCAL_OFFSET,load_address=0,entrypoint=0,code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[]
    def add(command,parameters):
        kind,payload=target_catalog_manual_payload(command,parameters);actions.append((ManualActionKind(kind),payload));return payload
    add('target.custom_struct.add',dict(name='Header',size=inner_size,fields=[dict(name='pixels',type='LONG',offset=0,size=4,value_kind='target_pointer',pointer_address_domain='mapped_source'),dict(name='flags',type='WORD',offset=4,size=2)]))
    if depth == 2:
        add('target.custom_struct.add',dict(name='Leaf',size=inner_size,fields=[dict(name='pixels',type='LONG',offset=0,size=4,value_kind='target_pointer',pointer_address_domain='mapped_source'),dict(name='flags',type='WORD',offset=4,size=2)]))
        add('target.custom_struct.edit',dict(name='Header',size=inner_size,fields=[dict(name='payload',type='STRUCT',struct='Leaf',offset=0,size=inner_size)]))
    fields=([dict(name='prefix',type='WORD',offset=0,size=prefix)]if prefix else [])+[dict(name='header',type='STRUCT',struct='Missing'if exception=='unknown'else'Header',offset=prefix,size=field_size),dict(name='next',type='LONG',offset=prefix+field_size,size=4,value_kind='struct_pointer',pointer_struct='Header',pointer_address_domain='mapped_source')]
    if exception=='cycle':fields=[dict(name='header',type='STRUCT',struct='Outer',offset=0,size=4)]
    add('target.custom_struct.add',dict(name='Outer',size=outer_size,fields=fields))
    owner=add('target.data_block.layout.create',dict(hunk=0,source_start=2,source_end=len(original),name='nested_records',role='data'))['data_block_layout']
    add('target.data_block.element.set',dict(layout_id=owner['layout_id'],offset=0,width=len(original)-2,kind='struct',array_count=count,array_stride=outer_size,binding_kind='custom_struct',type_id='Outer',name='records'))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    return source,original,effective_target_metadata(tmp_path),outer_size


@pytest.mark.parametrize('count,prefix,depth',[(1,0,1),(1,2,1),(2,0,1),(2,2,1),(1,2,2),(2,2,2)])
def test_declared_nested_leaves_keep_parent_span_and_exact_source(tmp_path,count,prefix,depth):
    source,original,metadata,stride=fixture(tmp_path,count,prefix,depth=depth)
    entities=metadata.seeded_entities
    leaf='Leaf' if depth==2 else 'Header'
    assert len([e for e in entities if e.struct_name==leaf])==2*count
    assert entities[0].name=='nested_records'
    assert (entities[0].source_owner_start,entities[0].source_owner_size)==(2,len(original)-2)
    assert sum(e.source_owner_start is not None for e in entities)==1
    for index in range(count):
        fields={e.field_name:e for e in entities if e.struct_name==leaf and 2+index*stride<=e.addr<2+(index+1)*stride}
        assert (fields['pixels'].addr,fields['pixels'].end)==(2+index*stride+prefix,6+index*stride+prefix)
        assert fields['pixels'].value_kind=='target_pointer' and fields['pixels'].pointer_address_domain=='mapped_source'
        assert fields['flags'].addr==6+index*stride+prefix
    with effective_metadata_file(tmp_path)as path:artifact=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=path)[2]
    try:
        text=artifact.source_text_with_profile()[0]
        assert text.count('; pixels\n')==count and text.count('; flags\n')==count
        assert '\t; header\n'not in text
        rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text);assert rebuilt==original
        path=tmp_path/'rendered.s';path.write_text(text);output=tmp_path/'oracle.bin';result=subprocess.run([str(c_backend.PROJECT_ROOT/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-o',str(output),str(path)],capture_output=True,text=True,timeout=10)
        assert result.returncode==0,result.stderr
        assert output.read_bytes()==original
    finally:artifact.close()


@pytest.mark.parametrize('exception',['size','unknown','cycle'])
def test_unknown_mismatched_or_cyclic_inline_record_stays_opaque(tmp_path,exception):
    source,original,metadata,stride=fixture(tmp_path,exception=exception)
    assert not any(e.struct_name=='Header'for e in metadata.seeded_entities)
    assert metadata.seeded_entities[0].field_name=='header'
    assert metadata.seeded_entities[0].name=='nested_records'
    assert metadata.seeded_entities[0].end-metadata.seeded_entities[0].addr== (4 if exception=='cycle'else 8 if exception=='size'else 6)
