"""Required Ochre trade, reached through normal engineering navigation.

The earlier model target above the patrol was blocked; use the floor below at
Y1606. IDs and health are read assertions. No guest state is injected.
"""
from .pandora_player import PlayerPlan,goal,PLAYER
from .pandora_completion import captain
import argparse
import json
from pathlib import Path

EXIT=[('down',[640,986]),('left',[591,986]),('right',[598,986]),
      ('down',[591,986]),('up',[591,954]),('left',[535,954]),
      ('down',[542,954]),('up',[542,934]),('left',[535,934])]
LEGS=[('down', [542, 934]), ('up', [542, 930]), ('left', [262, 930]), ('left', [164, 930]), ('right', [171, 930]), ('down', [164, 1086]), ('down', [164, 1166]), ('down', [164, 1226]), ('right', [339, 1226]), ('down', [332, 1226]), ('up', [332, 1170]), ('right', [612, 1170]), ('right', [640, 1170]), ('left', [633, 1170]), ('down', [640, 1242]), ('right', [703, 1242]), ('left', [696, 1242]), ('down', [703, 1242]), ('up', [703, 1202]), ('right', [878, 1202]), ('left', [871, 1202]), ('down', [878, 1262]), ('right', [1067, 1262]), ('left', [1060, 1262]), ('down', [1067, 1310]), ('right', [1200, 1310]), ('left', [1193, 1310]), ('down', [1200, 1358]), ('right', [1298, 1358]), ('left', [1291, 1358]), ('down', [1298, 1514]), ('down', [1298, 1594]), ('down', [1298, 1754]), ('left', [1067, 1754]), ('down', [1074, 1754]), ('up', [1074, 1658]), ('left', [794, 1658]), ('left', [787, 1658]), ('right', [794, 1658]), ('down', [787, 1658]), ('up', [787, 1642]), ('left', [549, 1642]), ('down', [556, 1642]), ('up', [556, 1606])]


def approach(*,cold=False):
    p=PlayerPlan(0x5D6,modal=False,xy=[647,986],held=48,expected_health=32)
    for i,(dr,xy) in enumerate(EXIT):p.move_to(f'exit_captain_{i}',dr,xy)
    p.action('inventory_open',0x2754,control='key 64').select('equip_engineer',50).close_inventory()
    for i,(dr,xy) in enumerate(LEGS):
        if i == 8:
            p.action('defence_staging',0x5D6)
            p.action('wait_defence_south',0x5D6,
                until={'address':0x5BAEC,'size':2,'expect_hex':'0500','expect_mask_hex':'ff00'},
                visits=1024,frames=1600)
        if i == 11:
            p.move_to('wackobrain_staging','right',[430,1170])
            p.action('patrol_staging',0x5D6)
            p.action('wait_wackobrain_south',0x5D6,
                until={'address':0x5BB40,'size':2,'expect_hex':'0500','expect_mask_hex':'ff00'},
                visits=1024,frames=1600)
        p.move_to(f'engineering_{i}',dr,xy);p.scenario['phases'][-1]['max_frames']=600
    complete_trade(p)
    for q in p.scenario['phases'][1:]:q['name']='oc_'+q['name']
    for e in p.scenario['input_events']:
        e['after_phase']='oc_'+e['after_phase'];e['release_after_phase']='oc_'+e['release_after_phase']
    if not cold:return p.scenario
    s=captain(cold=True);previous=s['phases'][-1]['name'];s['phases']+=p.scenario['phases'][2:]
    for e in p.scenario['input_events']:
        if e['after_phase']=='oc_anchor':e['after_phase']=previous
        s['input_events'].append(e)
    s['identifier']='pandora-required-ochre-approach';return s


def complete_trade(p,*,inventory_expected=bytes([48,50,49,38,0,0,33,35])):
    if len(inventory_expected)!=8:raise ValueError('Inventory profile must contain8 IDs')
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([0,147],'down').select('equip_sonicdriver',5).close_inventory()
    p.action('trade_staging',0x5D6)
    p.action('trade_sonicdriver_for_ochre',0x5D6,control='port1 fire',
        until=goal(PLAYER+22,bytes([36])),visits=1024,frames=2400)
    p.action('ochre_objective',0x5D6)
    reads=p.scenario['phases'][-1]['capture']['memory_reads']
    # Snapshot the actual mutation, independently of the player-held goal.
    # Original world_object_robomechanic tables: inventory $1B230, offers $1B370.
    p.scenario['phases'][-1]['capture']['memory_reads']=[r for r in reads
        if r.get('address') not in (0x3CB2,0x3CB6,0x3CA2,0x3CD4,0x39BC)]
    p.scenario['phases'][-1]['capture']['memory_reads'] += [
        goal(0x1B230,bytes([6,10,2,20,5,40,10,100])),
        goal(0x1B370,bytes([0,40,4,60,0,0,0,0])),goal(0x5B39E+70,bytes([5])),
        goal(0x3B92,inventory_expected),
        goal(PLAYER+22,bytes([36]))]
    return p


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cold',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.write_text(json.dumps(approach(cold=args.cold),indent=2)+'\n')


if __name__=='__main__':
    main()
