"""Attached canonical numeric arrays keep their unit and bytes in source export."""
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from amiga_reversing.disasm.effective_metadata import effective_metadata_file


@pytest.mark.parametrize('unit,stride', [('byte',1),('word',2),('long',4)])
def test_attached_scalar_array_renders_its_declared_unit_exactly(tmp_path, unit, stride):
    original = b'\x4e\x75' + bytes(stride*8)
    path = tmp_path/'input.bin'
    path.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x1000,
        entrypoint=0x1000,code_start_offset=0,display_path=str(path),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    commands = [('target.data_block.layout.create', dict(layout_id='numeric-values',hunk=0,
        source_start=2,source_end=len(original),name='stored_values',default_unit=unit)),
        ('target.data_block.element.set',dict(layout_id='numeric-values',offset=0,
        width=stride*8,kind='array',name='stored_values',array_count=8,array_stride=stride))]
    actions = []
    for command, params in commands:
        kind,payload = target_catalog_manual_payload(command,params)
        actions.append((ManualActionKind(kind),payload))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path) as md:
        a=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=md)[2]
    try:
        text=a.inline_source_text_with_profile()[0]
        assert 'stored_values:' in text
        tail=text.split('stored_values:',1)[1]
        assert 'dc.' + unit[0] in tail or 'dcb.' + unit[0] in tail
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',text)[0] == original
        accepted=[r for r in a.analysis_payload()[0]['sections'][0]['range_ownerships']
                  if r['status_name']=='accepted' and r['start_offset']==2 and r['end_offset']==len(original)]
        assert accepted
    finally:
        a.close()
