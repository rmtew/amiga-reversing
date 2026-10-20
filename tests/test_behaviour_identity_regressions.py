"""Candidate/backend identity regressions from read-only review; no guest edits."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import behaviour_validation as bv
from amiga_reversing.disasm import restoration_verification as rv
from amiga_reversing.disasm.derived_artifact import validate_manifest,verify_native_binding
from amiga_reversing.tools import pandora_volume_local_compare as volume
from tests.test_behaviour_validation import DATA,ROOT
from tests.test_behaviour_receipts import service

TARGET='amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'


def test_candidate_helper_bytes_are_executed_not_replaced_by_donor():
    _,projection,regs=volume.load_context(ROOT/'runtime/observations/pandora-volume-local-context.json',DATA)
    run=volume.load_engine(ROOT/'src/build/libamiga_backend.so')
    changed=bytearray(DATA)
    evidence=json.loads((ROOT/'runtime/observations/pandora-audio-volume-relocation.json').read_text())
    for r in evidence['rewrite_ledger']:
        a=r['source_offset'];changed[a:a+len(bytes.fromhex(r['after']))]=bytes.fromhex(r['after'])
    # SF.B -> ST.B at the same EA and width. Both encodings already occur in
    # the original initializer/reset pair; the generated decoder executes them.
    assert DATA[0x4d876:0x4d878]==bytes.fromhex('51eb')
    changed[0x4d876]=0x50
    original=volume.execute(run,DATA,projection,regs,relocated=False,dead=True,armed=True,volume=64)
    mutant=volume.execute(run,bytes(changed),projection,regs,relocated=True,dead=True,armed=True,volume=64)
    result=bv.compare_ordered(original['events'],mutant['events'])
    assert result['status']=='mismatch'
    assert result['expected']['pc']==result['actual']['pc']==0x5d876
    assert result['expected']['value']==0 and result['actual']['value']==255


def manifest_fixture(tmp_path):
    evidence=json.loads((ROOT/'runtime/observations/pandora-audio-volume-relocation.json').read_text())
    derived=bytearray(DATA)
    for r in evidence['rewrite_ledger']:
        a=r['source_offset'];derived[a:a+len(bytes.fromhex(r['after']))]=bytes.fromhex(r['after'])
    (tmp_path/'payload.bin').write_bytes(derived)
    region=dict(region_id='audio_master_volume',name='audio_master_volume',runtime_address=volume.OLD,
        size=2,alignment=2,source_domain='mapped_source',memory_class='cpu_ram',lifetime='persistent',dma_access='none')
    plan=dict(status='ready',rewrite_ledger=evidence['rewrite_ledger'],initialization=evidence['initialization'])
    manifest=dict(schema_version=1,kind='fixed_width_memory_relocation',target_id=TARGET,
        original_sha256=volume.sha(DATA),artifact_sha256=volume.sha(derived),artifact_file='payload.bin',
        analysis_subject_revision='a'*64,region=region,placement=dict(runtime_address=volume.NEW,memory_class='chip',reservation='exec_allocabs'),
        rewrite_ledger=evidence['rewrite_ledger'],native_plan_sha256=bv.digest(plan),initialization=evidence['initialization'])
    path=tmp_path/'manifest.json';path.write_text(json.dumps(manifest))
    artifact=SimpleNamespace(memory_regions_payload=lambda:dict(items=[region]),memory_region_plan=lambda *args:plan)
    return path,manifest,artifact


def test_bad_native_plan_hash_is_refused_even_with_identical_payload(tmp_path,monkeypatch):
    path,manifest,artifact=manifest_fixture(tmp_path)
    verify_native_binding(manifest,artifact)
    manifest['native_plan_sha256']='0'*64;path.write_text(json.dumps(manifest))
    validate_manifest(path,TARGET)  # Syntax/byte validity alone is insufficient.
    with pytest.raises(ValueError,match='native relocation proof'):
        volume.compare(TARGET,ROOT/'runtime/observations/pandora-volume-local-context.json',path,ROOT/'src/build/libamiga_backend.so',artifact=artifact)


def test_backend_replacement_after_compare_cannot_name_unexecuted_bytes(service,tmp_path,monkeypatch):
    _,result,request=service
    library=tmp_path/'src/build/libamiga_backend.so';executed=hashlib.sha256(library.read_bytes()).hexdigest()
    result['backend_sha256']=executed
    def compare(*args,**kwargs):
        library.write_bytes(b'backend B never executed')
        return result
    monkeypatch.setattr(volume,'compare',compare)
    r=rv.run_behaviour('target','revision',request)
    assert r['status']=='stale'


def test_ledger_listed_trap_is_refused_by_native_binding_and_not_hidden_in_execution(tmp_path):
    path,manifest,artifact=manifest_fixture(tmp_path)
    payload=path.parent/'payload.bin';changed=bytearray(payload.read_bytes())
    before=bytes(changed[0x4d872:0x4d874]);changed[0x4d872:0x4d874]=bytes.fromhex('4e40')
    payload.write_bytes(changed)
    manifest['artifact_sha256']=volume.sha(changed)
    manifest['rewrite_ledger']=sorted(manifest['rewrite_ledger']+[
        dict(section_index=0,source_offset=0x4d872,before=before.hex(),after='4e40',operand_index=0,region_offset=0)],key=lambda r:r['source_offset'])
    path.write_text(json.dumps(manifest))
    validate_manifest(path,TARGET)
    with pytest.raises(ValueError,match='native relocation proof'):
        volume.compare(TARGET,ROOT/'runtime/observations/pandora-volume-local-context.json',path,
                       ROOT/'src/build/libamiga_backend.so',artifact=artifact)
    _,projection,regs=volume.load_context(ROOT/'runtime/observations/pandora-volume-local-context.json',DATA)
    run=volume.load_engine(ROOT/'src/build/libamiga_backend.so')
    with pytest.raises(bv.BehaviourError) as exc:
        volume.execute(run,bytes(changed),projection,regs,relocated=True,dead=True,armed=True,volume=64)
    assert exc.value.result['status']=='unsupported' and exc.value.result['pc']==0x5d872


@pytest.mark.parametrize('module',[bv,volume,rv])
def test_cached_checker_changed_on_disk_requires_restart_on_second_request(service,tmp_path,monkeypatch,module):
    _,_,request=service
    source=tmp_path/'imported_checker.py';source.write_text('implementation A')
    loaded=bv.LoadedSource(source)
    monkeypatch.setattr(module,'LOADED_SOURCE',loaded)
    # The modeled runner identity follows the loaded implementation, not disk.
    if module is volume:service[1]['implementation_sha256']=loaded.sha256
    assert rv.run_behaviour('target','revision',request)['status']=='pass'
    source.write_text('implementation B, not imported')
    result=rv.run_behaviour('target','revision',request)
    assert result['status']=='stale'
    assert 'restart' in result['outcome']['reason']


def test_native_plan_and_manifest_are_part_of_receipt_profile(service):
    _,result,request=service
    first=rv.run_behaviour('target','revision',request)
    request['previous_receipt_id']=first['receipt_id']
    result['native_plan_sha256']=bv.digest('another plan')
    second=rv.run_behaviour('target','revision',request)
    assert second['status']=='stale' and second['admission']['identity']=='profile'
    result['native_plan_sha256']=bv.digest('native plan')
    result['manifest_sha256']=bv.digest('another manifest')
    third=rv.run_behaviour('target','revision',request)
    assert third['status']=='stale' and third['admission']['identity']=='profile'
