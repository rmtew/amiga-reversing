"""Bounded normal-media boot/title/protection-entry observations.

Private payload/ROM inputs are supplied by the caller. No protection answers
are read or entered. Not observing flight or a write never establishes dead code.
"""
import argparse
import hashlib
import json
from pathlib import Path

from amiga_reversing.tools.copperline_control import CopperlineProcess
from amiga_reversing.tools.copperline_runtime import wait_for_memory_access, wait_for_pc

IDENTITIES = {
    'original.adf': '77c633a9270f85361a30ba19175f5940155631ceb6c84b47b1efbb0bf2150ee3',
    'first-read.bin': '553dcd88883415160d219d6c5b1c3cddfb9c80e2aeb20aab20cb8943a0650f2e',
    'main-copy.bin': '662976920689c38fd47271ed7e656a92caf20aa20ce0b8801db2bdc77ba864d9',
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True,
                        help='Private original.adf, first-read.bin and main-copy.bin directory')
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--copperline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=['flight-entry', 'shot-watch'], default='flight-entry')
    args = parser.parse_args(argv)
    inputs, output = args.inputs.resolve(), args.output.resolve()
    for filename, expected in IDENTITIES.items():
        if hashlib.sha256((inputs / filename).read_bytes()).hexdigest() != expected:
            raise ValueError('Unexpected original input: ' + filename)
    output.mkdir(parents=True, exist_ok=False)
    result = dict(status='incomplete', input_sha256=IDENTITIES, steps=[], inputs=[], mode=args.mode,
                  limits=['Original ADF; no guest memory/register writes',
                          'CPU range watch only; no DMA or complete code coverage claim'])

    def save():
        (output / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')

    def stage(name, value):
        result['steps'].append(dict(name=name, **value))
        save()
        print(name, json.dumps(value), flush=True)

    try:
        with CopperlineProcess(str(args.copperline), rom=str(args.rom),
                               floppy=str(inputs / 'original.adf')) as process:
            client = process.client
            for name, pc, address, filename in [
                ('intro', 0x24000, 0x23FF8, 'first-read.bin'),
                ('main', 0x1000, 0x1000, 'main-copy.bin'),
            ]:
                observed = wait_for_pc(client, pc, 60)
                stage(name, observed)
                if observed['status'] != 'hit':
                    raise RuntimeError('Entry not observed: ' + name)
                data = (inputs / filename).read_bytes()
                if client.read_memory(address, len(data)) != data:
                    raise RuntimeError('Payload differs at entry: ' + name)
                result['steps'][-1].update(payload_byte_exact=True, payload_sha256=IDENTITIES[filename])
                result['inputs'].append(dict(frame=observed['stop_event']['frame'], port=1,
                                             blue=name == 'intro'))
                client.joystick(port=1, blue=name == 'intro')
            observed = wait_for_pc(client, 0x118A, 60)
            stage('title_wait', observed)
            if observed['status'] != 'hit':
                raise RuntimeError('Title input loop not observed')
            registers = client.registers()
            base = int.from_bytes(client.read_memory(0x27A8, 4), 'big')
            stage('title_registers', dict(registers=registers, workspace_pointer=base))
            if registers['a6'] != base:
                raise RuntimeError('Title A6 is not the stored workspace base')
            frame = observed['stop_event']['frame']
            result['inputs'].append(dict(frame=frame, port=2, red=True))
            client.joystick(port=2, red=True)
            observed = client.run_until({'frame': frame + 25}, timeout=30)
            stage('fire_held', observed)
            client.joystick(port=2)
            result['inputs'].append(dict(frame=observed['frame'], port=2, red=False))
            observed = wait_for_pc(client, 0x1202, 30)
            stage('game_start_transition', observed)
            if observed['status'] != 'hit':
                raise RuntimeError('Start transition not observed')
            if args.mode == 'flight-entry':
                observed = wait_for_pc(client, 0x1288, 45,
                                       frame_limit=observed['stop_event']['frame'] + 1200)
                stage('flight_frame_entry', observed)
                result['flight_loop_observed'] = observed['status'] == 'hit'
            else:
                observed = client.run_until({'frame': observed['stop_event']['frame'] + 150}, timeout=30)
                stage('post_start_settle', observed)
                client.joystick(port=2, red=True)
                result['inputs'].append(dict(frame=observed['frame'], port=2, red=True))
                watch = wait_for_memory_access(client, dict(address=base + 0x6DC, length=4,
                    access='write', engine='cpu', wait_seconds=30, frames=300), start_event=observed)
                stage('shots_field_write', watch)
                stage('after_watch_registers', dict(registers=client.registers(),
                                                    stats=client.read_memory(base + 0x6DC, 24).hex()))
                client.joystick(port=2)
                stop = watch.get('stop_event') or {}
                result['inputs'].append(dict(frame=stop.get('frame'), port=2, red=False))
            result['status'] = 'bounded_observation_complete'
            save()
    except Exception as error:
        result.update(status='failed_or_not_observed', error=str(error))
        save()
        raise


if __name__ == '__main__':
    main()
