"""Bounded natural HAND instruction-boundary probe; never release guest GO.

Replay an existing qualified experiment.adf on the same diagnostic ECS profile.
No media creation, payload patches, register writes or gameplay execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .copperline_control import CopperlineProcess
from .copperline_runtime import wait_for_marker


def probe(run_directory: Path, output: Path, rom: Path, copperline: Path) -> dict:
    adf = run_directory / 'experiment.adf'
    expected = json.loads((run_directory / 'report.json').read_text())
    identity = hashlib.sha256(adf.read_bytes()).hexdigest()
    if identity != expected['adf_sha256']:
        raise ValueError('Qualified ADF identity differs; refusing execution')
    output.mkdir(parents=True, exist_ok=False)
    report = dict(schema_version=1, ADF_sha256=identity,
        scope='Natural HAND then fixed CCK target and 16 successive instruction-boundary observations; never GO.',
        points=[], payload_entry_released=False, guest_memory_or_register_writes=False)
    try:
        with CopperlineProcess(copperline, rom=rom, floppy=adf,
                machine_profile='a500ecs_1m', audio_wav=output / 'boot.wav') as process:
            client = process.client
            marker = wait_for_marker(client, 0x7fff8, b'HAND', 90)
            if not marker['matched'] or marker['stop_reason'] != 'watchpoint':
                raise ValueError('Natural HAND guest write was not caught')
            report['natural_HAND'] = dict(marker=marker,
                status=client.request('status'), registers=client.registers())
            report['loop_memory'] = client.read_memory(0x1618, 32).hex()
            target = 500 * 71051
            for _ in range(17):
                stop = client.run_until({'cck': target}, timeout=30)
                if stop['reason'] != 'target' or client.read_memory(0x7fff8, 4) != b'HAND':
                    raise ValueError('Expected target stop in unreleased HAND state')
                report['points'].append(dict(requested_cck=target, stop=stop,
                    registers=client.registers()))
                target = stop['cck'] + 1
            report['status'] = 'complete_before_GO'
    except BaseException as exc:
        report['status'] = 'probe_failed'
        report['error'] = str(exc)
        raise
    finally:
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-directory', type=Path, required=True,
        help='Existing qualified capture with report.json and experiment.adf')
    parser.add_argument('--output-directory', type=Path, required=True, help='Fresh private directory')
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--copperline', type=Path, required=True)
    args = parser.parse_args()
    report = probe(args.run_directory, args.output_directory, args.rom, args.copperline)
    print(json.dumps(dict(status=report['status'], observed_boundaries=len(report['points']))))


if __name__ == '__main__':
    main()
