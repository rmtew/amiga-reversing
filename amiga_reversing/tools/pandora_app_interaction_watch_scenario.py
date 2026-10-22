"""Compose normal inventory/card-deposit observations for Pandora's app watches.

Normal keyboard/joystick inputs must satisfy the original interaction gates.
Use copperline_session to compile/run, with fresh owned local state directories.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .pandora_app_memory_watch_scenario import ROOT, BASE, AUDIT, APP_BASE


def capture():
    return {'registers': [f'd{i}' for i in range(8)] + [f'a{i}' for i in range(8)] + ['sr'],
            'memory_reads': [{'address': 0x5C352, 'size': 36},
                             {'address': APP_BASE + 0x196, 'size': 8},
                             {'address': APP_BASE + 0x2DA, 'size': 16},
                             {'address': APP_BASE + 0x214, 'size': 32},
                             {'address': APP_BASE + 0x2A6, 'size': 1},
                             {'address': APP_BASE + 0x22E, 'size': 2},
                             {'address': 0x591EE, 'size': 12},
                             {'address': APP_BASE + 0x2D4, 'size': 4},
                             {'address': APP_BASE + 0x368, 'size': 4},
                             {'address': 0x39BC, 'size': 1},
                             {'base_register': 'a7', 'offset': 0, 'size': 32}]}


def build_route():
    s = copy.deepcopy(json.loads(BASE.read_text()))
    s['identifier'] = 'pandora-inventory-card-store-retrieve-terminal-deposit'
    s['phases'] = s['phases'][:5]
    s['input_events'] = s['input_events'][:1]
    for p in s['phases'][1:]:p['capture'] = capture()

    def phase(name, offset, visits=None):
        p = {'name': name, 'breakpoint_stable_key': f's0:{offset:08X}:instruction',
             'wait_seconds': 60, 'capture': capture()}
        if visits is not None:p['occurrences'] = visits
        s['phases'].append(p)

    def hold(after, control, until):
        s['input_events'].append({'after_phase': after, 'control': control,
                                  'release_after_phase': until})

    phase('down_19_before_inventory', 0x9844, 19)
    hold('entry_officer_card_transferred', 'port1 down', 'down_19_before_inventory')
    for action, trigger in [('store', 'down_19_before_inventory'),
                            ('retrieve', 'store_inventory_closed')]:
        phase(f'{action}_player_inventory_open', 0x2754)
        hold(trigger, 'key 64', f'{action}_player_inventory_open')
        phase(f'{action}_inventory_ready', 0x28D4, 2)
        phase(f'{action}_selection_committed', 0x2AD0)
        hold(f'{action}_inventory_ready', 'port1 fire', f'{action}_selection_committed')
        phase(f'{action}_no_fire_services', 0x28D4, 2)
        phase(f'{action}_inventory_close_entry', 0x2778)
        hold(f'{action}_no_fire_services', 'key 64', f'{action}_inventory_close_entry')
        # A close-entry key release needs ordinary services to clear bit 3
        # before the next key press; an immediate reopen stays latched.
        phase(f'{action}_inventory_closed', 0x5D6, 3)
    phase('down_2_to_deposit_row', 0x9844, 2)
    hold('retrieve_inventory_closed', 'port1 down', 'down_2_to_deposit_row')
    phase('left_13_to_deposit', 0x9844, 13)
    hold('down_2_to_deposit_row', 'port1 left', 'left_13_to_deposit')
    phase('terminal_deposit_committed', 0x89E4)
    hold('left_13_to_deposit', 'port1 fire', 'terminal_deposit_committed')
    phase('terminal_deposit_feedback', 0x8A08)
    phase('post_deposit_main', 0x5D6)
    return s


def build_root(stage):
    if stage not in ('inventory', 'deposit'):
        raise ValueError('Choose inventory or deposit root')
    s = build_route()
    final = 'down_19_before_inventory' if stage == 'inventory' else 'left_13_to_deposit'
    end = next(i for i,p in enumerate(s['phases']) if p['name'] == final)
    s['phases'] = s['phases'][:end+1]
    names = {p['name'] for p in s['phases']}
    s['input_events'] = [e for e in s['input_events']
                         if e['after_phase'] in names and e['release_after_phase'] in names]
    s['identifier'] = f'pandora-{stage}-interaction-root'
    return s


def build_watch(stage, offset, length, *, resume=False):
    if stage not in ('inventory', 'deposit'):
        raise ValueError('Choose inventory or deposit interaction')
    gaps = json.loads(AUDIT.read_text())['gaps']
    allowed = {(g['start'], g['end'] - g['start']) for g in gaps} | {(0x2D4, 4), (0x368, 4)}
    if (offset, length) not in allowed:
        raise ValueError('Choose a published declaration gap or one of the two unresolved slots')
    s = build_route()
    if stage == 'inventory':
        # Key is released at the proven own-panel entry. Two no-fire services
        # precede the fire-triggered selection-call anchor.
        anchor = 'store_inventory_ready'
        s['phases'] = s['phases'][:next(i for i,p in enumerate(s['phases']) if p['name']==anchor)+1]
        # One ordinary no-fire service must clear the initial selection latch.
        # Source $28F4 is then the first selection call after fire polling.
        s['phases'].append({'name': 'watched_interaction',
            'breakpoint_stable_key': 's0:000028F4:instruction', 'wait_seconds': 60,
            'capture': capture()})
        names = {p['name'] for p in s['phases']}
        s['input_events'] = [e for e in s['input_events'] if e['after_phase'] in names and e['release_after_phase'] in names]
        s['input_events'].append({'after_phase':anchor, 'control':'port1 fire',
                                  'release_after_phase':'watched_interaction'})
    else:
        # At this point fire was pressed by the validated approach. Watch before
        # the storage scan/store, so a normal deposit can execute under the watch.
        cutoff = next(i for i,p in enumerate(s['phases']) if p['name']=='terminal_deposit_committed')
        s['phases'] = s['phases'][:cutoff]
        s['phases'].append({'name':'watched_interaction',
            'breakpoint_stable_key':'s0:000089D6:instruction', 'wait_seconds':60,
            'capture':capture()})
        names = {p['name'] for p in s['phases']}
        s['input_events'] = [e for e in s['input_events'] if e['after_phase'] in names and e['release_after_phase'] in names]
        s['input_events'].append({'after_phase':'left_13_to_deposit','control':'port1 fire',
                                  'release_after_phase':'watched_interaction'})
    # Input is released after the hook completes (and in finally on failure).
    # Inventory selection is latched; deposit clears the held ID before feedback.
    s['phases'][-1]['memory_access_watch'] = {
        'address': APP_BASE + offset, 'length': length, 'engine':'cpu', 'access':'access',
        'frames':120, 'wait_seconds':60}
    s['phases'][-1]['capture']['memory_reads'].append({'address':APP_BASE+offset,'size':min(64,length)})
    if resume:
        root = 'down_19_before_inventory' if stage == 'inventory' else 'left_13_to_deposit'
        begin = next(i for i,p in enumerate(s['phases']) if p['name'] == root)
        s['phases'] = [{'name':'verified_root','observable':'verified_checkpoint'}] + s['phases'][begin:]
        s['phases'][1]['occurrences'] = 1
        names = {p['name'] for p in s['phases']}
        s['input_events'] = [e for e in s['input_events']
                             if e['after_phase'] in names and e['release_after_phase'] in names]
    s['identifier'] = f'pandora-{stage}-app-{offset:03x}-{length}-watch'
    return s


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=('route','inventory-root','deposit-root','inventory','deposit'),default='route')
    p.add_argument('--resume',action='store_true',help='Compose a verified-checkpoint resume scenario')
    p.add_argument('--offset',type=lambda x:int(x,0))
    p.add_argument('--length',type=int)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.stage in ('inventory','deposit') and (a.offset is None or a.length is None):p.error('Watches require --offset and --length')
    if a.resume and a.stage not in ('inventory','deposit'):p.error('--resume requires a watch stage')
    if a.stage=='route':s=build_route()
    elif a.stage.endswith('-root'):s=build_root(a.stage.removesuffix('-root'))
    else:s=build_watch(a.stage,a.offset,a.length,resume=a.resume)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(s,indent=2)+'\n')


if __name__=='__main__':main()
