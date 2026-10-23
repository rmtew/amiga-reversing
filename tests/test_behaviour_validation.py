import copy
import ctypes as C
import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.behaviour_validation import (
    BehaviourError, IDENTITIES, MemoryEvidence, admit_identities,
    check_producer_consumer, compare_ordered, digest, fixture_manifest,
)
from amiga_reversing.tools import pandora_volume_local_compare as volume

ROOT = Path(__file__).resolve().parents[1]
DATA = (ROOT/'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8/binary.bin').read_bytes()


@pytest.fixture
def cpu_context():
    _, memory, regs = volume.load_context(ROOT/'runtime/observations/pandora-volume-local-context.json', DATA)
    run = volume.load_engine(ROOT/'src/build/libamiga_backend.so')
    assert run.observed is not None, 'Build the generated backend with its ordered observer'
    return run, memory, regs


def test_ordered_comparison_rejects_equal_final_state_and_duplicate_loss():
    a = [dict(address=5,value=1),dict(address=5,value=2),dict(address=5,value=2)]
    b = [dict(address=5,value=2),dict(address=5,value=1),dict(address=5,value=2)]
    assert a[-1] == b[-1]
    assert compare_ordered(a,b)['first_divergence'] == 0
    assert compare_ordered(a,a[:-1])['first_divergence'] == 2
    assert compare_ordered(a,a)['status'] == 'pass'
    assert compare_ordered([],[],complete=False)['status'] == 'incomplete_truncated'


@pytest.mark.parametrize('key',sorted(IDENTITIES))
def test_every_changed_assumption_stales_prior_result(key):
    a = {k:digest(k) for k in IDENTITIES};b=dict(a);b[key]=digest('changed')
    assert admit_identities(a,a)['status'] == 'pass'
    assert admit_identities(a,b) == dict(status='stale',reason='Bound assumption changed',identity=key,expected=a[key],actual=b[key])
    del b[key]
    assert admit_identities(a,b)['status'] == 'missing_prerequisite'


def test_shadow_zero_is_unknown_and_write_establishes_only_its_extent():
    memory=bytearray(16);e=MemoryEvidence(memory,{},[(4,8)])
    with pytest.raises(BehaviourError) as exc:e.access(0,4,2,0)
    assert exc.value.result['status']=='missing_prerequisite'
    e.access(1,4,2,0x1234);memory[4:6]=b'\x12\x34';e.access(0,4,2,0x1234)
    assert e.events[0]['before'] is None
    with pytest.raises(BehaviourError):e.access(0,6,1,0)
    with pytest.raises(BehaviourError) as exc:e.access(1,7,2,0)
    assert exc.value.result['status']=='mismatch'
    e.event_limit=len(e.events)
    with pytest.raises(BehaviourError) as exc:e.access(0,4,2,0x1234)
    assert exc.value.result['status']=='incomplete_truncated'
    f=fixture_manifest(memory,e.known,donor_sha256=digest('donor'),modeled_inputs={},registers={})
    assert f['known_ranges'][0]['end']==6 and 'bytes' not in f['known_ranges'][0]


def transfer(access,address=0x1002,value=0x1234):
    return dict(engine='blitter',access=access,address=address,size=2,data=hex(value),
                subtype=3 if access=='write' else 0,reg=0x54 if access=='write' else 0x50)


def test_bus_read_before_write_fails_even_with_identical_final_buffer():
    write=transfer('write');read=transfer('read');tail=transfer('write',value=0)
    a=[write,read,tail];b=[read,write,tail]
    assert a[-1]==b[-1]
    assert check_producer_consumer(a,start=0x1000,end=0x1004)['status']=='pass'
    bad=check_producer_consumer(b,start=0x1000,end=0x1004)
    assert bad['status']=='mismatch' and bad['first_divergence']==0
    assert check_producer_consumer([write,transfer('read',value=7)],start=0x1000,end=0x1004)['status']=='mismatch'
    assert check_producer_consumer([transfer('write',0x1000),transfer('read',0x1000)],start=0x1000,end=0x1004)['status']=='mismatch'
    assert check_producer_consumer(a,start=0x1000,end=0x1004,complete=False)['status']=='incomplete_truncated'
    assert check_producer_consumer([],start=0x1000,end=0x1004)['status']=='timeout_not_observed_within_bounds'
    assert check_producer_consumer([write],start=0x1000,end=0x1004)['status']=='incomplete_truncated'
    assert check_producer_consumer([dict(write,engine='cpu')],start=0x1000,end=0x1004)['status']=='unsupported'


@pytest.mark.parametrize('xy,expected',[
    ((840,168),64),((1095,168),1),((1096,168),64),((839,168),64),
    ((33607,168),64),((33608,168),64),((33608,32936),64),((808,154),53),
])
def test_generated_word_arithmetic_and_ordered_return(cpu_context,xy,expected):
    run, projection,regs=cpu_context
    r=volume.execute(run,DATA,projection,regs,relocated=False,dead=False,armed=True,volume=0x1234,xy=xy)
    assert r['logical_word']==expected and r['state']['pc']==volume.RETURN
    assert r['events'][-1]['kind']=='read' and r['events'][-1]['value']==volume.RETURN
    assert any(e['kind']=='fetch' for e in r['events'])


def test_cpu_fixture_refuses_unknown_inputs_and_preserves_first_failure(cpu_context):
    run, projection,regs=cpu_context;projection=dict(projection)
    del projection[0x5c352]
    with pytest.raises(BehaviourError) as exc:
        volume.execute(run,DATA,projection,regs,relocated=False,dead=False,armed=True,volume=64)
    assert exc.value.result['status']=='missing_prerequisite' and exc.value.result['address']==0x5c352
    assert exc.value.result['pc']==0x6530e


def test_budget_and_unadmitted_audio_initialisation_are_nonpass(cpu_context):
    run, projection,regs=cpu_context
    with pytest.raises(BehaviourError) as exc:
        volume.execute(run,DATA,projection,regs,relocated=False,dead=True,armed=True,volume=64,instruction_budget=1)
    assert exc.value.result['status']=='timeout_not_observed_within_bounds'
    with pytest.raises(BehaviourError) as exc:
        volume.execute(run,DATA,projection,regs,relocated=False,dead=False,armed=False,volume=64,xy=(840,168))
    assert exc.value.result['status']=='unsupported'


def test_call_frame_store_and_return_reads_are_observed(cpu_context):
    run,projection,regs=cpu_context
    r=volume.execute(run,DATA,projection,regs,relocated=False,dead=True,armed=True,volume=255)
    calls=[e for e in r['events'] if e['kind']=='write' and e['pc']==0x652ea]
    assert len(calls)==1 and calls[0]['width']==4 and calls[0]['value']==0x652f0
    assert any(e['kind']=='read' and e['value']==0x652f0 for e in r['events'])


def test_observer_rejects_exception_and_does_not_leak_to_next_call(cpu_context):
    run,projection,regs=cpu_context
    memory=bytearray(0x1000);memory[0x100:0x102]=bytes.fromhex('4e40')
    s=volume.cpu(regs);s.pc=0x100
    buffer=(C.c_uint8*len(memory)).from_buffer(memory);trace=volume.Trace()
    callback=volume.Observe(lambda *args:1);observer=volume.Observer(callback,None)
    run.observed(0,buffer,len(memory),C.byref(s),1,0x200,0x202,None,C.byref(observer),C.byref(trace))
    assert trace.steps==0 and trace.stop_reason==5
    # Wrapper restored the prior TLS context; the next ordinary original call works.
    assert volume.execute(run,DATA,projection,regs,relocated=False,dead=True,armed=False,volume=64)['logical_word']==64


def test_renderer_checks_exact_address_order_not_only_read_values():
    from amiga_reversing.tools.pandora_scratch_behaviour import validate_renderer_stream
    events=[transfer('write',0x1b3a8+4*p+16*r+2*w,value=0)
            for p in range(4) for r in range(32) for w in range(2)]
    events += [transfer('read',0x1b3aa+4*r,value=0) for r in range(128)]
    assert validate_renderer_stream(events)['status']=='pass'
    repeated=copy.deepcopy(events);repeated[-1]=dict(repeated[-2])
    assert validate_renderer_stream(repeated)['status']=='mismatch'
    reordered=[events[256],*events[:256],*events[257:]]
    assert validate_renderer_stream(reordered)['first_divergence']==0
    assert validate_renderer_stream(events[:-1])['status']=='mismatch'
    wrong_channel=copy.deepcopy(events);wrong_channel[-1]['subtype']=1
    assert validate_renderer_stream(wrong_channel)['status']=='mismatch'


@pytest.mark.parametrize('bad',[
    dict(engine='blitter',size=2,address='invalid',access='read',data='0'),
    dict(engine='blitter',size=2,address=0x1002,access='read',data='bad-hex'),
    None,
])
def test_malformed_physical_transfers_are_unsupported(bad):
    assert check_producer_consumer([bad],start=0x1000,end=0x1004)['status']=='unsupported'


def test_changed_contract_budget_is_not_ignored():
    with pytest.raises(BehaviourError):volume.admit_contract(dict(contract_id='pandora.volume.local.v1',instruction_budget=1))


@pytest.mark.parametrize('phase,expected',[
    (dict(status='timeout'),'timeout_not_observed_within_bounds'),
    (dict(termination='capture_expectation_mismatch'),'mismatch'),
    (dict(chip_bus_trace=dict(status='unavailable')),'unsupported'),
    (dict(status='not_hit'),'incomplete_truncated'),
])
def test_capture_failure_categories_do_not_become_equivalence(tmp_path,phase,expected):
    from amiga_reversing.tools.pandora_scratch_behaviour import read_capture
    file=tmp_path/'failed.json';file.write_text(json.dumps(dict(runner=dict(status='incomplete',
        observation=dict(status='incomplete',scenario=dict(phases=[phase]))))))
    with pytest.raises(BehaviourError) as exc:read_capture(file,b'',{}, {})
    assert exc.value.result['status']==expected
