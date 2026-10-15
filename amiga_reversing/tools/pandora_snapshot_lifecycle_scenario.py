"""Compose snapshot stops into Pandora's existing normal Feed input route.

Writes a disposable scenario for the public target-aware Copperline session CLI.
It does not modify game state, canonical target facts or the base scenario.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_SCENARIO = ROOT / 'runtime/scenarios/pandora-volume-feed-combat-probe.json'


def build_scenario():
    scenario = json.loads(BASE_SCENARIO.read_text())
    scenario['identifier'] = 'pandora-snapshot-gameplay-lifecycle'
    capture = {
        'registers': ['a5', 'a6', 'sr'],
        'custom_registers': ['DMACON', 2, 28, 30],
        'memory_reads': [{'address': address, 'size': size} for address, size in [
            (0x1335A, 44), (0x133DE, 44), (0x77D00, 64), (0x77FE0, 32),
            (0x7F0, 64), (0x10B0, 64), (0x3C2A, 1)]],
    }

    def phase(name, offset, seconds=10):
        return {'name': name, 'breakpoint_stable_key': f's0:{offset:08X}:instruction',
                'wait_seconds': seconds, 'capture': capture}

    phases = []
    for item in scenario['phases']:
        if item['name'] == 'feed_after_combat_audio_entry':
            phases.extend([phase('hit_restore_call', 0x7A8E, 20),
                           phase('hit_restore_start', 0x63FA),
                           phase('hit_restore_flags_clear', 0x640C),
                           phase('hit_restore_return', 0x7A92)])
        item['capture'] = capture
        phases.append(item)
        if item['name'] == 'feed_combat_entry':
            phases.extend([phase('hit_capture_entry', 0x6332),
                           phase('hit_capture_started', 0x6396),
                           phase('hit_clear_started', 0x64AA),
                           phase('hit_overlay_ready', 0x77B8)])
    phases.extend([phase('post_combat_idle', 0x5CA),
                   phase('body_open_entry', 0x27E0, 15),
                   phase('body_capture_entry', 0x6332),
                   phase('body_overlay_ready', 0x281E),
                   phase('body_open_idle', 0x5CA),
                   phase('body_open_idle_release', 0x5CA),
                   phase('body_restore_call', 0x27C0, 15),
                   phase('body_restore_flags_clear', 0x640C),
                   phase('body_next_clear_wait', 0x6478)])
    scenario['phases'] = phases
    scenario['input_events'].extend([
        {'after_phase': 'post_combat_idle', 'control': 'key 64',
         'release_after_phase': 'body_open_entry'},
        {'after_phase': 'body_open_idle_release', 'control': 'key 64',
         'release_after_phase': 'body_restore_call'},
    ])
    return scenario


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build_scenario(), indent=2)+'\n')


if __name__ == '__main__':
    main()
