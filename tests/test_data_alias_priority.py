"""Authored data aliases survive generated field labels at the same address."""
import json
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource


@pytest.mark.parametrize('authored,reverse,root_alias', [
    (False,False,False),(True,False,False),(True,True,False),(True,False,True)])
def test_authored_alias_is_not_suppressed_as_an_expanded_field(tmp_path,authored,reverse,root_alias):
    assembly=' SECTION code,code\n ORG $1000\n lea.l record.l,a0\n move.w 2(a0),d0\n rts\nrecord:dc.w 1,2,3,4\n'
    original,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',assembly)
    start=len(original)-8
    entities=[dict(addr=start,end=start+2,hunk=0,name='record',type='data',unit='word',
                   struct_name='Record',field_name='head',field_type='WORD'),
              dict(addr=start+2,end=start+4,hunk=0,name='record_middle',type='data',unit='word',
                   struct_name='Record',field_name='middle',field_type='WORD'),
              dict(addr=start+4,end=start+8,hunk=0,name='record_tail',type='data',unit='long',
                   struct_name='Record',field_name='tail',field_type='LONG')]
    if root_alias:
        entities[0].update(source_owner_start=start,source_owner_size=8)
    if authored:entities.append(dict(addr=start if root_alias else start+2,end=start+8,hunk=0,
                                    name='older_record_name'if root_alias else'authored_suffix',
                                    type='data',unit='byte'))
    if reverse:entities.reverse()
    metadata=dict(target_type='program',custom_structs=[dict(name='Record',size=8,fields=[
        dict(name='head',type='WORD',offset=0,size=2),dict(name='middle',type='WORD',offset=2,size=2),
        dict(name='tail',type='LONG',offset=4,size=4)])],seeded_entities=entities)
    binary=tmp_path/'input.bin';binary.write_bytes(original)
    path=tmp_path/'metadata.json';path.write_text(json.dumps(metadata))
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x1000,entrypoint=0x1000,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    a=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=path)[2]
    try:
        rendered=a.inline_source_text_with_profile()[0]
        assert ('authored_suffix:\n'in rendered)==(authored and not root_alias)
        if root_alias:assert 'record:\n'in rendered and 'older_record_name:\n'not in rendered
        assert 'record_middle:\n'not in rendered and 'record_tail:\n'not in rendered
        assert 'Record_middle(a0)'in rendered
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',rendered)[0]==original
        assert not a.analysis_payload()[0]['incomplete_analysis']
    finally:a.close()
