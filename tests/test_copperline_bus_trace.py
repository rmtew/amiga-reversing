import json
from pathlib import Path

import pytest

from amiga_reversing.tools import copperline_bus_trace as bus, copperline_runtime as runtime
from amiga_reversing.tools.copperline_control import CopperlineError, CopperlineTimeout
from tests.test_copperline_runtime import Client, payload


def spec():
    return dict(frames=2, wait_seconds=3,
                ranges=[dict(name='region', address=0x1000, length=32)])


def profile(path, frames=2):
    path = Path(path)
    (path/'profile.json').write_text(json.dumps(dict(version=1, frames_written=frames)))
    rows = []
    for n in range(frames):
        name = f'slots-{n:06}-frame-{10+n:06}.bin'
        records = [
            (0x1000, 2, 1, 2, 0, 0, 0x1000, 0x1234, 0),
            (0x72, 5, 1, 2, 0, 0, 0x1002, 0x5678, 0),
            (0, 5, 3, 2, 0, 1, 0x2000, 0x9abc, 0),
            (0xffff, 0, 0, 0, 0, 0, 0x1000, 0, 0),
        ]
        (path/name).write_bytes(b''.join(bus.SLOT.pack(*r) for r in records))
        rows.append(dict(frame=10+n, traced=True, partial=n == 0, rows=1,
                         line_cck=4, slots_file=name, slots_record_bytes=24, retired=7))
    (path/'profile.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))


def test_slot_parser_uses_documented_width_flags_owner_and_exact_extent(tmp_path):
    profile(tmp_path)
    result = bus.read_bus_profile(tmp_path, spec()['ranges'], 2)
    assert result['scanned_slots'] == 8 and result['matching_transfers'] == 4
    assert result['frames'][0]['partial'] is True
    assert result['counts'] == [
        dict(range='region', engine='blitter', access='read', transfers=2),
        dict(range='region', engine='cpu', access='read', transfers=2)]
    assert result['records'][1]['address'] == 0x1002
    assert result['records'][1]['size'] == 2
    assert result['records'][1]['data'] == '0x0000000000005678'


@pytest.mark.parametrize('change', ['extent', 'path', 'stride', 'owner_only', 'missing', 'instantaneous'])
def test_parser_refuses_incomplete_or_unsupported_bus_coverage(tmp_path, change):
    profile(tmp_path)
    p = tmp_path/'profile.jsonl'
    rows = [json.loads(x) for x in p.read_text().splitlines()]
    if change == 'extent':
        (tmp_path/rows[0]['slots_file']).write_bytes(b'bad')
    elif change == 'path':
        rows[0]['slots_file'] = '../outside.bin'
    elif change == 'stride':
        rows[0]['slots_record_bytes'] = 25
    elif change == 'owner_only':
        rows[0]['traced'] = False
    elif change == 'missing':
        rows.pop()
    else:
        rows[0]['instantaneous_slots'] = [dict(vpos=0, hpos=0)]
    p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    with pytest.raises(CopperlineError):
        bus.read_bus_profile(tmp_path, spec()['ranges'], 2)


def test_retained_transfer_limit_does_not_hide_full_scanned_counts(tmp_path, monkeypatch):
    profile(tmp_path)
    monkeypatch.setattr(bus, 'MAX_MATCHES', 1)
    result = bus.read_bus_profile(tmp_path, spec()['ranges'], 2)
    assert len(result['records']) == 1 and result['omitted_matching_records'] == 3
    assert sum(r['transfers'] for r in result['counts']) == 4


def test_write_flag_and_crossing_transfer_keep_actual_bus_address(tmp_path):
    profile(tmp_path)
    result = bus.read_bus_profile(tmp_path, [dict(name='last_byte', address=0x2001, length=1)], 2)
    assert result['counts'] == [dict(range='last_byte', engine='blitter', access='write', transfers=2)]
    assert result['records'][0]['address'] == 0x2000
    assert result['records'][0]['size'] == 2
    assert result['records'][0]['flags'] == 1


@pytest.mark.parametrize('change', [
    {'frames': True}, {'frames': 0}, {'frames': 5}, {'wait_seconds': 31},
    {'ranges': []}, {'extra': 'command'},
    {'ranges': [dict(name='region', address=0xfffff0, length=32)]},
    {'ranges': [dict(name='../escape', address=0x1000, length=2)]},
    {'ranges': [dict(name='region', address=0x1000, length=4097)]},
])
def test_trace_schema_is_bounded_and_has_no_arbitrary_protocol_fields(change):
    request = spec()
    request.update(change)
    with pytest.raises(ValueError):
        bus.validate_bus_trace(request)


@pytest.mark.parametrize('timeout', [False, True])
def test_owned_capture_stops_and_retains_event_on_success_or_timeout(tmp_path, timeout):
    c = Client()
    c.stop = CopperlineTimeout('expired') if timeout else dict(reason='target', frame=13)
    original = c.request
    output = None
    def request(method, params=None):
        nonlocal output
        if method == 'profile.start':
            output = params['path']
        if method == 'profile.stop':
            profile(output)
        return original(method, params)
    c.request = request
    result = bus.capture_bus_trace(c, spec(), dict(frame=10), tmp_path)
    assert result['status'] == ('timeout' if timeout else 'captured')
    assert c.calls[-1][0] == 'profile.stop'
    assert result['profile_request']['memory'] is False
    assert result['profile_request']['screenshots'] == 'none'


def test_profile_cleanup_failure_is_not_a_successful_capture(tmp_path):
    c = Client()
    c.stop = dict(reason='target', frame=13)
    original = c.request
    def request(method, params=None):
        if method == 'profile.stop':
            raise CopperlineError('cannot stop owned profile')
        return original(method, params)
    c.request = request
    with pytest.raises(CopperlineError, match='cannot stop'):
        bus.capture_bus_trace(c, spec(), dict(frame=10), tmp_path)


@pytest.mark.parametrize('identity_ok', [True, False])
def test_trace_requires_the_original_canonical_anchor_before_start(tmp_path, monkeypatch, identity_ok):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    c.stop = dict(reason='target', frame=10)
    calls = []
    def capture(*args):
        calls.append(args)
        return dict(status='captured', stop_event=dict(reason='target', frame=13))
    monkeypatch.setattr(bus, 'capture_bus_trace', capture)
    phase = dict(name='bus', stable_key='s0:00000200:instruction', breakpoint_address=0x1200,
                 source_offset=0x200 if identity_ok else 0x201, wait_seconds=1, chip_bus_trace=spec())
    result = runtime._run_scenario_phase(c, phase, p, {}, None, trace_directory=tmp_path)
    assert bool(calls) == identity_ok
    assert result['status'] == ('hit' if identity_ok else 'not_hit')


def complete_profile(path):
    profile(path)
    p=path/'profile.json';summary=json.loads(p.read_text());summary['samples_dropped']=0
    p.write_text(json.dumps(summary))


def test_partitions_keep_order_and_real_repeated_addresses(tmp_path):
    complete_profile(tmp_path)
    result=bus.read_bus_partitions(tmp_path,[[dict(name='source',address=0x1000,length=4)],
                                           [dict(name='destination',address=0x2000,length=2)]],2)
    assert result['matching_transfers']==6 and result['omitted_matching_records']==0
    assert [r['address'] for r in result['records']]==[0x1000,0x1002,0x2000]*2
    assert result['partition_matching_transfers']==[4,2]


def test_crossing_access_in_two_projections_is_one_physical_event(tmp_path):
    complete_profile(tmp_path)
    result=bus.read_bus_partitions(tmp_path,[[dict(name='head',address=0x1000,length=2)],
                                           [dict(name='tail',address=0x1001,length=2)]],2)
    assert result['matching_transfers']==4 and result['projection_memberships']==6
    assert result['records'][0]['ranges']==['head','tail']
    assert result['records'][2]['address']==result['records'][0]['address']
    assert result['records'][2]['frame']!=result['records'][0]['frame']


def test_partition_join_keeps_container_order_and_refuses_ambiguous_labels(tmp_path):
    complete_profile(tmp_path)
    path=tmp_path/'profile.jsonl';frames=[json.loads(x) for x in path.read_text().splitlines()]
    frames[0]['frame']=11;frames[1]['frame']=10
    path.write_text(''.join(json.dumps(f)+'\n' for f in frames))
    result=bus.read_bus_partitions(tmp_path,[[dict(name='source',address=0x1000,length=4)]],2)
    assert [r['frame'] for r in result['records']]==[11,11,10,10]
    frames[1]['frame']=11;path.write_text(''.join(json.dumps(f)+'\n' for f in frames))
    with pytest.raises(CopperlineError,match='not unique'):
        bus.read_bus_partitions(tmp_path,[[dict(name='source',address=0x1000,length=4)]],2)


@pytest.mark.parametrize('failure',['truncated','combined_limit','changed_sidecar'])
def test_partition_join_refuses_incomplete_or_changed_evidence(tmp_path,monkeypatch,failure):
    complete_profile(tmp_path)
    if failure=='truncated':monkeypatch.setattr(bus,'MAX_MATCHES',1)
    if failure=='changed_sidecar':
        read=bus.read_bus_profile;calls=[]
        def changing(*args):
            if calls:
                path=tmp_path/'slots-000000-frame-000010.bin'
                slots=list(bus.SLOT.iter_unpack(path.read_bytes()));r=list(slots[2]);r[7]+=1;slots[2]=r
                path.write_bytes(b''.join(bus.SLOT.pack(*r) for r in slots))
            calls.append(True);return read(*args)
        monkeypatch.setattr(bus,'read_bus_profile',changing)
    with pytest.raises(CopperlineError):
        bus.read_bus_partitions(tmp_path,[[dict(name='source',address=0x1000,length=4)],
                                         [dict(name='destination',address=0x2000,length=2)]],2,
                                max_total=5 if failure=='combined_limit' else 8192)


@pytest.mark.parametrize('partitions,limit',[
    ([],8192),([[dict(name='r',address=0,length=1)]]*5,8192),
    ([[dict(name='r',address=0,length=4097)]],8192),
    ([[dict(name='r',address=dict(base_register='a0',offset=0),length=1)]],8192),
    ([[dict(name='r',address=0,length=1)],[dict(name='r',address=2,length=1)]],8192),
    ([[dict(name='r',address=0,length=1)]],8193),
])
def test_partition_schema_stays_bounded(tmp_path,partitions,limit):
    with pytest.raises(CopperlineError):bus.read_bus_partitions(tmp_path,partitions,2,max_total=limit)
