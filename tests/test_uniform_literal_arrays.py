"""Compact typed literal leaves without discarding source identities or meaning."""
import subprocess

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file, effective_target_metadata
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind as Kind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def render(tmp_path, width=2, value=0, count=16, exception=None):
    units = [value.to_bytes(width, 'big')] * count
    if exception == 'mixed':
        units[count // 2] = (value ^ 1).to_bytes(width, 'big')
    original = bytes.fromhex('4e75') + b''.join(units)
    binary = tmp_path / 'input.bin';binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    actions = []
    def add(command, parameters):
        kind, payload = target_catalog_manual_payload(command, parameters)
        actions.append((Kind(kind), payload));return payload
    def owner(start, end, name):
        p = add('target.data_block.layout.create',dict(hunk=0,source_start=start,source_end=end,name=name,role='data',default_unit={1:'byte',2:'word',4:'long'}[width]))
        lid = p['data_block_layout']['layout_id']
        add('target.data_block.element.set',dict(layout_id=lid,offset=0,width=end-start,kind='array',array_count=(end-start)//width,array_stride=width,name=name,representation='hex'))
        return lid
    if exception == 'owners':
        owner(2,2+count*width//2,'first_fill');owner(2+count*width//2,len(original),'second_fill')
    else:
        lid = owner(2,len(original),'typed_fill')
    if exception in ('label','odd_label'):
        offset = 2+count*width//2 if exception=='label' else 7
        actions.append((Kind.CREATE_MANUAL_LABEL,{'label':dict(label_id='anchor',name='interior_anchor',scope='global',address_domain='source',hunk=0,addr=offset)}))
    if exception in ('comment','authored_data'):
        for offset, text in [(2,'data' if exception=='authored_data' else 'Original fill owner.'),(2+count*width//2,'Second half has a separate use.')]:
            actions.append((Kind.CREATE_MANUAL_COMMENT,{'comment':dict(comment_id=str(offset),hunk=0,addr=offset,text=text)}))
    if exception == 'symbol':
        add('target.custom_struct.add',dict(name='Unit',size=width,fields=[dict(name='value',type='WORD',offset=0,size=width)]))
        add('target.data_block.element.set',dict(layout_id=lid,offset=0,width=count*width,kind='struct',binding_kind='custom_struct',type_id='Unit',name='typed_fill',array_count=count,array_stride=width))
        add('target.equate.add',dict(name='AUTHORED_FILL_VALUE',value=value))
        actions.append((Kind.CREATE_MANUAL_REPRESENTATION,{'representation':dict(representation_id='selected',hunk=0,addr=2+count*width//2,end=2+count*width//2+width,element_kind='data_literal',style='symbol',value=value,width_bytes=width,symbol='AUTHORED_FILL_VALUE')}))
    if exception == 'references':
        for i in range(count):
            add('target.data_block.element.interpret_ref',dict(layout_id=lid,offset=i*width,width=width,reference_kind='absolute',target_hunk=0,target_offset=value,source_value=value))
    if exception == 'field':
        # A member literally named 'data' is meaningful and must keep its comment.
        actions.pop()
        add('target.custom_struct.add',dict(name='Buffer',size=count*width,fields=[dict(name='data',type='WORD',offset=0,size=count*width)]))
        add('target.data_block.element.set',dict(layout_id=lid,offset=0,width=count*width,kind='struct',binding_kind='custom_struct',type_id='Buffer',name='typed_fill'))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path) as metadata:
        artifact=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    try:
        text=artifact.source_text_with_profile()[0]
        rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text)
        assert rebuilt==original
        path=tmp_path/'rendered.s';path.write_text(text);output=tmp_path/'oracle.bin'
        result=subprocess.run([str(c_backend.PROJECT_ROOT/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-o',str(output),str(path)],capture_output=True,text=True,timeout=10)
        assert result.returncode==0,result.stderr
        assert output.read_bytes()==original
        return text,effective_target_metadata(tmp_path)
    finally:artifact.close()


@pytest.mark.parametrize('width,value,count',[(1,0,16),(1,0xA5,16),(2,0,256),(2,0x1234,16),(4,0,16),(4,0x12345678,16)])
def test_uniform_numeric_units_keep_width_and_typed_metadata(tmp_path,width,value,count):
    text,metadata=render(tmp_path,width,value,count)
    suffix={1:'b',2:'w',4:'l'}[width]
    assert f'dcb.{suffix} ${count:X},${value:0{width*2}X}\n' in text
    assert '; data' not in text
    element=metadata.data_block_layouts[0].elements[0]
    assert (element.array_count,element.array_stride,element.width)==(count,width,count*width)


@pytest.mark.parametrize('exception',['mixed','label','odd_label','comment','authored_data','owners','symbol','references','field'])
def test_compaction_respects_boundaries_and_semantics(tmp_path,exception):
    width,value=(4,2) if exception=='references' else (2,0)
    text,_=render(tmp_path,width,value,exception=exception)
    if exception in ['label','odd_label']:assert 'interior_anchor:\n' in text
    if exception in ['comment','authored_data']:
        assert 'Second half has a separate use.' in text
        assert ('; data\n' if exception=='authored_data' else '; Original fill owner.\n') in text
    if exception=='owners':
        assert text.count('dcb.w $8,$0000')==2
        assert 'first_fill:'in text and 'second_fill:'in text
    if exception=='symbol':assert 'dc.w AUTHORED_FILL_VALUE' in text
    if exception=='references':
        assert text.count('dc.l dblk_ref_h0_00000002')==15
        assert 'dc.l $00000002' in text
        assert 'dcb.l'not in text
    if exception=='field':assert 'dcb.b $20,$00\t; data' in text
    if exception=='mixed':assert 'dcb.w'not in text
    if exception in ['label','odd_label','comment','authored_data','owners','symbol']:assert 'dcb.w $10'not in text
