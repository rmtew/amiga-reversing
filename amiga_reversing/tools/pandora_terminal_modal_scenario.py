"""Validated northern-terminal approach, bounded CPU watches and normal exit.

Approach resumes the verified pre-inventory root. Watch/exit stages use separate
verified terminal checkpoints. Inputs never force guest memory or registers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pandora_app_interaction_watch_scenario import build_root, capture as interaction_capture
from .pandora_app_memory_watch_scenario import APP_BASE


def capture():
    c=interaction_capture()
    c['memory_reads']=[m for m in c['memory_reads']
        if m.get('address') not in (0x591EE,APP_BASE+0x2DA,0x39BC)]
    c['memory_reads'] += [
        {'address':APP_BASE+0x1B6,'size':24},
        {'address':APP_BASE+0x31A,'size':1},
        {'address':APP_BASE+0x2D8,'size':1},
        {'address':APP_BASE+0x27B,'size':15},
        {'address':0x5C72A,'size':26},
        {'address':0x39BC,'size':1},
        {'address':APP_BASE+0x2B6,'size':8},
    ]
    return c


def phase(name, offset, count=None):
    p={'name':name,'breakpoint_stable_key':f's0:{offset:08X}:instruction',
       'wait_seconds':60,'capture':capture()}
    if count is not None:p.update(occurrences=count,capture_first=True)
    return p


def build_approach(*, entry_root=False):
    root=build_root('inventory')
    anchor=phase('verified_inventory_position',0x9844,1)
    # Many roots stop at $9844. Require the actual live origin/held ID, rather
    # than admitting another position merely because its PC matches.
    read=next(m for m in anchor['capture']['memory_reads'] if m.get('address')==0x5C352)
    expected=bytearray(36);mask=bytearray(36)
    expected[:4]=bytes.fromhex('00f103ae');mask[:4]=b'\xff'*4
    expected[22]=0x36;mask[22]=0xff;mask[24]=2
    read.update(expect_hex=expected.hex(),expect_mask_hex=mask.hex())
    s={k:v for k,v in root.items() if k not in ('phases','input_events')}
    s['identifier']='pandora-northern-terminal-natural-entry'
    s['phases']=[{'name':'checkpoint','observable':'verified_checkpoint'},anchor]
    s['input_events']=[]
    previous=anchor['name']
    for name,direction,count in [('north_37','up',37),('east_44','right',44),
                                  ('north_to_opening','up',24),('through_opening','right',8),
                                  ('below_console','down',9)]:
        s['phases'].append(phase(name,0x9844,count))
        s['input_events'].append({'after_phase':previous,'control':'port1 '+direction,
                                  'release_after_phase':name})
        previous=name
    s['phases'].append(phase('terminal_modal_entry',0x8FF2))
    s['input_events'].append({'after_phase':previous,'control':'port1 right',
                              'release_after_phase':'terminal_modal_entry'})
    if not entry_root:s['phases'].append(phase('terminal_frame_service',0x9074))
    return s


def build_lifecycle():
    """Normal direction exit from the verified terminal frame-service root."""
    root=build_approach()
    s={k:v for k,v in root.items() if k not in ('phases','input_events')}
    s['identifier']='pandora-terminal-normal-direction-exit'
    s['phases']=[{'name':'checkpoint','observable':'verified_checkpoint'},
                  phase('terminal_anchor',0x9074,1),
                  phase('exit_direction_seen',0x9088),
                  phase('world_context_restored',0x90B0),
                  phase('world_main_return',0x5D6)]
    s['input_events']=[{'after_phase':'terminal_anchor','control':'port1 down',
                        'release_after_phase':'exit_direction_seen'}]
    return s


def build_watch(stage,offset,length):
    from .pandora_app_memory_watch_scenario import AUDIT
    allowed={(g['start'],g['end']-g['start']) for g in json.loads(AUDIT.read_text())['gaps']}|{(0x2D4,4),(0x368,4)}
    if (offset,length) not in allowed or stage not in ('entry','inventory-open'):
        raise ValueError('Choose entry/inventory-open and a published gap or unresolved slot')
    if stage=='entry':
        s=build_approach(entry_root=True)
        s['phases']=[{'name':'checkpoint','observable':'verified_checkpoint'},
                      phase('watched_modal_entry',0x8FF2,1)]
        s['input_events']=[]
    else:
        s=build_lifecycle()
        s['phases']=s['phases'][:2]+[phase('watched_modal_inventory_open',0x9078)]
        s['input_events']=[{'after_phase':'terminal_anchor','control':'key 64',
                            'release_after_phase':'watched_modal_inventory_open'}]
    s['identifier']=f'pandora-terminal-{stage}-app-{offset:03x}-watch'
    s['phases'][-1]['memory_access_watch']={'address':APP_BASE+offset,'length':length,
        'engine':'cpu','access':'access','frames':120,'wait_seconds':60}
    s['phases'][-1]['capture']['memory_reads'].append({'address':APP_BASE+offset,'size':min(length,64)})
    return s


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=('approach','entry-root','lifecycle','entry','inventory-open'),default='approach')
    p.add_argument('--offset',type=lambda s:int(s,0));p.add_argument('--length',type=int)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.stage in ('entry','inventory-open') and (a.offset is None or a.length is None):p.error('Watch stages require --offset and --length')
    if a.stage=='lifecycle':s=build_lifecycle()
    elif a.stage in ('entry','inventory-open'):s=build_watch(a.stage,a.offset,a.length)
    else:s=build_approach(entry_root=a.stage=='entry-root')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(s,indent=2)+'\n')


if __name__=='__main__':main()
