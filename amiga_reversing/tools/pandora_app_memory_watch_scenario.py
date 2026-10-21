"""Compose one app-declaration-gap watch into Pandora's existing input route.

This writes a scenario for copperline_session, not guest state or source facts.
Use a fresh owned state directory for every run; raw reports stay local.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'runtime/scenarios/pandora-nearby-interaction-callback.json'
AUDIT = ROOT / 'docs/validation/pandora-app-access-audit.json'
APP_BASE = 0x39FC


def build_scenario(gap_start: int, window: str, access: str = 'access') -> dict:
    audit = json.loads(AUDIT.read_text())
    gap = next((g for g in audit['gaps'] if g['start'] == gap_start), None)
    if gap is None:
        raise ValueError('Choose a declaration-gap start from the published app audit')
    if window not in ('startup', 'moving') or access not in ('read', 'write', 'access'):
        raise ValueError('Unsupported watch window/access')
    scenario = copy.deepcopy(json.loads(BASE.read_text()))
    scenario['identifier'] = f'pandora-app-gap-{gap_start:03x}-{window}-{access}'
    capture = {
        'registers': [f'd{i}' for i in range(8)] + [f'a{i}' for i in range(8)] + ['sr'],
        'memory_reads': [{'base_register': 'a7', 'offset': 0, 'size': 32},
                         {'address': APP_BASE + gap_start,
                          'size': min(64, gap['end'] - gap_start)},
                         {'address': 0x5C352, 'size': 36}],
    }
    phase = {
        'name': 'watched_access',
        'breakpoint_stable_key': 's0:0000046A:instruction' if window == 'startup'
                                 else 's0:00009844:instruction',
        'wait_seconds': 20,
        'capture': capture,
        'memory_access_watch': {'address': APP_BASE + gap_start,
                                'length': gap['end'] - gap_start,
                                'engine': 'cpu', 'access': access, 'wait_seconds': 3},
    }
    if window == 'startup':
        scenario['phases'] = [scenario['phases'][0], phase]
        scenario['input_events'] = []
    else:
        # Retain the existing card transfer, 19 down commits and 20 right commits.
        # Keep right held through one further commit, then watch while held.
        # The watch ends on the first access or its wall deadline, not after a
        # deterministic number of emulated frames. Report the actual stop frame.
        scenario['phases'] = scenario['phases'][:7] + [phase]
        scenario['input_events'].append({
            'after_phase': 'rightward_moves_complete', 'control': 'port1 right',
            'release_after_phase': 'watched_access',
        })
    return scenario


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gap-start', type=lambda s: int(s, 0), required=True)
    p.add_argument('--window', choices=('startup', 'moving'), required=True)
    p.add_argument('--access', choices=('read', 'write', 'access'), default='access')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    scenario = build_scenario(args.gap_start, args.window, args.access)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scenario, indent=2) + '\n')


if __name__ == '__main__':
    main()
