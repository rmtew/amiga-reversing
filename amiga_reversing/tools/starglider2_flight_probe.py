"""Bounded original-media flight observation with explicitly opted-in protection input.

Reads the selected original record and enters its answer using raw keyboard
press/release transitions. No guest-memory or register writes. Captures remain
private; this does not establish full-game or all-code coverage.
"""
import argparse
import hashlib
import json
from pathlib import Path
from amiga_reversing.tools.copperline_control import CopperlineProcess
from amiga_reversing.tools.copperline_runtime import wait_for_pc

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--copperline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--answer-selected-protection-request', action='store_true', help='Explicit opt-in to read the selected original record and type its answer')
    parser.add_argument('--observe-model-paths', action='store_true',
                        help='Observe bounded model/disc entries after flight, then stop')
    args = parser.parse_args(argv)
    if not args.answer_selected_protection_request:
        parser.error('This probe requires explicit protection-input opt-in')
    p = args.inputs.resolve()
    out = args.output.resolve()
    from amiga_reversing.tools.starglider2_refinement_probe import IDENTITIES
    for filename, expected in IDENTITIES.items():
        if hashlib.sha256((p / filename).read_bytes()).hexdigest() != expected:
            raise ValueError('Unexpected original input: ' + filename)
    out.mkdir(parents=True, exist_ok=False)
    r = dict(status='incomplete', steps=[], inputs=[], limits=['Unmodified original media; normal controller and keyboard input only', 'No guest register/memory writes; no DMA coverage claim'])

    def save():
        (out / 'receipt.json').write_text(json.dumps(r, indent=2) + '\n')

    def stage(n, v):
        r['steps'].append(dict(name=n, **v))
        save()
        print(n, json.dumps(v), flush=True)
    try:
        with CopperlineProcess(str(args.copperline), rom=str(args.rom), floppy=str(p / 'original.adf')) as process:
            c = process.client
            for n, pc, addr, f in [('intro', 0x24000, 0x23FF8, 'first-read.bin'), ('main', 0x1000, 0x1000, 'main-copy.bin')]:
                w = wait_for_pc(c, pc, 60)
                stage(n, w)
                assert w['status'] == 'hit'
                assert c.read_memory(addr, len((p / f).read_bytes())) == (p / f).read_bytes()
                c.joystick(port=1, blue=n == 'intro')
                r['inputs'].append(dict(frame=w['stop_event']['frame'], port=1, blue=n == 'intro'))
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
