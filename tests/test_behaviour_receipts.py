import json
from pathlib import Path

import pytest

from amiga_reversing.disasm import behaviour_validation as bv
from amiga_reversing.disasm import restoration_verification as rv
from amiga_reversing.tools import pandora_volume_local_compare as volume


@pytest.fixture
def service(tmp_path,monkeypatch):
    monkeypatch.setattr(rv,'PROJECT_ROOT',tmp_path)
    for name in ('src/build/libamiga_backend.so','amiga_reversing/disasm/behaviour_validation.py'):
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'test implementation')
    contract=dict(contract=dict(execution_kind='pandora_volume_cpu',contract_id='pandora.volume.local.v1',
                  entry_source=volume.ENTRY-volume.BASE,return_pc=volume.RETURN,instruction_budget=128,
                  original_volume=volume.OLD,derived_volume=volume.NEW,
                  control_source_ranges=[[0x552de,0x55370],[0x4d872,0x4d8f2]]),contract_sha256=bv.digest('contract'),
                  function_summary_id='canonical-summary',action_id='canonical-action',review_status='accepted')
    monkeypatch.setattr(bv,'canonical_contract',lambda *args:dict(contract))
    result=dict(original_sha256=bv.digest('original'),derived_sha256=bv.digest('derived'),
                backend_sha256=rv._hash((tmp_path/'src/build/libamiga_backend.so').read_bytes()),
                implementation_sha256=volume.LOADED_SOURCE.sha256,
                manifest_sha256=bv.digest('manifest'),native_plan_sha256=bv.digest('native plan'),
                binding_checker_sha256=bv.digest('native binding checker'),
                context_sha256=bv.digest('fixture'),routine_comparison=dict(refused_cases=[]),
                accepted_cases=[dict(fixture_ids=[bv.digest('a'),bv.digest('b')])])
    def compare(*args,**kwargs):
        result['manifest_sha256']=rv._hash(args[2].read_bytes())
        return result
    monkeypatch.setattr(volume,'compare',compare)
    request=dict(contract_id='bounded-test',manifest='.runtime-state/restoration/derived/fixture/manifest.json')
    manifest=tmp_path/request['manifest'];manifest.parent.mkdir(parents=True,exist_ok=True)
    manifest.write_text(json.dumps(dict(analysis_subject_revision='revision')))
    result['manifest_sha256']=rv._hash(manifest.read_bytes())
    return contract,result,request


def test_receipt_is_content_addressed_and_cannot_substitute_for_exact_build(service,tmp_path):
    _,_,request=service;r=rv.run_behaviour('target','revision',request)
    assert r['status']=='pass' and r['kind']=='behaviour_verification'
    assert rv.load_receipt('target',r['receipt_id'])==r
    with pytest.raises(ValueError,match='exact rebuilt'):
        rv._verified_receipt('target','revision',r)
    file=rv._directory('target')/(r['receipt_id']+'.json');file.write_text('{}')
    with pytest.raises(ValueError,match='integrity'):rv.load_receipt('target',r['receipt_id'])


def test_predicate_pass_without_canonical_review_is_missing_prerequisite(service):
    contract,_,request=service;contract['review_status']='unassessed'
    r=rv.run_behaviour('target','revision',request)
    assert r['evaluation_outcome']['status']=='pass'
    assert r['status']=='missing_prerequisite'


def test_prior_receipt_stales_when_profile_or_fixture_changes(service,tmp_path):
    _,result,request=service;r=rv.run_behaviour('target','revision',request)
    request['previous_receipt_id']=r['receipt_id']
    manifest=tmp_path/request['manifest'];manifest.write_text(json.dumps(dict(analysis_subject_revision='other-revision')))
    new=rv.run_behaviour('target','other-revision',request)
    assert new['status']=='stale' and new['admission']['identity']=='profile'
    manifest.write_text(json.dumps(dict(analysis_subject_revision='revision')))
    result['context_sha256']=bv.digest('new fixture')
    new=rv.run_behaviour('target','revision',request)
    assert new['status']=='stale' and new['admission']['identity']=='fixture'


def test_stale_manifest_is_not_admitted_as_a_new_result(service,tmp_path):
    _,_,request=service
    (tmp_path/request['manifest']).write_text(json.dumps(dict(analysis_subject_revision='old')))
    r=rv.run_behaviour('target','revision',request)
    assert r['status']=='stale' and r['outcome']['reason']=='Derived manifest belongs to another analysis subject'


@pytest.mark.parametrize('status',[
    'mismatch','missing_prerequisite','timeout_not_observed_within_bounds',
    'unsupported','incomplete_truncated','stale',
])
def test_no_nonpass_case_is_promoted_by_other_successful_cases(service,status):
    _,result,request=service
    result['routine_comparison']['refused_cases']=[dict(status='refused',outcome=dict(status=status,reason='test'))]
    r=rv.run_behaviour('target','revision',request)
    assert r['status']==status


def test_owned_manifest_path_and_missing_contract_fail_closed(service,monkeypatch):
    _,_,request=service;request['manifest']='../../outside.json'
    assert rv.run_behaviour('target','revision',request)['status']=='unsupported'
    def absent(*args):raise bv.BehaviourError('missing_prerequisite','Contract absent')
    monkeypatch.setattr(bv,'canonical_contract',absent)
    assert rv.run_behaviour('target','revision',request)['status']=='missing_prerequisite'


def test_deviation_needs_explicit_reviewed_authority_and_is_never_equivalence(service):
    contract,result,request=service
    result['routine_comparison']['refused_cases']=[dict(status='deviation',outcome=dict(
        status='accepted_deviation',deviation_id='reviewed-example'))]
    assert rv.run_behaviour('target','revision',request)['status']=='missing_prerequisite'
    contract['contract']['accepted_deviations']=[dict(id='reviewed-example',reason='Explicit bounded test deviation')]
    assert rv.run_behaviour('target','revision',request)['status']=='accepted_deviation'
    contract['review_status']='unassessed'
    assert rv.run_behaviour('target','revision',request)['status']=='missing_prerequisite'


def test_unknown_runner_outcome_cannot_pass(service):
    _,result,request=service
    result['routine_comparison']['refused_cases']=[dict(status='bad',outcome=dict(status='skipped'))]
    assert rv.run_behaviour('target','revision',request)['status']=='unsupported'
