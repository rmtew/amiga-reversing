"""Name-only canonical data entities retain labels, without inventing extents."""
import json
import pytest
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.c_backend import (
    build_listing_artifact_profile_from_binary_source,
    assemble_platform_source_text_with_c_backend,
    validate_policy_storage_with_c_backend,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT


def source(tmp_path,base=0):
    # Local-offset input needs a source-backed PC reference. A numeric absolute
    # operand that happens to equal offset8 is a distinct, ambiguous domain.
    raw=(bytes.fromhex('41f9')+(base+8).to_bytes(4,'big')+bytes.fromhex('4e75')
         if base else bytes.fromhex('41fa00064e714e75'))+bytes.fromhex('aabbccdd')
    binary=tmp_path/'input.bin';binary.write_bytes(raw)
    return raw,RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE if base else RawAddressModel.LOCAL_OFFSET,
        load_address=base,entrypoint=base,code_start_offset=0,
        display_path=str(binary),analysis_cache_path=tmp_path/'analysis')


@pytest.mark.parametrize('base',[0,0x4000])
@pytest.mark.parametrize('null_end',[False,True])
@pytest.mark.parametrize('owned',[False,True])
def test_extentless_data_name_renders_definition_and_reference_without_new_ownership(tmp_path,base,null_end,owned):
    raw,binary=source(tmp_path,base)
    owners=[dict(type='data',hunk=0,addr=8,end=12,unit='byte')]if owned else[]
    before=None;before_flow=None
    for named in[False,True]:
        entity=dict(type='data',hunk=0,addr=8,name='named_bytes')
        if null_end:entity['end']=None
        metadata=tmp_path/'metadata.json';metadata.write_text(json.dumps(dict(seeded_entities=owners+([entity]if named else[]))))
        _,_,artifact=build_listing_artifact_profile_from_binary_source(binary,
            metadata_path=metadata,project_root=PROJECT_ROOT)
        try:
            facts=artifact.analysis_payload()[0]
            # A name must not become a data classification, type or extent.
            items=facts['analysis_policy']['structured_data_items']
            flow={key:facts['sections'][0][key]for key in['blocks','edges','range_ownerships']}
            if not named:before=items;before_flow=flow;continue
            assert items==before
            assert flow==before_flow
            rendered,_=artifact.inline_source_text_with_profile()
            assert 'named_bytes:' in rendered and 'named_bytes' in next(line for line in rendered.splitlines()if '\tlea' in line)
            rebuilt,_=assemble_platform_source_text_with_c_backend('amiga-raw',rendered,project_root=PROJECT_ROOT)
            assert rebuilt==raw
        finally:artifact.close()


@pytest.mark.parametrize('end',[8,7])
def test_explicit_invalid_extent_is_not_treated_as_name_only(tmp_path,end):
    _,binary=source(tmp_path)
    metadata=tmp_path/'metadata.json';metadata.write_text(json.dumps(dict(seeded_entities=[
        dict(type='data',hunk=0,addr=8,end=end,name='invalid_extent')])) )
    _,_,artifact=build_listing_artifact_profile_from_binary_source(binary,
        metadata_path=metadata,project_root=PROJECT_ROOT)
    try:
        rendered,_=artifact.inline_source_text_with_profile()
        assert 'invalid_extent' not in rendered
    finally:artifact.close()


@pytest.mark.parametrize('owner',[
    dict(source_owner_start=8),dict(source_owner_size=4),
    dict(source_owner_start=8,source_owner_size=4)])
def test_name_without_extent_does_not_bypass_bound_owner_validation(tmp_path,owner):
    _,binary=source(tmp_path)
    metadata=dict(seeded_entities=[dict(type='data',hunk=0,addr=8,name='unbound_owner',**owner)])
    with pytest.raises(RuntimeError,match='failed parsing target metadata seeded entity'):
        validate_policy_storage_with_c_backend(binary,metadata_text=json.dumps(metadata),project_root=PROJECT_ROOT)


def test_source_name_does_not_reinterpret_numeric_absolute_operand_in_local_domain(tmp_path):
    _,binary=source(tmp_path)
    binary.path.write_bytes(bytes.fromhex('41f9000000084e75aabbccdd'))
    metadata=tmp_path/'metadata.json';metadata.write_text(json.dumps(dict(seeded_entities=[
        dict(type='data',hunk=0,addr=8,name='source_only_bytes')])))
    _,_,artifact=build_listing_artifact_profile_from_binary_source(binary,
        metadata_path=metadata,project_root=PROJECT_ROOT)
    try:
        rendered,_=artifact.inline_source_text_with_profile()
        assert 'source_only_bytes:' in rendered
        assert 'source_only_bytes' not in next(line for line in rendered.splitlines()if '\tlea' in line)
    finally:artifact.close()


@pytest.mark.parametrize('entity',[dict(type='code',addr=8),dict(type='unknown',addr=8),dict(type='data')])
def test_name_only_data_path_does_not_promote_unsupported_or_unaddressed_entities(tmp_path,entity):
    _,binary=source(tmp_path)
    metadata=tmp_path/'metadata.json';metadata.write_text(json.dumps(dict(seeded_entities=[dict(name='not_admitted',hunk=0,**entity)])))
    _,_,artifact=build_listing_artifact_profile_from_binary_source(binary,
        metadata_path=metadata,project_root=PROJECT_ROOT)
    try:
        rendered,_=artifact.inline_source_text_with_profile()
        assert 'not_admitted' not in rendered
    finally:artifact.close()
