"""Explicit fields grow past the old limit; invalid batches still fail atomically."""
import json
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata
from amiga_reversing.disasm.manual_actions import append_manual_actions,ManualActionKind as Kind


def fixture(tmp_path):
    binary=tmp_path/'source.bin';binary.write_bytes(bytes.fromhex('4e75'))
    return RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0,entrypoint=0,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')


@pytest.mark.c_backend
@pytest.mark.parametrize('count',[128,129,256,257,300])
def test_native_rsset_capacity_preserves_every_region(tmp_path,count):
    source=fixture(tmp_path)
    regions=[dict(offset=i*2,size=1,symbol=f'state_{i}',layout_name='app',storage_kind='scalar')for i in range(count)]
    path=tmp_path/'metadata.json';path.write_text(json.dumps(dict(rsset_layout_regions=regions)))
    policy=c_backend.effective_policy_project_source_with_c_backend(source,metadata_path=path)['analysis_policy']
    assert policy['rsset_layout_region_count']==count
    assert len(policy['rsset_layout_regions'])==count
    assert [r['symbol']for r in policy['rsset_layout_regions']]==[r['symbol']for r in regions]


@pytest.mark.c_backend
def test_invalid_rsset_tail_refuses_entire_grown_manual_batch(tmp_path):
    source=fixture(tmp_path);write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[(Kind.CREATE_MANUAL_RSSET_LAYOUT_REGION,{'rsset_layout_region':dict(
        rsset_layout_region_id=f'slot-{i}',offset=2*i,size=1,symbol=f'slot_{i}',layout_name='app',storage_kind='scalar')})for i in range(300)]
    # Native signed app displacement validation must still reject an invalid
    # tail after a valid prefix larger than the former fixed storage.
    actions.append((Kind.CREATE_MANUAL_RSSET_LAYOUT_REGION,{'rsset_layout_region':dict(
        rsset_layout_region_id='bad-tail',offset=0x8000,size=1,symbol='invalid_displacement',
        layout_name='app',storage_kind='scalar')}))
    before=(tmp_path/'target_metadata.json').read_bytes()
    with pytest.raises(ValueError,match='unprojectable RSSET layout region'):
        append_manual_actions(tmp_path,binary_source=source,actions=actions)
    assert not(tmp_path/'manual_actions.jsonl').exists()
    assert not(tmp_path/'decision_journal.jsonl').exists()
    assert(tmp_path/'target_metadata.json').read_bytes()==before


@pytest.mark.c_backend
@pytest.mark.parametrize('count',[129,256,300])
def test_manual_rsset_batch_commits_all_admitted_fields(tmp_path,count):
    from amiga_reversing.disasm.manual_actions import load_manual_projection
    source=fixture(tmp_path);write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[(Kind.CREATE_MANUAL_RSSET_LAYOUT_REGION,{'rsset_layout_region':dict(
        rsset_layout_region_id=f'slot-{i}',offset=2*i,size=1,symbol=f'slot_{i}',layout_name='app',storage_kind='scalar')})for i in range(count)]
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    fields=load_manual_projection(tmp_path).rsset_layout_regions
    assert len(fields)==count
    assert {f['symbol']for f in fields}=={f'slot_{i}'for i in range(count)}
