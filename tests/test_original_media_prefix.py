"""Original media must reach a verified, normal-input boundary before scenarios."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.tools import copperline_session as session
from amiga_reversing.tools import original_media_prefix as media
from amiga_reversing.tools import starglider2_flight_probe as flight

TARGET = 'amiga_raw_starglider2_game'


@pytest.mark.parametrize('target,prefix', [('other', 'starglider2'), (TARGET, 'unknown'), (TARGET, None)])
def test_recipe_cannot_select_other_targets_or_unregistered_code(target, prefix):
    with pytest.raises(ValueError, match='not registered'):
        media.validate_prefix_target(prefix, target)


@pytest.mark.parametrize('conflicting_base,native_address', [(None,None), (0x10000,None), (None,0x2288)])
def test_compile_uses_exact_recipe_coordinates_without_mutating_artifact(tmp_path, monkeypatch, conflicting_base, native_address):
    view = () if conflicting_base is None else (
        dict(source_start=0, source_end=412736, base_addr=conflicting_base),)
    artifact = SimpleNamespace(_runtime_observation_views=view, close=lambda: None,
        row_for_source_offset=lambda **_: dict(stable_key='s0:00000288:instruction',
            section_index=0, start_offset=0x288, **({'runtime_address':native_address} if native_address else {})))
    monkeypatch.setattr(session, 'build_project_listing_artifact_profile', lambda _: (0, {}, artifact))
    spec = dict(schema_version=1, target_id=TARGET, identifier='media-test', original_media_prefix='starglider2',
        phases=[dict(name='media', observable='original_media_handoff'),
                dict(name='flight', breakpoint_stable_key='s0:00000288:instruction', wait_seconds=1)])
    path = tmp_path / 'scenario.json'; path.write_text(json.dumps(spec))
    if conflicting_base or native_address:
        with pytest.raises(ValueError, match='conflicts'):
            session.compile_scenario(TARGET, path, tmp_path / 'compiled.json')
    else:
        result = session.compile_scenario(TARGET, path, tmp_path / 'compiled.json', symbol_directory=tmp_path)
        assert result['phases'][0]['breakpoint_address'] == 0x1288
        assert result['phases'][0]['runtime_view']['requires_loaded_byte_identity']
        assert 'symbols' not in result  # no injected-function support in this mode
    assert artifact._runtime_observation_views == view


@pytest.mark.parametrize('option', ['--direct-payload-contract', '--checkpoint-load', '--host-directory'])
def test_cli_rejects_mixed_launch_modes_before_loading_target(tmp_path, option):
    with pytest.raises(ValueError, match='Original-media prefix requires|cannot be combined'):
        session.main(['--target', TARGET, '--rom', 'rom', '--floppy0', 'disk',
            '--scenario', 'scenario.json', '--state-directory', str(tmp_path),
            '--original-media-prefix', 'starglider2', option, 'other'])


def test_original_media_refuses_function_injection_before_listing(tmp_path):
    spec = dict(schema_version=1, target_id=TARGET, identifier='injection', original_media_prefix='starglider2',
        phases=[dict(name='media', observable='original_media_handoff'),
                dict(name='forced', breakpoint_stable_key='s0:00000288:instruction',
                     wait_seconds=1, transition='enter_function')])
    path = tmp_path/'scenario.json'; path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match='normal execution only'):
        session.compile_scenario(TARGET, path, tmp_path/'compiled.json')


def test_wrong_disk_is_rejected_before_creating_run_inputs(tmp_path):
    disk = tmp_path/'disk.adf'; disk.write_bytes(b'not the reviewed disk')
    spec = tmp_path/'compiled.json'; spec.write_text(json.dumps(dict(target_id=TARGET,
        start_observable='original_media_handoff', original_media_prefix='starglider2', phases=[dict(name='flight')])))
    run_dir = tmp_path/'run'
    config = session.HeadlessCopperlineSession(rom_path=Path('rom'), target_payload_path=tmp_path/'payload',
        binary_path=Path('runtime'), floppy0=disk, state_directory=run_dir, scenario_path=spec,
        original_media_prefix='starglider2')
    with pytest.raises(ValueError, match='reviewed'):
        media.run_original_media_session(config)
    assert not run_dir.exists()


@pytest.fixture
def prefix_client(tmp_path, monkeypatch):
    from amiga_reversing.tools import copperline_runtime as runtime, starglider2_refinement_probe as refinement
    image = bytearray(0xD000); image[0xCF0C] = ord('A')
    blobs = {'original.adf': b'disk', 'first-read.bin': b'intro', 'main-copy.bin': bytes(image)}
    for name, data in blobs.items(): (tmp_path / name).write_bytes(data)
    monkeypatch.setattr(refinement, 'IDENTITIES', {k: hashlib.sha256(v).hexdigest() for k,v in blobs.items()})
    class Client:
        frame = 1
        fail_press = False
        bad_copy = False
        events = []
        def read_memory(self, address, size):
            if address == 0x23FF8: return b'intro'
            if address == 0x1000: return b'bad' if self.bad_copy else blobs['main-copy.bin']
            if address == 0x60068: return (0x12F80).to_bytes(4, 'big')
            if address == 0x12F80: return b'\0\0\0A' + b'\0'*12
            return bytes(size)
        def registers(self): return dict(a6=0x60000, pc=0x1288, sp=0x3370)
        def joystick(self, **control): self.events.append(('joystick', control))
        def key(self, key, *, pressed):
            self.events.append(('key', key, pressed))
            if pressed and self.fail_press: raise RuntimeError('lost press response')
        def run_until(self, goal, **_): self.frame = goal['frame']; return dict(frame=self.frame)
    client = Client()
    class Process:
        def __init__(self, *_, **__): self.client = client
        def __enter__(self): return self
        def __exit__(self, *_): client.events.append(('closed',))
    monkeypatch.setattr(flight, 'CopperlineProcess', Process)
    monkeypatch.setattr(flight, 'wait_for_pc', lambda *_, **__: dict(status='hit', stop_event=dict(frame=client.frame)))
    monkeypatch.setattr(runtime, 'payload_at_pc', lambda *_, **__: dict(status='pc_matched', runtime_base='0x1000', payload_offset='0x288'))
    calls = []
    def scenario(c, spec, payload, release, **_):
        assert c is client and payload.read_bytes() == blobs['main-copy.bin']
        boundary = release(); assert boundary['memory_write'] is boundary['register_write'] is None
        calls.append(spec)
        return dict(phases=[dict(status='hit') for _ in spec['phases']])
    monkeypatch.setattr(runtime, 'run_scenario', scenario)
    args = ['--inputs', str(tmp_path), '--output', str(tmp_path/'run'),
            '--rom', 'rom', '--copperline', 'runtime', '--answer-selected-protection-request']
    spec = dict(target_id=TARGET, original_media_prefix='starglider2',
                start_observable='original_media_handoff', phases=[dict(name='flight')])
    return client, args, spec, calls


def test_normal_prefix_passes_same_client_only_after_loaded_identity(prefix_client):
    client, args, spec, calls = prefix_client
    result = flight.main(args, canonical_scenario=spec)
    assert calls == [spec]
    assert result['canonical_observation']['status'] == 'ok'
    handoff = result['canonical_observation']['observation']['original_media_handoff']
    assert len(handoff['loaded_payloads']) == 2
    assert all(p['byte_exact'] for p in handoff['loaded_payloads'])
    assert client.events[-1] == ('closed',)


@pytest.mark.parametrize('failure', ['bad_copy', 'fail_press'])
def test_failed_prefix_never_runs_scenario_and_releases_owned_input(prefix_client, failure):
    client, args, spec, calls = prefix_client
    setattr(client, failure, True)
    with pytest.raises((ValueError, RuntimeError)):
        flight.main(args, canonical_scenario=spec)
    assert not calls and client.events[-1] == ('closed',)
    assert ('joystick', dict(port=1)) in client.events
    assert ('joystick', dict(port=2)) in client.events
    if failure == 'fail_press': assert ('key', 0, False) in client.events
