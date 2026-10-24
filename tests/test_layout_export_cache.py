"""Cache ownership, warm placement edits, stale inputs and loaded identities."""
import copy
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import layout_export_cache as cache,c_backend
from amiga_reversing.disasm.behaviour_validation import LoadedSource
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from tests.test_bootstrap_layouts import build,ORIGINAL
from tests.test_layout_projection import model


@pytest.fixture
def setup(tmp_path,monkeypatch):
    cache._CACHE.reset()
    current=dict(metadata=model(),data=ORIGINAL)
    path=tmp_path/'layout.json';owner_file=tmp_path/'owner.py';owner_file.write_text('VERSION=1\n')
    paths=SimpleNamespace(target_dir=tmp_path,binary_source='flat-fixture')
    def full():
        value=copy.deepcopy(current['metadata']);value.pop('selected_memory_layout_id',None)
        return hashlib.sha256((json.dumps(value,sort_keys=True,indent=2)+'\n').encode()).hexdigest()
    def snapshot():path.write_text(json.dumps(current['metadata']))
    monkeypatch.setattr(cache.effective_metadata,'effective_metadata_hash',lambda _:full())
    monkeypatch.setattr(cache,'read_binary_source_bytes',lambda _:current['data'])
    artifacts=[]
    def builder():
        result=build(tmp_path,current['metadata'],current['data']);artifacts.append(result);return result
    owner_source=LoadedSource(owner_file)
    def acquire(**options):return cache.acquire(paths,PROJECT_ROOT,path,builder,owner_source,256,**options)
    snapshot()
    yield current,snapshot,acquire,artifacts,path,owner_file
    cache._CACHE.reset()


def test_placement_edit_reuses_semantics_but_core_edit_evicts_owned_artifact(setup):
    current,snapshot,acquire,artifacts,_,_=setup
    with acquire() as artifact:before=artifact.inline_source_text_with_profile()[0]
    assert len(artifacts)==1 and artifacts[0]._handle.value
    current['metadata']['memory_layouts'][0]['placements'].append(dict(region_id='workspace',runtime_address=0xe0000));snapshot()
    with acquire() as projection:
        text,profile=projection.inline_source_text_with_profile()
        assert text!=before and profile['layout_projection']['semantic_analysis_runs']==0
        assert projection.source_package_payload(256)['source_text']==text
    assert len(artifacts)==1
    current['metadata']['target_equates'][0]['value']+=2;snapshot()
    with acquire() as artifact:assert artifact.inline_source_text_with_profile()[0]!=text
    assert len(artifacts)==2 and not artifacts[0]._handle.value


def test_changed_image_requires_exactly_one_cold_rebuild(setup):
    current,snapshot,acquire,artifacts,_,_=setup
    with acquire():pass
    current['metadata']['memory_layouts'][0]['placements'][0]['runtime_address']=0x90000;snapshot()
    with acquire():pass
    assert len(artifacts)==2 and not artifacts[0]._handle.value
    with acquire() as projection:assert projection.profile['layout_projection']['semantic_analysis_runs']==0
    assert len(artifacts)==2


def test_invalid_placement_refuses_without_a_rebuild_or_silent_skip(setup):
    current,snapshot,acquire,artifacts,_,_=setup
    with acquire():pass
    current['metadata']['memory_layouts'][0]['placements'].append(dict(region_id='workspace',runtime_address=0x80000));snapshot()
    with pytest.raises(cache.LayoutExportRefused,match='unrelated_region_overlap'):
        with acquire():pass
    assert len(artifacts)==1
    current['metadata']['memory_layouts'][0]['placements'][-1]['runtime_address']=0xe0000;snapshot()
    with acquire() as projection:assert projection.profile['layout_projection']['semantic_analysis_runs']==0
    assert len(artifacts)==1


def test_two_readers_share_one_owned_build_and_serialized_projection(setup):
    from concurrent.futures import ThreadPoolExecutor
    _,_,acquire,artifacts,_,_=setup
    def request(_):
        with acquire() as artifact:return artifact.inline_source_text_with_profile()[0]
    with ThreadPoolExecutor(max_workers=2) as pool:outputs=list(pool.map(request,range(2)))
    assert outputs[0]==outputs[1] and len(artifacts)==1


def test_unreviewed_metadata_swap_before_admission_refuses_before_build(setup):
    current,_,acquire,artifacts,_,_=setup
    current['metadata']['target_equates'][0]['value']+=2
    with pytest.raises(cache.LayoutExportRefused,match='metadata changed'):
        with acquire():pass
    assert not artifacts


def test_loaded_owner_edit_requires_restart_and_closes_cached_native_owner(setup):
    _,_,acquire,artifacts,_,owner_file=setup
    with acquire():pass
    owner_file.write_text('VERSION=2\n')
    with pytest.raises(cache.LayoutExportRefused,match='restart') as error:
        with acquire():pass
    assert error.value.payload['restart_required'] and not artifacts[0]._handle.value


def test_input_change_never_reuses_previously_valid_contract(setup):
    current,_,acquire,artifacts,_,_=setup
    with acquire():pass
    current['data']=bytes(len(ORIGINAL))
    with pytest.raises(RuntimeError,match='bootstrap_input_identity_mismatch'):
        with acquire():pass
    assert len(artifacts)==1 and not artifacts[0]._handle.value


def test_native_load_identity_cannot_be_relabelled_after_file_replacement(tmp_path,monkeypatch):
    compiler=shutil.which('cc')
    if compiler is None or os.name=='nt':pytest.skip('Atomic loaded-library replacement regression requires cc and POSIX')
    monkeypatch.delenv('AMIGA_C_BACKEND_DLL_ROOT',raising=False)
    folder=tmp_path/'src/build';folder.mkdir(parents=True)
    a=folder/'probe.dll';b=folder/'replacement.dll';source=tmp_path/'probe.c'
    for path,value in [(a,1),(b,2)]:
        source.write_text(f'int probe(void) {{ return {value}; }}\n')
        subprocess.run([compiler,'-shared','-fPIC','-o',str(path),str(source)],check=True,capture_output=True)
    loaded=c_backend._load_dll(tmp_path,'probe.dll')
    assert loaded.probe()==1
    identity=c_backend._require_loaded_native_identity(loaded)
    b.replace(a)
    assert loaded.probe()==1
    with pytest.raises(c_backend.NativeBackendStale):c_backend._require_loaded_native_identity(loaded)
    with pytest.raises(c_backend.NativeBackendStale):c_backend._load_dll(tmp_path,'probe.dll')
    assert identity['sha256']!=hashlib.sha256(a.read_bytes()).hexdigest()


def test_shared_export_warm_package_equals_a_clean_export(tmp_path,monkeypatch):
    from contextlib import contextmanager
    from amiga_reversing.disasm import source_export,source_rendering
    from amiga_reversing.disasm.binary_source import RawBinarySource,RawAddressModel,BinarySourceKind
    cache._CACHE.reset();m=model();binary=tmp_path/'binary.bin';binary.write_bytes(ORIGINAL)
    source=RawBinarySource(BinarySourceKind.RAW_BINARY,binary,RawAddressModel.RUNTIME_ABSOLUTE,
        0x10000,0x10000,0,'fixture',tmp_path/'analysis.json')
    paths=SimpleNamespace(target_dir=tmp_path,binary_source=source)
    def metadata_hash(_):
        raw=dict(m);raw.pop('selected_memory_layout_id',None)
        return hashlib.sha256((json.dumps(raw,sort_keys=True,indent=2)+'\n').encode()).hexdigest()
    @contextmanager
    def metadata_file(*args,layout_id=None,**kwargs):
        payload=dict(m);payload['selected_memory_layout_id']=layout_id
        path=tmp_path/'consumed-metadata.json';path.write_text(json.dumps(payload));yield path
    monkeypatch.setattr(source_export,'effective_metadata_file',metadata_file)
    monkeypatch.setattr(source_export,'resolve_project_paths',lambda *a,**kw:paths)
    monkeypatch.setattr(cache.effective_metadata,'effective_metadata_hash',metadata_hash)
    monkeypatch.setattr(source_rendering,'effective_metadata_hash',metadata_hash)
    builds=[];original_builder=source_export.build_listing_artifact_profile_from_binary_source
    def counted(*args,**kwargs):builds.append(1);return original_builder(*args,**kwargs)
    monkeypatch.setattr(source_export,'build_listing_artifact_profile_from_binary_source',counted)
    try:
        cold=source_export.source_export_payload('fixture',project_root=PROJECT_ROOT,binary_assets=True,layout_id='diagnostic')
        assert cold['status']=='ok',cold
        m['memory_layouts'][0]['placements'].append(dict(region_id='workspace',runtime_address=0xe0000))
        warm=source_export.source_export_payload('fixture',project_root=PROJECT_ROOT,binary_assets=True,layout_id='diagnostic')
        assert warm['status']=='ok',warm
        assert len(builds)==1 and warm['listing_profile']['layout_projection']['semantic_analysis_runs']==0
        cache._CACHE.reset()
        clean=source_export.source_export_payload('fixture',project_root=PROJECT_ROOT,binary_assets=True,layout_id='diagnostic')
        assert len(builds)==2
        assert warm['source_text']==clean['source_text'] and warm['package']==clean['package']
    finally:cache._CACHE.reset()


def test_allocation_export_refreshes_only_a_valid_different_baseline(setup):
    current,snapshot,acquire,artifacts,_,_=setup
    with acquire():pass
    current['metadata']['memory_layouts'][0]['placements'].append(dict(region_id='workspace',runtime_address=0x80000));snapshot()
    with pytest.raises(cache.LayoutExportRefused,match='unrelated_region_overlap'):
        with acquire(require_native_baseline=True):pass
    assert len(artifacts)==1 and artifacts[0]._handle.value
    current['metadata']['memory_layouts'][0]['placements'][-1]['runtime_address']=0xe0000;snapshot()
    with acquire(require_native_baseline=True) as artifact:artifact.loaded_backend_identity()
    assert len(artifacts)==2 and not artifacts[0]._handle.value
    with acquire(require_native_baseline=True) as projection:
        assert projection._native is artifacts[1]
        projection.loaded_backend_identity()
    assert len(artifacts)==2
