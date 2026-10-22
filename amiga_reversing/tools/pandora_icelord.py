"""Bounded original-input approach from the sonicdriver checkpoint to Icelord.

Terrain-model waypoints are candidates until validated live. No actor/state
writes or routine calls are used. Reuses the existing state-aware player.
"""
from .pandora_player import PlayerPlan,walkthrough

# Existing terrain/pose model, staged below the Icelord rather than in the wall
# west of it. Short turn reversals accommodate original geometry-origin drift.
LEGS=[('up',[633,730]),('left',[591,730]),('right',[598,730]),
      ('down',[591,730]),('up',[591,698]),('left',[542,698]),
      ('right',[549,698]),('down',[542,698]),('up',[542,650]),
      ('left',[500,650]),('right',[507,650]),('down',[500,650]),
      ('up',[500,410]),('up',[500,314]),('right',[920,314]),
      ('right',[969,314]),('down',[962,314]),('up',[962,230]),
      ('right',[1305,230])]


def approach(*, after_first_step=False, cold=False):
    xy=[633,734] if after_first_step else [640,734]
    p=PlayerPlan(0x9844 if after_first_step else 0x5D6,modal=False,xy=xy,held=5)
    if not after_first_step:p.move_to('icelord_initial_turn','up',[633,734])
    for i,(direction,target) in enumerate(LEGS):
        p.move_to(f'icelord_waypoint_{i}',direction,target)
        p.scenario['phases'][-1]['max_frames']=600
    p.scenario['identifier']='pandora-icelord-approach'
    if not cold:return p.scenario
    s=walkthrough(provision=True)
    s['phases']+=p.scenario['phases'][2:]
    for e in p.scenario['input_events']:
        s['input_events'].append(dict(e,after_phase='world_main' if e['after_phase']=='anchor' else e['after_phase']))
    s['identifier']='pandora-cold-boot-icelord-approach'
    return s


def fight():
    from .pandora_player import goal,PLAYER,HEADER
    p=PlayerPlan(0x9844,modal=False,xy=[1305,230],held=5)
    actor=0x59D7A
    def combat(name,pc,**kwargs):
        p.action(name,pc,guard=False,**kwargs)
        reads=p.scenario['phases'][-1]['capture']['memory_reads']
        reads[:]=[r for r in reads if r.get('address') not in (0x39BC,0x3D16,0x3CD4)]
        carried=next(r for r in reads if r.get('address')==0x3B92)
        carried.update(expect_hex='32'+'00'*7,expect_mask_hex='ff'+'00'*7)
        reads += [{'address':actor+48,'size':36},{'address':0x3CAA,'size':10},
                  {'address':0x3B9E,'size':4,'expect_hex':'00059d7a'},
                  {'address':PLAYER+24,'size':1,'expect_hex':'00','expect_mask_hex':'02'},
                  goal(PLAYER+22,b'\x05'),goal(HEADER+8,bytes.fromhex('00004000005a0081'))]
    combat('sonicdriver_override',0x7854,control='port1 up',frames=120)
    for n,hp in enumerate([75,55,35,15,None],1):
        combat(f'charge_{n}',0x7938,until=goal(0x3CAA,b'\x00\x18'),visits=64,frames=180)
        if hp is not None:
            combat(f'sonicdriver_hit_{n}',0x7938,control='port1 fire',
                   until=goal(actor+60,hp.to_bytes(2,'big')),visits=16,frames=60)
        else:
            combat('icelord_defeated_world',0x5D6,control='port1 fire',
                   until={'address':actor+72,'size':1,'expect_hex':'02','expect_mask_hex':'02'},
                   visits=16,frames=120)
    p.scenario['identifier']='pandora-sonicdriver-icelord-fight'
    return p.scenario


def cold_fight():
    s=approach(cold=True)
    # These no-input phases are redundant for this objective. Release events
    # still happen at their original close/selection hooks; rewrite only the
    # following press anchor, not elapsed frame counts or guest state.
    for name in ['terminal_card_displayed','terminal_noncard_display','released_close_key']:
        i=next(i for i,p in enumerate(s['phases']) if p['name']==name)
        previous=s['phases'][i-1]['name'];s['phases'].pop(i)
        for e in s['input_events']:
            if e['after_phase']==name:e['after_phase']=previous
            if e['release_after_phase']==name:raise ValueError('Cannot drop an input release hook')
    final=s['phases'][-1]['name'];f=fight()
    s['phases']+=f['phases'][2:]
    s['input_events'] += [dict(e,after_phase=final if e['after_phase']=='anchor' else e['after_phase']) for e in f['input_events']]
    s['identifier']='pandora-cold-boot-sonicdriver-defeats-icelord'
    return s


def main():
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['approach','fight','cold-fight'],default='cold-fight')
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    s={'approach':approach,'fight':fight,'cold-fight':cold_fight}[a.stage]()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(s,indent=2)+'\n')


if __name__=='__main__':main()
