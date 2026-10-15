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
                   phase('body_open_entry', 0x27EA, 15),
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


def build_guard_root():
    """Save a normal post-combat root before any inventory input."""
    scenario = build_scenario()
    scenario['identifier'] = 'pandora-post-combat-body-guard-root'
    index = next(i for i, p in enumerate(scenario['phases']) if p['name'] == 'post_combat_idle')
    scenario['phases'] = scenario['phases'][:index+1]
    names = {p['name'] for p in scenario['phases']}
    scenario['input_events'] = [e for e in scenario['input_events']
                               if e['after_phase'] in names and e['release_after_phase'] in names]
    scenario['phases'][-1]['capture']['memory_reads'] += [
        {'address': address, 'size': size} for address, size in [
            (0x3B9A, 8), (0x5C322, 64), (0x5C362, 20), (0x5C1D2, 64), (0x5C212, 20)]]
    return scenario


def build_guard_scenario():
    capture = {'registers': ['a0', 'a1', 'a2', 'a4', 'a5', 'a6', 'd0', 'd1', 'd2', 'sr'],
               'memory_reads': [{'address': 0x3B9A, 'size': 8},
                                {'address': 0x3C2A, 'size': 1},
                                {'address': 0x5C352, 'size': 4},
                                {'base_register': 'a5', 'offset': 0x48, 'size': 1}]}
    geometry = {**capture, 'memory_reads': capture['memory_reads']+[
        {'base_register': reg, 'offset': 0, 'size': size}
        for reg, size in [('a0', 12), ('a1', 28), ('a2', 26)]]}
    return {'schema_version': 1, 'identifier': 'pandora-body-open-guard-inputs',
            'target_id': build_scenario()['target_id'], 'direct_payload_contract': 'pandora',
            'phases': [{'name': 'checkpoint', 'observable': 'verified_checkpoint'},
                       {'name': 'anchor', 'breakpoint_stable_key': 's0:000005CA:instruction', 'wait_seconds': 5},
                       {'name': 'nearest_guard', 'breakpoint_stable_key': 's0:00002736:instruction',
                        'wait_seconds': 10, 'capture': capture},
                       {'name': 'geometry_guard', 'breakpoint_stable_key': 's0:000026A4:instruction',
                        'wait_seconds': 5, 'capture': geometry}],
            'input_events': [{'after_phase': 'anchor', 'control': 'key 64',
                              'release_after_phase': 'nearest_guard'}]}


def build_body_scenario():
    # The direct-up geometric candidate is terrain-blocked. This local route
    # uses the existing terrain model and establishes left-facing first; each
    # commit is checked before any further input or inventory attempt.
    common = {'registers': ['a0', 'a1', 'a5', 'a6', 'd1', 'sr'],
              'custom_registers': ['DMACON', 2, 28, 30],
              'memory_reads': [{'address': a, 'size': n} for a, n in [
                  (0x1335A, 44), (0x133DE, 44), (0x5C352, 4),
                  (0x3B9A, 4), (0x5C21A, 1), (0x77FE0, 32)]]}
    sampled = {**common, 'memory_reads': common['memory_reads']+[
        {'address': a, 'size': 64} for a in [0x7F0, 0x830, 0x870, 0x1030, 0x1070, 0x10B0]]}

    def phase(name, offset, samples=False):
        return {'name': name, 'breakpoint_stable_key': f's0:{offset:08X}:instruction',
                'wait_seconds': 10, 'capture': sampled if samples else common}

    phases = [{'name': 'checkpoint', 'observable': 'verified_checkpoint'}, phase('anchor', 0x5CA)]
    route = [
        ('left', 822, 182),
        ('left', 815, 182),
        ('down', 822, 182),
        ('down', 822, 186),
        ('left', 815, 186),
        ('right', 822, 186),
        ('down', 815, 186),
        ('up', 815, 182),
        ('up', 815, 178),
        ('up', 815, 174),
        ('up', 815, 170),
        ('up', 815, 166),
        ('up', 815, 162),
        ('up', 815, 158),
        ('up', 815, 154),
        ('up', 815, 150),
        ('up', 815, 146),
        ('right', 822, 146),
    ]
    route_names = []
    for i, (direction, x, y) in enumerate(route):
        name = f'body_route_{i:02d}_{direction}'
        route_names.append(name)
        item = phase(name, 0x9844)
        item['capture'] = {**common, 'memory_reads': [
            {'address': 0x5C352, 'size': 4, 'expect_hex': f'{x:04x}{y:04x}'}]}
        phases.append(item)
    phases.extend([phase('moved_idle', 0x5CA), phase('body_open', 0x27EA),
                   phase('body_capture_before_start', 0x6392, True),
                   phase('body_capture_after_start', 0x6396, True), phase('body_ready', 0x281E, True),
                   phase('body_inventory_ready', 0x28D4), phase('body_idle', 0x5CA),
                   phase('body_idle_release', 0x5CA), phase('body_restore_call', 0x27C0, True),
                   phase('body_restore_after_start', 0x640C, True), phase('following_clear_wait', 0x6478),
                   phase('closed_idle', 0x5CA), phase('closed_idle_release', 0x5CA),
                   phase('body_reopen', 0x27EA), phase('body_second_capture_before_start', 0x6392, True),
                   phase('body_second_capture_after_start', 0x6396, True),
                   phase('body_second_ready', 0x281E, True), phase('body_second_idle', 0x5CA)])
    events = []
    for i, (direction, _, _) in enumerate(route):
        events.append({'after_phase': 'anchor' if i == 0 else route_names[i-1],
                       'control': f'port1 {direction}', 'release_after_phase': route_names[i]})
    events.extend([
        {'after_phase': 'moved_idle', 'control': 'key 64', 'release_after_phase': 'body_open'},
        {'after_phase': 'body_idle_release', 'control': 'key 64', 'release_after_phase': 'body_restore_call'},
        {'after_phase': 'closed_idle_release', 'control': 'key 64', 'release_after_phase': 'body_reopen'}])
    return {'schema_version': 1, 'identifier': 'pandora-body-snapshot-directed-recapture',
            'target_id': build_scenario()['target_id'], 'direct_payload_contract': 'pandora',
            'phases': phases, 'input_events': events}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--stage', choices=['full', 'root', 'guards', 'body'], default='full')
    args = parser.parse_args()
    builder = {'full': build_scenario, 'root': build_guard_root,
               'guards': build_guard_scenario, 'body': build_body_scenario}[args.stage]
    args.output.write_text(json.dumps(builder(), indent=2)+'\n')


if __name__ == '__main__':
    main()
