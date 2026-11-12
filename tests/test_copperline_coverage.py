import struct
from pathlib import Path

import pytest

from amiga_reversing.tools import copperline_coverage as coverage
from amiga_reversing.tools import copperline_bus_trace as bus
from amiga_reversing.tools.copperline_control import CopperlineError
from tests.test_copperline_bus_trace import profile, spec
from tests.test_copperline_runtime import Client


def sidecar(path, base=0x1000, size=32):
    counts = [3, 1] + [0]*(size//2-2)
    path.write_bytes(b'CLCV'+struct.pack('<IIIII', 1, 1, base, size, size//2)
                     + struct.pack('<'+'I'*len(counts), *counts)+struct.pack('<IQQ', 0, 7, 11))


def binding(tmp_path):
    raw = tmp_path/'payload.bin'
    raw.write_bytes(bytes(range(32)))
    view = dict(section_index=0, base_addr=0x1000, source_start=0, source_end=32)
    return raw, view, coverage.bind_coverage_view(raw, view)


def test_exact_counter_format(tmp_path):
    _, _, bound = binding(tmp_path)
    p = tmp_path/'coverage.bin'; sidecar(p)
    result = coverage.read_retired_coverage(p, bound)
    assert result['counters'] == {0x1000: 3, 0x1002: 1}
    assert result['inside_retired'] == 4 and result['outside_retired'] == 7


@pytest.mark.parametrize('offset,value', [(0,0), (4,2), (8,2), (12,0x1002), (16,30),
                                          (20,15), (24,0xffffffff), (88,1), (100,12)])
def test_reject_malformed_or_inconsistent_counters(tmp_path, offset, value):
    _, _, bound = binding(tmp_path)
    p = tmp_path/'coverage.bin'; sidecar(p)
    raw = bytearray(p.read_bytes()); struct.pack_into('<I', raw, offset, value); p.write_bytes(raw)
    with pytest.raises(CopperlineError):
        coverage.read_retired_coverage(p, bound)


@pytest.mark.parametrize('delta', [-1, 1])
def test_exact_sidecar_extent(tmp_path, delta):
    _, _, bound = binding(tmp_path)
    p = tmp_path/'coverage.bin'; sidecar(p)
    raw = p.read_bytes(); p.write_bytes(raw[:-1] if delta < 0 else raw+b'x')
    with pytest.raises(CopperlineError): coverage.read_retired_coverage(p, bound)


@pytest.mark.parametrize('change', [dict(base_addr=4097), dict(source_end=33),
                                     dict(source_start=-2), dict(section_index=1), dict(base_addr=True)])
def test_reject_unbound_or_unaligned_views(tmp_path, change):
    raw, view, _ = binding(tmp_path); view.update(change)
    with pytest.raises(ValueError): coverage.bind_coverage_view(raw, view)


@pytest.mark.parametrize('value', [1, None, 'yes'])
def test_coverage_flag_is_strict_boolean(value):
    request = spec(); request['retired_coverage'] = value
    with pytest.raises(ValueError): bus.validate_bus_trace(request)


@pytest.mark.parametrize('writes,mismatch', [(False,False), (True,False), (False,True)])
def test_capture_pairs_retirement_with_same_window_identity_and_writes(tmp_path, writes, mismatch):
    raw, view, _ = binding(tmp_path)
    c = Client(); c.stop = dict(reason='target', frame=13)
    c.read_memory = lambda address,size: (b'x'*size if mismatch else raw.read_bytes()[:size])
    original = c.request; output = None
    def request(method, params=None):
        nonlocal output
        if method == 'profile.start':
            output = params['path']
            assert params['coverage'] is True
            assert params['code_ranges'] == [dict(base=0x1000, size=32)]
        if method == 'profile.stop':
            profile(output); sidecar(Path(output)/'coverage.bin')
            if writes:
                p = Path(output)/'slots-000000-frame-000010.bin'
                rows = bytearray(p.read_bytes()); rows[6:8] = struct.pack('<H', 1); p.write_bytes(rows)
        return original(method, params)
    c.request = request
    request_spec = dict(spec(), retired_coverage=True)
    result = bus.capture_bus_trace(c, request_spec, dict(frame=10), tmp_path,
                                   coverage_view=view, payload_path=raw)
    assert result['status'] == 'captured', result
    observed = result['retired_coverage']
    assert 'counters' not in observed
    assert observed['windows'][0]['retired_instructions'] == 4
    assert observed['windows'][0]['source_bytes_stable'] is (not writes and not mismatch)
    assert c.calls[-1][0] == 'profile.stop'


def test_missing_canonical_view_refuses_before_profile_start(tmp_path):
    c = Client()
    with pytest.raises(ValueError):
        bus.capture_bus_trace(c, dict(spec(), retired_coverage=True), dict(frame=10), tmp_path)
    assert not any(method == 'profile.start' for method, *_ in c.calls)


def test_changed_canonical_payload_is_rejected(tmp_path):
    raw, view, _ = binding(tmp_path)
    c = Client(); c.read_memory = lambda address,size: bytes(range(size))
    bound, windows = coverage.before_coverage(c, raw, view, spec()['ranges'])
    sidecar(tmp_path/'coverage.bin'); raw.write_bytes(b'changed')
    with pytest.raises(CopperlineError, match='payload changed'):
        coverage.finish_coverage(c, tmp_path, raw, bound, windows, dict(counts=[]))


def test_bad_coverage_is_unavailable_after_profile_cleanup(tmp_path):
    raw, view, _ = binding(tmp_path)
    c = Client(); c.stop = dict(reason='target', frame=13)
    c.read_memory = lambda address,size: raw.read_bytes()[:size]
    original = c.request; output = None
    def request(method, params=None):
        nonlocal output
        if method == 'profile.start': output = params['path']
        if method == 'profile.stop': profile(output)
        return original(method, params)
    c.request = request
    result = bus.capture_bus_trace(c, dict(spec(), retired_coverage=True), dict(frame=10), tmp_path,
                                   coverage_view=view, payload_path=raw)
    assert result['status'] == 'unavailable'
    assert c.calls[-1][0] == 'profile.stop'


@pytest.mark.parametrize('identity_ok', [True,False])
def test_runtime_forwards_verified_view_only_after_anchor(tmp_path, monkeypatch, identity_ok):
    from amiga_reversing.tools import copperline_runtime as runtime
    from tests.test_copperline_runtime import payload
    p = payload(tmp_path); c = Client(p.read_bytes()); c.stop = dict(reason='target', frame=10)
    calls = []
    def capture(*args, **kwargs):
        calls.append(kwargs)
        return dict(status='captured', stop_event=dict(reason='target', frame=13))
    monkeypatch.setattr(bus, 'capture_bus_trace', capture)
    view = dict(base_addr=0x1000,source_start=0,source_end=len(p.read_bytes()))
    phase = dict(name='coverage', stable_key='s0:00000200:instruction', breakpoint_address=0x1200,
                 source_offset=0x200 if identity_ok else 0x201, wait_seconds=1,
                 runtime_view=view, chip_bus_trace=dict(spec(),retired_coverage=True))
    result = runtime._run_scenario_phase(c,phase,p,{},None,trace_directory=tmp_path)
    assert bool(calls) is identity_ok
    if calls: assert calls == [dict(coverage_view=view,payload_path=p)]
    assert result['status'] == ('hit' if identity_ok else 'not_hit')


def test_chip_bus_cannot_prove_absence_of_cpu_only_memory_writes(tmp_path):
    raw, view, _ = binding(tmp_path)
    view['base_addr'] = 0xc00000
    c = Client()
    with pytest.raises(ValueError, match='Chip RAM'):
        coverage.before_coverage(c, raw, view, [dict(name='slow',address=0xc00000,length=32)])
