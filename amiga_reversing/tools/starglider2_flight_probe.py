"""Bounded original-media flight observation with explicitly opted-in protection input.

Reads the selected original record and enters its answer using raw keyboard
press/release transitions. No guest-memory or register writes. Captures remain
private; this does not establish full-game or all-code coverage.
"""
import argparse
from contextlib import ExitStack
import hashlib
import json
import time
from pathlib import Path
from amiga_reversing.tools.copperline_control import CopperlineProcess, CopperlineTimeout
from amiga_reversing.tools.copperline_runtime import wait_for_pc


def _bind_instruction_windows(hits, views):
    """Coordinate-bound byte matches, retaining ambiguity between source views."""
    identities = [(target, base, data, hashlib.sha256(data).hexdigest())
                  for target, base, data in views]
    result = []
    for index, hit in enumerate(hits):
        pc = hit['triggering_pc']
        sample = bytes.fromhex(hit['instruction_window_hex'])
        if len(sample) != 16:
            raise ValueError('Startup source binding requires the recorded 16-byte window')
        matches = [dict(target_id=target, section_index=0, source_offset=pc-base,
                        source_sha256=digest)
                   for target, base, data, digest in identities
                   if 0 <= pc-base <= len(data)-len(sample) and data[pc-base:pc-base+len(sample)] == sample]
        result.append(dict(hit_index=index, runtime_pc=pc, sample_size=len(sample),
            sample_sha256=hashlib.sha256(sample).hexdigest(), matches=matches,
            status='matched' if len(matches) == 1 else 'ambiguous' if matches else 'not_matched'))
    return result


def bind_startup_flag_source_views(hits, original):
    from amiga_reversing.tools import starglider2_protection as recipe
    decoded, transformation = recipe.extract_view(original)
    return dict(transformation=transformation,
        instruction_windows=_bind_instruction_windows(hits, [
            ('amiga_raw_starglider2_game', 0x1000, original),
            ('amiga_raw_starglider2_protection_view', recipe.START, decoded)]),
        scope='Site windows only, not whole runtime-view identity or original encoded code promotion')


class StartupFlagObserver:
    """First CPU zero writes to two fixed target flags, without changing inputs.

    Resume the SAME absolute frame/PC goal after each observed bus transfer.
    Stop collecting once both first clears are seen; later writers are outside
    this observation. This adapter neither writes guest state nor guesses code.
    """
    def __init__(self, client, base, original, stage, *, max_hits=16):
        self.client, self.base, self.original, self.stage = client, base, original, stage
        self.max_hits, self.hits, self.cleared, self.ident = max_hits, [], {}, None
        self.armed = dict(kind='mmio', addr=base + 0x205, len=2, access='write')
        try:
            self.ident = client.request('break.add', self.armed)['id']
            state = client.request('break.list')
            entries = state.get('breaks', [])
            if not isinstance(entries, list) or not all(isinstance(b, dict) for b in entries):
                raise ValueError('Malformed startup flag watch readback')
            if not any(b.get('id') == self.ident and all(b.get(k) == v for k, v in self.armed.items())
                       for b in entries):
                raise ValueError('Startup flag watch readback differs from requested CPU range')
            if any(b.get('id') != self.ident and b.get('kind') in ('mmio', 'watch') for b in entries):
                raise ValueError('Startup flag observation requires an isolated memory watch')
            stage('startup_flag_watch_armed', dict(armed_watch=self.armed, watch_id=self.ident,
                backend_watch_state=state, flags=client.read_memory(base + 0x205, 2).hex(),
                max_hits=max_hits, coverage='CPU data writes only; no DMA/fetch coverage'))
        except Exception:
            self.close_watch()
            raise

    def __getattr__(self, name):
        return getattr(self.client, name)

    def close_watch(self):
        ident, self.ident = self.ident, None
        if ident is not None:
            self.client.remove_breakpoint(ident)

    def run_until(self, params, *, timeout):
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CopperlineTimeout('Startup flag observation exhausted original run deadline')
            stop = self.client.run_until(params, timeout=remaining)
            if stop.get('reason') != 'mmio':
                return stop
            access = stop.get('access') or {}
            addr, size, value, pc = (access.get(k) for k in ('addr', 'size', 'value', 'pc'))
            if (self.ident is None or access.get('access') != 'write'
                    or type(addr) is not int or type(size) is not int or size not in (1, 2, 4)
                    or type(value) is not int or not 0 <= value < (1 << (8 * size))
                    or type(pc) is not int or not 0 <= pc <= 0xFFFFF0
                    or not (addr < self.base + 0x207 and addr + size > self.base + 0x205)):
                raise ValueError('Unexpected memory trap during startup flag observation')
            if len(self.hits) >= self.max_hits:
                raise ValueError('Startup flag write budget exhausted before both first clears')
            registers = self.client.registers()
            sample = self.client.read_memory(pc, 16)
            offset = pc - 0x1000
            matches = 0 <= offset <= len(self.original) - 16 and sample == self.original[offset:offset + 16]
            hit = dict(stop_event=stop, registers=registers, triggering_pc=pc,
                instruction_window_hex=sample.hex(), original_bytes_match=matches,
                source_offset=offset if matches else None,
                flags=self.client.read_memory(self.base + 0x205, 2).hex())
            self.hits.append(hit)
            for flag in (0x205, 0x206):
                at = self.base + flag
                if addr <= at < addr + size and not ((value >> (8 * (addr + size - 1 - at))) & 255):
                    self.cleared.setdefault(flag, len(self.hits) - 1)
            self.stage('startup_flag_write', dict(hit_index=len(self.hits) - 1, **hit))
            if len(self.cleared) == 2:
                self.close_watch()
                self.stage('startup_flags_first_clears_observed', dict(
                    first_clear_hit_indices={hex(k): v for k, v in self.cleared.items()},
                    collection_retired=True, later_writers_observed=False))

def observe_modal_inventory(client, flight_entry, workspace_base, translation, stage, inputs):
    """Bounded empty-inventory modal observation, using normal keys only.

    Snapshots establish state, not per-byte attribution. The two CPU watches
    attribute only the modal flag writes. Nonempty-list formatting is not covered.
    """
    from amiga_reversing.tools.copperline_runtime import wait_for_memory_access

    def state(label):
        fields = {hex(offset): client.read_memory(workspace_base + offset, size).hex()
                  for offset, size in [(0x6DA, 1), (0x6C2, 2), (0x7C2, 2),
                      (0x17C, 2), (0x756, 2), (0x752, 2), (0xA70, 2),
                      (0xA48, 10), (0xA55, 10), (0xA62, 10), (0x774, 6)]}
        stage(label, dict(workspace_base=workspace_base, fields=fields))

    def key(token, pressed, frame):
        raw = next(i for i, value in enumerate(translation) if value == token)
        client.key(raw, pressed=pressed)
        inputs.append(dict(frame=frame, rawkey=raw, pressed=pressed))
        return raw

    event = client.run_until({'frame': flight_entry['stop_event']['frame'] + 120}, timeout=30)
    state('normal_before')
    event = client.run_until({'frame': event['frame'] + 30}, timeout=30)
    state('normal_after_30')
    for token, expected, label in [(8, b'\xff', 'modal_flag_set'), (88, b'\x00', 'modal_flag_clear')]:
        raw = key(token, True, event['frame'])
        try:
            observed = wait_for_memory_access(client, dict(address=workspace_base + 0x6DA,
                length=1, access='write', engine='cpu', wait_seconds=30, frames=180),
                start_event=event)
            stage(label, observed)
        finally:
            client.key(raw, pressed=False)
            inputs.append(dict(rawkey=raw, pressed=False, release_after_watch=True))
        assert observed['status'] == 'hit'
        assert client.read_memory(workspace_base + 0x6DA, 1) == expected
        event = observed['stop_event']
        state('modal_at_set' if token == 8 else 'modal_at_clear')
        if token == 8:
            event = client.run_until({'frame': event['frame'] + 30}, timeout=30)
            state('modal_after_30')
            raw = key(73, True, event['frame'])
            try:
                event = client.run_until({'frame': event['frame'] + 3}, timeout=10)
            finally:
                client.key(raw, pressed=False)
                inputs.append(dict(rawkey=raw, pressed=False, release_after_run=True))
            event = client.run_until({'frame': event['frame'] + 30}, timeout=30)
            state('modal_after_inventory_I')
    returned = wait_for_pc(client, 0x1288, 30, frame_limit=event['frame'] + 120)
    stage('returned_to_flight', returned)
    assert returned['status'] == 'hit'
    client.run_until({'frame': returned['stop_event']['frame'] + 30}, timeout=30)
    state('resumed_after_30')


def observe_reticle_target(client, flight_entry, workspace_base, translation, stage, inputs):
    """Observe actual reticle production and normal I-command scan, including no-target."""
    def state(label):
        stage(label, dict(registers=client.registers(), fields={
            hex(offset): client.read_memory(workspace_base + offset, size).hex()
            for offset, size in [(0x194, 2), (0x196, 2), (0x19C, 2), (0x19E, 2),
                (0x766, 2), (0x768, 2), (0x76A, 2), (0x76C, 2), (0x6B0, 4),
                (0x840, 2), (0x846, 2), (0x7D0, 2), (0x7D2, 2)]}))

    event = wait_for_pc(client, 0xD3E2, 30,
                        frame_limit=flight_entry['stop_event']['frame'] + 180)
    stage('reticle_coordinates_ready', event)
    assert event['status'] == 'hit'
    state('reticle_state')
    raw = next(i for i, value in enumerate(translation) if value == 73)
    client.key(raw, pressed=True)
    inputs.append(dict(frame=event['stop_event']['frame'], rawkey=raw, pressed=True))
    try:
        event = wait_for_pc(client, 0x753C, 30,
                            frame_limit=event['stop_event']['frame'] + 180)
        stage('identify_command_entry', event)
    finally:
        client.key(raw, pressed=False)
        inputs.append(dict(rawkey=raw, pressed=False, release_after_watch=True))
    assert event['status'] == 'hit'
    for label, pc in [('target_scan_setup', 0x73FC), ('target_scan_return', 0x74FE)]:
        event = wait_for_pc(client, pc, 30,
                            frame_limit=event['stop_event']['frame'] + 120)
        stage(label, event)
        assert event['status'] == 'hit'
        state(label + '_state')
    # Zero type means no candidate, even if another shared field is stale.
    kind = int.from_bytes(client.read_memory(workspace_base + 0x840, 2), 'big')
    if kind:
        target = int.from_bytes(client.read_memory(workspace_base + 0x6B0, 4), 'big')
        pool = workspace_base + 0x2330
        assert pool <= target < pool + 17000 and (target - pool) % 68 == 0
        record = client.read_memory(target, 68)
        assert int.from_bytes(record[:2], 'big') == kind
        stage('target_record', dict(address=target, pool_record=(target - pool) // 68,
            stored_type=kind, sha256=hashlib.sha256(record).hexdigest()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--copperline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--answer-selected-protection-request', action='store_true', help='Explicit opt-in to read the selected original record and type its answer')
    parser.add_argument('--observe-model-paths', action='store_true',
                        help='Observe bounded model/disc entries after flight, then stop')
    parser.add_argument('--observe-modal-inventory', action='store_true',
                        help='Observe bounded Backspace/I/X inventory modal state, then stop')
    parser.add_argument('--observe-reticle-target', action='store_true',
                        help='Observe reticle production and normal I-key target scan, then stop')
    parser.add_argument('--observe-startup-flags', action='store_true',
                        help='Observe first CPU clears of app0205/0206 through the normal startup/input prefix')
    args = parser.parse_args(argv)
    if sum([args.observe_model_paths, args.observe_modal_inventory, args.observe_reticle_target,
            args.observe_startup_flags]) > 1:
        parser.error('Choose only one bounded observation route')
    if not args.answer_selected_protection_request:
        parser.error('This probe requires explicit protection-input opt-in')
    p = args.inputs.resolve()
    out = args.output.resolve()
    from amiga_reversing.tools.starglider2_refinement_probe import IDENTITIES
    for filename, expected in IDENTITIES.items():
        if hashlib.sha256((p / filename).read_bytes()).hexdigest() != expected:
            raise ValueError('Unexpected original input: ' + filename)
    out.mkdir(parents=True, exist_ok=False)
    r = dict(status='incomplete', steps=[], inputs=[],
        driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_sha256=dict(IDENTITIES), machine_profile='a500ocs_512k',
        limits=['Unmodified original media; normal controller and keyboard input only', 'No guest register/memory writes; no DMA coverage claim'])

    def save():
        (out / 'receipt.json').write_text(json.dumps(r, indent=2) + '\n')

    def stage(n, v):
        r['steps'].append(dict(name=n, **v))
        save()
        print(n, json.dumps(v), flush=True)
    try:
        with CopperlineProcess(str(args.copperline), rom=str(args.rom), floppy=str(p / 'original.adf')) as process, ExitStack() as observers:
            c = process.client
            for n, pc, addr, f in [('intro', 0x24000, 0x23FF8, 'first-read.bin'), ('main', 0x1000, 0x1000, 'main-copy.bin')]:
                w = wait_for_pc(c, pc, 60)
                stage(n, w)
                assert w['status'] == 'hit'
                assert c.read_memory(addr, len((p / f).read_bytes())) == (p / f).read_bytes()
                c.joystick(port=1, blue=n == 'intro')
                r['inputs'].append(dict(frame=w['stop_event']['frame'], port=1, blue=n == 'intro'))
            flag_observer = None
            if args.observe_startup_flags:
                anchor = wait_for_pc(c, 0xCD56, 60)
                stage('startup_flags_initialized', anchor)
                assert anchor['status'] == 'hit'
                original = (p / 'main-copy.bin').read_bytes()
                assert c.read_memory(0xCD56, 16) == original[0xBD56:0xBD66]
                base = c.registers()['a6']
                assert 0 <= base <= 0x80000 - 0x6998
                assert int.from_bytes(c.read_memory(0x27A8, 4), 'big') == base
                assert c.read_memory(base + 0x205, 2) == b'\xff\xff'
                flag_observer = StartupFlagObserver(c, base, original, stage)
                observers.callback(flag_observer.close_watch)
                c = flag_observer
            w = wait_for_pc(c, 0x118A, 60)
            stage('title', w)
            assert w['status'] == 'hit'
            frame = w['stop_event']['frame']
            c.joystick(port=2, red=True)
            r['inputs'].append(dict(frame=frame, port=2, red=True))
            w = c.run_until({'frame': frame + 25}, timeout=30)
            c.joystick(port=2)
            r['inputs'].append(dict(frame=w['frame'], port=2, red=False))
            w = wait_for_pc(c, 0xD7BE, 45, frame_limit=w['frame'] + 1200)
            stage('protection_input', w)
            assert w['status'] == 'hit'
            regs = c.registers()
            base = regs['a6']
            selected = int.from_bytes(c.read_memory(base + 0x68, 4), 'big')
            assert 0x12F80 <= selected < 0x12F80 + 147 * 16 and (selected - 0x12F80) % 16 == 0
            record = c.read_memory(selected, 16)
            answer = record[3:].split(b'\x00', 1)[0]
            assert answer and len(answer) <= 12 and all((32 <= x < 127 for x in answer))
            translation = (p / 'main-copy.bin').read_bytes()[0xDF0C - 0x1000:0xDF0C - 0x1000 + 126]
            keys = []
            for char in answer:
                candidates = [i for i, x in enumerate(translation) if x == char]
                assert candidates, hex(char)
                keys.append(candidates[0])
            stage('selected_record', dict(address=selected, coordinates=list(record[:3]), sha256=hashlib.sha256(record).hexdigest(), answer_length=len(answer), registers=regs))
            frame = w['stop_event']['frame']
            for key in keys + [0x44]:
                c.key(key, pressed=True)
                r['inputs'].append(dict(frame=frame, rawkey=key, pressed=True))
                w = c.run_until({'frame': frame + 3}, timeout=10)
                frame = w['frame']
                c.key(key, pressed=False)
                r['inputs'].append(dict(frame=frame, rawkey=key, pressed=False))
                w = c.run_until({'frame': frame + 3}, timeout=10)
                frame = w['frame']
                save()
            stage('keyboard_answer_submitted', dict(frame=frame, transitions=len(keys + [0x44]) * 2))
            w = wait_for_pc(c, 0x1288, 45, frame_limit=frame + 1200)
            stage('flight_entry', w)
            if w['status'] == 'hit':
                regs = c.registers()
                base = regs['a6']
                stage('flight_state', dict(registers=regs, player_pointer=c.read_memory(base + 0x700, 4).hex(), resources=c.read_memory(base + 0x774, 34).hex()))
                if args.observe_startup_flags:
                    assert flag_observer is not None
                    stage('startup_flag_source_bindings', bind_startup_flag_source_views(
                        flag_observer.hits, (p / 'main-copy.bin').read_bytes()))
                    stage('startup_flags_at_flight', dict(flags=c.read_memory(base + 0x205, 2).hex(),
                        observed_first_clears={hex(k): v for k, v in flag_observer.cleared.items()},
                        hit_count=len(flag_observer.hits)))
                    r['status'] = ('bounded_startup_flag_observation_complete'
                        if len(flag_observer.cleared) == 2 else 'flight_reached_first_clears_not_observed')
                    save()
                    return
                if args.observe_reticle_target:
                    observe_reticle_target(c, w, base, translation, stage, r['inputs'])
                    r['status'] = 'bounded_reticle_target_observation_complete'
                    save()
                    return
                if args.observe_modal_inventory:
                    observe_modal_inventory(c, w, base, translation, stage, r['inputs'])
                    r['status'] = 'bounded_modal_inventory_observation_complete'
                    save()
                    return
                if args.observe_model_paths:
                    for label, pc in [('model_projection', 0x4A2A),
                                      ('nonmodel_disc_projection', 0x67F4)]:
                        observed = wait_for_pc(c, pc, 30,
                            frame_limit=w['stop_event']['frame'] + 180)
                        stage(label, observed)
                        if observed['status'] == 'hit':
                            context = c.registers()
                            record = c.read_memory(context['a4'], 68)
                            selector = context['d0'] & 0xFFFF
                            state = dict(registers=context,
                                object_pointer=context['a4'],
                                stored_object_type=int.from_bytes(record[:2], 'big'),
                                type30_render_selector=int.from_bytes(c.read_memory(base + 0x192, 2), 'big'),
                                active_model_index=int.from_bytes(c.read_memory(base + 0x190, 2), 'big'))
                            if label == 'model_projection' and selector < 104:
                                state.update(model_selector=selector,
                                    header_pointer=int.from_bytes(c.read_memory(0x18974 + 4 * selector, 4), 'big'))
                            stage(label + '_context', state)
                    r['status'] = 'bounded_model_path_observation_complete'
                    save()
                    return
                from amiga_reversing.tools.copperline_bus_trace import capture_bus_trace
                from amiga_reversing.tools.copperline_runtime import wait_for_memory_access

                def pool_snapshot(label):
                    data = c.read_memory(base + 0x2330, 17000)
                    (out / (label + '.bin')).write_bytes(data)
                    from collections import Counter
                    stage(label, dict(sha256=hashlib.sha256(data).hexdigest(), pool_base=base + 0x2330, records=250, stride=68, type_counts=dict(Counter((str(int.from_bytes(data[i:i + 2], 'big')) for i in range(0, len(data), 68))))))
                pool_snapshot('pool_at_flight_entry')
                x = c.run_until({'frame': w['stop_event']['frame'] + 120}, timeout=30)
                stage('flight_settle', x)
                trace = capture_bus_trace(c, dict(frames=4, wait_seconds=30, ranges=[dict(name='app_resource_words', address=base + 0x740, length=96), dict(name='sound_event_flags', address=base + 0xAE0, length=224), dict(name='player_record', address=int.from_bytes(c.read_memory(base + 0x700, 4), 'big'), length=68)]), x, out)
                (out / 'flight-bus-trace.json').write_text(json.dumps(trace, indent=2))
                stage('flight_bus_trace', dict(status=trace['status'], stop_event=trace.get('stop_event'), counts=trace.get('profile', {}).get('counts'), omitted_matching_records=trace.get('profile', {}).get('omitted_matching_records'), samples_dropped=trace.get('profile', {}).get('profile_summary', {}).get('samples_dropped')))
                pool_snapshot('pool_after_settle')
                x = trace.get('stop_event') or x
                fire_key = c.read_memory(base + 0x7F2, 1)[0]
                assert 0 <= fire_key < 128
                stage('configured_fire_key', dict(rawkey=fire_key, one_hand=c.read_memory(base + 0x7F1, 1).hex()))
                c.key(fire_key, pressed=True)
                r['inputs'].append(dict(frame=x['frame'], rawkey=fire_key, pressed=True))
                try:
                    watch = wait_for_memory_access(c, dict(address=base + 0x6DC, length=4, access='write', engine='cpu', wait_seconds=30, frames=300), start_event=x)
                    stage('shots_field_write', watch)
                    stage('after_shot_registers', dict(registers=c.registers(), stats=c.read_memory(base + 0x6DC, 24).hex()))
                finally:
                    c.key(fire_key, pressed=False)
                    r['inputs'].append(dict(frame=(watch.get('stop_event') or x)['frame'] if 'watch' in locals() else None, rawkey=fire_key, pressed=False))
                    save()
            r['status'] = 'flight_observed' if w['status'] == 'hit' else 'not_observed_within_bounds'
            save()
    except Exception as e:
        r.update(status='failed', error=str(e))
        save()
        print('FAIL', repr(e), flush=True)
        raise
if __name__ == '__main__':
    main()
