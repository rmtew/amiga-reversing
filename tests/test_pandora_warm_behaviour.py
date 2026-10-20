"""Bounded warm-path integration, using owned private captured inputs.

Missing fixture is an explicit test skip, never a behavioural pass receipt. The
published manifest/contract hash, not these test mutations, defines real inputs.
"""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import behaviour_validation as bv
from amiga_reversing.tools import pandora_volume_local_compare as volume
from tests.test_behaviour_validation import DATA,ROOT
from tests.test_behaviour_receipts import service
from amiga_reversing.disasm import restoration_verification as rv
from tests.test_behaviour_identity_regressions import manifest_fixture,TARGET

REAL_COMPARE=volume.compare

CAPTURE=ROOT/'.runtime-state/pandora-behaviour/warm-audio-start-inputs/capture.json'


@pytest.fixture
def warm_context():
    if not CAPTURE.exists():
        pytest.skip('Private identity-bound warm fixture absent; no CPU warm evidence evaluated')
    _,memory,regs=volume.load_context(CAPTURE,DATA,warm_start=True)
    return volume.load_engine(ROOT/'src/build/libamiga_backend.so'),memory,regs


def execute(context,**kwargs):
    run,memory,regs=context
    return volume.execute(run,DATA,memory,regs,relocated=False,dead=False,armed=False,
                          volume=kwargs.pop('volume',0),xy=kwargs.pop('xy',(840,168)),
                          instruction_budget=kwargs.pop('instruction_budget',256),warm_start=True,**kwargs)


@pytest.mark.parametrize('xy,expected,steps',[
    ((840,168),64,141),((1095,168),1,141),((33608,32936),64,143),
])
def test_captured_warm_start_initializes_four_channels_and_returns(warm_context,xy,expected,steps):
    result=execute(warm_context,xy=xy,volume=65535)
    assert result['logical_word']==expected and result['steps']==steps
    assert volume.warm_effect_contract(result,warm_context[1])['status']=='pass'
    assert 0x5d7de in result['pcs'] and 0x5e378 in result['pcs']
    assert not any(0x5e380<=pc<0x5e3ea for pc in result['pcs'])
    assert not result['BYTE_writer_executed']
    port=[e for e in result['events'] if e['address']==0xbfe001]
    assert [e['kind'] for e in port]==['read','write']
    assert port[0]['value']==warm_context[1][0xbfe001]
    assert any(r['origin']=='captured_device_snapshot_as_CPU_input'
               for r in result['fixture']['known_ranges'])


@pytest.mark.parametrize('address',[0xbfe001,0x5df48,0x5e25c])
def test_warm_start_unknown_device_preset_or_pointer_read_refuses(warm_context,address):
    run,memory,regs=warm_context;memory=dict(memory);del memory[address]
    with pytest.raises(bv.BehaviourError) as exc:execute((run,memory,regs))
    assert exc.value.result['status']=='missing_prerequisite' and exc.value.result['address']==address


def test_cold_sample_guard_and_old_budget_are_not_admitted(warm_context):
    run,memory,regs=warm_context;memory=dict(memory);memory[0x5dd06]=0
    with pytest.raises(bv.BehaviourError) as exc:execute((run,memory,regs))
    assert exc.value.result['status']=='missing_prerequisite'
    with pytest.raises(bv.BehaviourError) as exc:execute(warm_context,instruction_budget=128)
    assert exc.value.result['status']=='timeout_not_observed_within_bounds'
    with pytest.raises(bv.BehaviourError) as exc:execute(warm_context,xy=(1096,168))
    assert exc.value.result['status']=='unsupported'


def test_warm_channel_order_is_not_replaced_by_equal_final_fields(warm_context):
    result=execute(warm_context);changed=copy.deepcopy(result)
    positions=[i for i,e in enumerate(changed['events']) if e['kind']=='write' and 0x5dd14<=e['address']<0x5ddd4]
    a,b=positions[:2];changed['events'][a],changed['events'][b]=changed['events'][b],changed['events'][a]
    assert changed['effects']==result['effects'] and changed['state']==result['state']
    outcome=volume.warm_effect_contract(changed,warm_context[1])
    assert outcome['status']=='mismatch' and outcome['first_divergence']==0


@pytest.fixture
def canonical_set(tmp_path,monkeypatch):
    from amiga_reversing.disasm import effective_metadata,project_paths,target_metadata,manual_actions,decision_journal
    contracts=[dict(contract_id=k,entry_source=7) for k in ('old','new')]
    summary=dict(function_summary_id='summary',callable_kind='direct',entry_offset=7,
                 note=bv.CONTRACT_PREFIX+json.dumps(dict(contracts=contracts)))
    monkeypatch.setattr(effective_metadata,'effective_target_metadata',lambda *args:True)
    monkeypatch.setattr(target_metadata,'target_metadata_json_payload',lambda *args:dict(function_summaries=[summary]))
    monkeypatch.setattr(project_paths,'resolve_project_paths',lambda *args:SimpleNamespace(target_dir=tmp_path,binary_source=None))
    monkeypatch.setattr(manual_actions,'load_manual_projection',lambda *args,**kwargs:SimpleNamespace(active_action_ids={'action'}))
    (tmp_path/'manual_actions.jsonl').write_text(json.dumps(dict(action_id='action',function_summary=summary))+'\n')
    monkeypatch.setattr(decision_journal,'read_decision_journal',lambda *args:dict(valid=True,records=[]))
    monkeypatch.setattr(decision_journal,'project_decision_journal',lambda *args:dict(accepted_facts=[dict(
        fact_type='restoration_interpretation',selected_identity=dict(subject_id='action'),decision_id='decision')]))
    return summary,contracts


def test_named_predicates_share_the_existing_summary_action_and_review(canonical_set):
    old=bv.canonical_contract('target','old');new=bv.canonical_contract('target','new')
    assert old['contract']['contract_id']=='old' and new['contract']['contract_id']=='new'
    assert old['contract_sha256']!=new['contract_sha256']
    for key in ('function_summary_id','action_id','decision_id','review_status'):
        assert old[key]==new[key]
    assert new['review_status']=='accepted'


@pytest.mark.parametrize('failure',['duplicate','wrong_entry','oversize','mixed_wrapper'])
def test_named_contract_sets_fail_closed(canonical_set,failure):
    summary,contracts=canonical_set
    if failure=='duplicate':contracts.append(dict(contracts[0]))
    elif failure=='wrong_entry':contracts[0]['entry_source']=8
    elif failure=='oversize':contracts*=5
    wrapper=dict(contracts=contracts)
    if failure=='mixed_wrapper':wrapper['contract_id']='hidden'
    summary['note']=bv.CONTRACT_PREFIX+json.dumps(wrapper)
    with pytest.raises(bv.BehaviourError) as exc:bv.canonical_contract('target','old')
    assert exc.value.result['status']==('missing_prerequisite' if failure=='duplicate' else 'unsupported')


def test_replacement_summary_never_inherits_an_older_actions_acceptance(canonical_set,tmp_path,monkeypatch):
    from amiga_reversing.disasm import manual_actions,decision_journal
    summary,_=canonical_set
    path=tmp_path/'manual_actions.jsonl'
    with path.open('a') as stream:stream.write(json.dumps(dict(action_id='replacement',function_summary=summary))+'\n')
    monkeypatch.setattr(manual_actions,'load_manual_projection',lambda *args,**kwargs:SimpleNamespace(active_action_ids={'action','replacement'}))
    assert bv.canonical_contract('target','new')['action_id']=='replacement'
    assert bv.canonical_contract('target','new')['review_status']=='unassessed'
    monkeypatch.setattr(decision_journal,'project_decision_journal',lambda *args:dict(accepted_facts=[dict(
        fact_type='restoration_interpretation',selected_identity=dict(subject_id='replacement'),decision_id='new-review')]))
    assert bv.canonical_contract('target','new')['review_status']=='accepted'
    summary['note']+=' '
    with pytest.raises(bv.BehaviourError) as exc:bv.canonical_contract('target','new')
    assert exc.value.result['status']=='missing_prerequisite'


def test_warm_service_binds_reviewed_private_capture_and_refuses_changes(service,tmp_path,monkeypatch):
    canonical,result,request=service
    capture=tmp_path/'.runtime-state/warm/capture.json';capture.parent.mkdir(parents=True);capture.write_text('{}')
    canonical['contract'].update(contract_id='pandora.volume.warm-start.v1',instruction_budget=256,
        control_source_ranges=[list(r) for r in volume.WARM_CODE_RANGES],
        sample_initialization='captured_nonzero_guard',device_inputs='captured_CIAA_port_snapshot_CPU_model',
        fixture_capture=str(capture.relative_to(tmp_path)),fixture_capture_sha256=rv._hash(capture.read_bytes()))
    result['context_sha256']=rv._hash(capture.read_bytes())
    invoked=[]
    def compare(*args,**kwargs):
        invoked.append((args[1],kwargs['warm_start']))
        return result
    monkeypatch.setattr(volume,'compare',compare)
    assert rv.run_behaviour('target','revision',request)['status']=='pass'
    assert invoked==[(capture,True)]
    capture.write_text('{"changed":true}')
    assert rv.run_behaviour('target','revision',request)['status']=='stale'
    capture.unlink()
    assert rv.run_behaviour('target','revision',request)['status']=='missing_prerequisite'
    canonical['contract']['fixture_capture']='outside.json'
    assert rv.run_behaviour('target','revision',request)['status']=='unsupported'
    assert len(invoked)==1
    canonical['contract']['fixture_capture']=str(capture.relative_to(tmp_path));capture.write_text('{}')
    result['context_sha256']=bv.digest('unreviewed consumed fixture')
    assert rv.run_behaviour('target','revision',request)['status']=='stale'
    assert len(invoked)==2


def test_capture_swap_between_service_admission_and_consumption_is_stale(service,tmp_path,monkeypatch):
    if not CAPTURE.exists():
        pytest.skip('Private identity-bound warm fixture absent; no capture race evaluated')
    canonical,_,request=service
    capture=tmp_path/'.runtime-state/warm/capture.json';capture.parent.mkdir(parents=True)
    reviewed=CAPTURE.read_bytes();capture.write_bytes(reviewed)
    changed=json.loads(reviewed)
    xy=next(r for r in changed['runner']['observation']['scenario']['phases'][-1]['capture']['memory_reads']
            if int(r['address'],0)==0x5c352)
    data=bytearray.fromhex(xy['bytes']);data[1]^=1;xy['bytes']=data.hex()
    replacement=json.dumps(changed).encode()
    canonical['contract'].update(contract_id='pandora.volume.warm-start.v1',instruction_budget=256,
        control_source_ranges=[list(r) for r in volume.WARM_CODE_RANGES],
        sample_initialization='captured_nonzero_guard',device_inputs='captured_CIAA_port_snapshot_CPU_model',
        fixture_capture=str(capture.relative_to(tmp_path)),fixture_capture_sha256=rv._hash(reviewed))
    manifest,_,artifact=manifest_fixture((tmp_path/request['manifest']).parent)
    (tmp_path/'src/build/libamiga_backend.so').write_bytes((ROOT/'src/build/libamiga_backend.so').read_bytes())
    consumed=[]
    def compare(*args,**kwargs):
        assert capture.read_bytes()==reviewed
        capture.write_bytes(replacement)
        # The changed capture still passes real structural/code admission.
        volume.load_context(capture,DATA,warm_start=True)
        result=REAL_COMPARE(*args,**kwargs)
        consumed.append(result['context_sha256'])
        return result
    monkeypatch.setattr(volume,'compare',compare)
    result=rv.run_behaviour(TARGET,'a'*64,request,artifact=artifact)
    assert result['status']=='stale',dict(status=result['status'],consumed=consumed,reviewed=rv._hash(reviewed))
    assert not consumed  # Refused before executing the unreviewed CPU fixture.


def test_context_hash_and_parser_use_one_immutable_byte_snapshot(tmp_path,monkeypatch):
    if not CAPTURE.exists():
        pytest.skip('Private identity-bound warm fixture absent; no snapshot race evaluated')
    reviewed=CAPTURE.read_bytes();context=tmp_path/'context.json';context.write_bytes(reviewed)
    replacement=json.loads(reviewed)
    port=next(r for r in replacement['runner']['observation']['scenario']['phases'][-1]['capture']['memory_reads']
              if int(r['address'],0)==0xbfe001)
    original_port=int(port['bytes'],16);port['bytes']=bytes([original_port^2]).hex()
    changed=json.dumps(replacement).encode();parser=volume.context_from_bytes;consumed=[]
    def parse(snapshot,*args,**kwargs):
        context.write_bytes(changed)
        try:
            result=parser(snapshot,*args,**kwargs)
            consumed.append(result[1][0xbfe001])
            return result
        finally:context.write_bytes(reviewed)
    monkeypatch.setattr(volume,'context_from_bytes',parse)
    manifest,_,artifact=manifest_fixture(tmp_path)
    result=REAL_COMPARE(TARGET,context,manifest,ROOT/'src/build/libamiga_backend.so',
                        artifact=artifact,warm_start=True,expected_context_sha256=rv._hash(reviewed))
    assert consumed==[original_port] and result['context_sha256']==rv._hash(reviewed)
    assert result['routine_comparison']['accepted_cases']==6
