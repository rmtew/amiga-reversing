"""Typed media keeps its analysis while using the normal binary-asset package."""
import json

import pytest

from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.c_backend import listing_artifact_source_package_with_c_backend
from amiga_reversing.disasm.effective_metadata import effective_metadata_file, effective_metadata_text
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata

pytestmark = pytest.mark.c_backend


def typed_media(tmp_path, role, interior_label=False):
    target=tmp_path/'target';target.mkdir()
    path=tmp_path/'original.bin';path.write_bytes(bytes.fromhex('4e75')+bytes(range(128))*2)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=path,address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,entrypoint=0,code_start_offset=0,display_path=str(path),analysis_cache_path=tmp_path/'cache')
    write_target_metadata(target,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[target_catalog_manual_payload('target.custom_struct.add',dict(name='PlanarRow',size=8,
        fields=[dict(name=f'plane_{i}',type='UWORD',offset=2*i,size=2) for i in range(4)]))]
    for index in range(2):
        owner=target_catalog_manual_payload('target.data_block.layout.create',dict(hunk=0,source_start=2+128*index,
            source_end=130+128*index,name=f'cell_{index}',role=role,default_unit='word'))
        actions.append(owner)
        actions.append(target_catalog_manual_payload('target.data_block.element.set',dict(
            layout_id=owner[1]['data_block_layout']['layout_id'],offset=0,width=128,kind='array',
            array_count=16,array_stride=8,binding_kind='custom_struct',type_id='PlanarRow')))
    if interior_label:actions.append(target_catalog_manual_payload('target.code_label.add',dict(hunk=0,addr=4,name='interior_anchor')))
    append_manual_actions(target,actions=[(ManualActionKind(kind),payload) for kind,payload in actions],binary_source=source)
    return target,source


@pytest.mark.parametrize('role',['bitmap','sound_sample','opaque_data'])
def test_typed_media_exports_two_bounded_assets_without_field_comment_bulk(tmp_path,role):
    target,source=typed_media(tmp_path,role)
    metadata=json.loads(effective_metadata_text(target));leaves=[v for v in metadata['seeded_entities'] if v.get('struct_name')=='PlanarRow']
    assert len(leaves)==128 and {v['subtype'] for v in leaves}=={role}
    assert {v['field_name'] for v in leaves}=={f'plane_{i}' for i in range(4)}
    with effective_metadata_file(target) as path:
        package=listing_artifact_source_package_with_c_backend(source,minimum_asset_size=128,metadata_path=path)
    assets=package['assets'];assert len(assets)==2
    assert [(v['source_offset'],v['size']) for v in assets]==[(2,128),(130,128)]
    assert all(bytes.fromhex(v['data_hex'])==bytes(range(128)) for v in assets)
    assert package['source_text'].count('INCBIN')==2
    assert '; plane_' not in package['source_text']
    assert '; plane_0' in package['canonical_source_text']
    assert 'cell_0:' in package['source_text'] and 'cell_1:' in package['source_text']


def test_typed_media_keeps_interior_source_label_boundary(tmp_path):
    target,source=typed_media(tmp_path,'bitmap',interior_label=True)
    with effective_metadata_file(target) as path:
        package=listing_artifact_source_package_with_c_backend(source,minimum_asset_size=128,metadata_path=path)
    assert len(package['assets'])==1 and package['assets'][0]['source_offset']==130
    assert 'interior_anchor:' in package['source_text'] and '; plane_' in package['source_text']


def test_descriptive_role_is_not_promoted_to_media_or_native_subtype(tmp_path):
    target,source=typed_media(tmp_path,'descriptive role '*20)
    assert all(v.get('subtype') is None for v in json.loads(effective_metadata_text(target))['seeded_entities']
               if v.get('struct_name')=='PlanarRow')
