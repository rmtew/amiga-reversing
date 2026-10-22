"""Normal-input AWOL card acquisition; initial values assert the Ochre root."""
from .pandora_player import PlayerPlan,goal,PLAYER
from .pandora_ochre import approach as ochre
import argparse
import json
from pathlib import Path
LEGS=[('down',[556,1642]),('right',[780,1642]),('left',[773,1642]),
      ('down',[780,1694]),('right',[885,1694]),('down',[878,1770]),
      ('right',[927,1770]),('left',[920,1770]),('down',[927,1770]),
      ('up',[927,1746]),('right',[934,1746])]

def acquire(*,cold=False):
    p=PlayerPlan(0x5D6,modal=False,xy=[556,1606],held=36,expected_health=32)
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([96,139],'right').select('store_ochre',0)
    p.cursor_to([0,139],'left').cursor_to([0,147],'down').select('equip_engineer',50).close_inventory()
    for i,(direction,xy) in enumerate(LEGS):
        if i==4:
            p.action('kwik_kleen_staging',0x5D6)
            p.action('wait_kwik_kleen_east',0x5D6,
                until={'address':0x5BBE6,'size':4,'expect_hex':'04000694','expect_mask_hex':'ff00ffff'},
                visits=1024,frames=1600)
        p.move_to(f'awol_approach_{i}',direction,xy)
    # Proximity selection can alternate; catch the actual body owner AFTER
    # its update, before the next inventory-key service uses that pointer.
    p.action('body_context_ready',0x5EA,
        until=goal(0x3B9A,(0x5AA7E).to_bytes(4,'big')),visits=64,frames=180)
    p.action('inventory_open',0x27EA,control='key 64').select('take_awol',55)
    p.cursor_to([192,147],'down').cursor_to([96,147],'left').select('store_awol',0)
    p.cursor_to([192,147],'right').cursor_to([192,139],'up').select('retrieve_engineer',50).close_inventory()
    p.action('awol_objective',0x5D6)
    reads=p.scenario['phases'][-1]['capture']['memory_reads']
    reads += [goal(PLAYER+22,bytes([50])),goal(0x3B92,bytes([48,0,49,38,36,55,33,35]))]
    for q in p.scenario['phases'][1:]:q['name']='aw_'+q['name']
    for e in p.scenario['input_events']:
        e['after_phase']='aw_'+e['after_phase'];e['release_after_phase']='aw_'+e['release_after_phase']
    if not cold:return p.scenario
    s=ochre(cold=True);previous=s['phases'][-1]['name'];s['phases']+=p.scenario['phases'][2:]
    for e in p.scenario['input_events']:
        if e['after_phase']=='aw_anchor':e['after_phase']=previous
        s['input_events'].append(e)
    s['identifier']='pandora-required-awol-card';return s


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cold',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.write_text(json.dumps(acquire(cold=args.cold),indent=2)+'\n')


if __name__=='__main__':main()
