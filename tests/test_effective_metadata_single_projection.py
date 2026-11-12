"""One fresh, conflict-checked replay supplies both metadata and wire extras."""
import json
import os

import pytest

from amiga_reversing.disasm import effective_metadata as effective
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.target_metadata import (
    SeededCodeEntrypointMetadata, TargetMetadata, TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin, write_target_metadata,
)
from tests.test_manual_seed_effective_metadata import _action, _append_jsonl


def history(tmp_path):
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=(),
        seeded_code_entrypoints=(SeededCodeEntrypointMetadata(hunk=0,addr=4,name='base_entry',
            seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
            review_status=TargetMetadataReviewStatus.VALIDATED,citation='target_metadata'),)))
    path=tmp_path/'manual_actions.jsonl'
    _append_jsonl(path,[{'record':'manual_action_log_header','version':1,'target_identity':{}},
        _action('a1',1,'create_manual_seed',seed=dict(seed_id='conflict',kind='data',
            mode='required',hunk=0,addr=0,end=8,data_role='raw',unit='byte')),
        observation('a2',2,'initial')])
    return path


def observation(identity,sequence,name):
    return _action(identity,sequence,'create_manual_runtime_observation_view',
        runtime_observation_view=dict(execution_view_id='observed',source_start=32,source_end=128,
            base_addr=0x4000,name=name))


@pytest.mark.parametrize('mode',['conflict','malformed','different_binary'])
def test_wire_extras_share_the_checked_projection_and_refusals(tmp_path,monkeypatch,mode):
    path=history(tmp_path);source=None
    if mode=='malformed':path.write_text(path.read_text()+'broken JSON\n')
    if mode=='different_binary':
        binary=tmp_path/'input.bin';binary.write_bytes(bytes(128))
        source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
            address_model=RawAddressModel.LOCAL_OFFSET,load_address=0,entrypoint=0,code_start_offset=0,
            display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    real=effective.load_manual_projection;calls=[]
    def load(*args,**kwargs):
        calls.append(kwargs)
        return real(*args,**kwargs)
    monkeypatch.setattr(effective,'load_manual_projection',load)
    payload=json.loads(effective.effective_metadata_text(tmp_path,binary_source=source))
    assert len(calls)==1 and calls[0]['stronger_metadata'] is not None
    assert payload['seeded_entities']==[]  # The required data seed cannot hide base code.
    assert payload['seeded_code_entrypoints'][0]['name']=='base_entry'
    if mode=='conflict':
        view,=payload['runtime_observation_views']
        assert view['name']=='initial'
        mapped,=payload['execution_views']
        assert mapped['runtime_view_provenance']=='observed' and mapped['runtime_view_use']=='pointer_target'
    else:
        assert 'runtime_observation_views'not in payload and payload['execution_views']==[]


def test_pending_and_same_stat_edits_are_fresh_at_each_export(tmp_path,monkeypatch):
    path=history(tmp_path);real=effective.load_manual_projection;calls=[]
    def load(*args,**kwargs):
        calls.append(kwargs)
        return real(*args,**kwargs)
    monkeypatch.setattr(effective,'load_manual_projection',load)
    pending=[observation('a3',3,'pending')]
    first=json.loads(effective.effective_metadata_text(tmp_path,pending_actions=pending))
    second=json.loads(effective.effective_metadata_text(tmp_path))
    assert first['runtime_observation_views'][0]['name']=='pending'
    assert second['runtime_observation_views'][0]['name']=='initial'
    assert calls[0]['pending_actions']==pending and not calls[1]['pending_actions']
    stamp=path.stat();path.write_text(path.read_text().replace('initial','changed'))
    os.utime(path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
    assert path.stat().st_size==stamp.st_size
    third=json.loads(effective.effective_metadata_text(tmp_path))
    assert third['runtime_observation_views'][0]['name']=='changed' and len(calls)==3
