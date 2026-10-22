"""Reach and leave the original self-destruct console without submitting items."""
from .pandora_player import PlayerPlan,goal,PLAYER
from .pandora_awol import acquire

LEGS=[('up',[927,1746]),('down',[927,1770]),('left',[871,1770]),
      ('down',[878,1770]),('up',[878,1658]),('left',[787,1658]),
      ('right',[794,1658]),('down',[787,1658]),('up',[787,1650]),
      ('left',[507,1650]),('left',[395,1650]),('down',[402,1770]),
      ('right',[486,1770]),('down',[479,1770]),('up',[479,1746]),
      ('up',[479,1706]),('right',[500,1706])]


def inspect_console(*,cold=False):
    p=PlayerPlan(0x5D6,modal=False,xy=[934,1746],held=50,expected_health=32)
    p.action('wait_kwik_kleen_east',0x5D6,
        until={'address':0x5BBE6,'size':4,'expect_hex':'04000694','expect_mask_hex':'ff00ffff'},
        visits=1024,frames=1600)
    for i,(direction,xy) in enumerate(LEGS):p.move_to(f'console_approach_{i}',direction,xy)
    p.action('console_entry',0x9C00,control='port1 right')
    p.modal=True
    p.action('console_ready_unarmed',0x9C88)
    p.scenario['phases'][-1]['capture']['memory_reads'] += [goal(0x3D27,b'\x00'),{'address':0x3C82,'size':2}]
    p.action('leave_console_unarmed',0x9C9C,control='port1 down')
    p.modal=False
    p.action('world_context_restored',0x9CBC).action('world_main_unarmed',0x5D6)
    reads=p.scenario['phases'][-1]['capture']['memory_reads']
    reads[:]=[r for r in reads if r.get('address') not in (0x3D16,0x3CA2)]
    reads += [goal(0x3D27,b'\x00'),goal(PLAYER+22,bytes([50])),
              goal(PLAYER,bytes.fromhex('020206aa')),goal(PLAYER+27,b'\x08')]
    next(r for r in reads if r.get('address')==0x3B92).update(expect_hex='3000312624372123')
    for q in p.scenario['phases'][1:]:q['name']='cs_'+q['name']
    for e in p.scenario['input_events']:
        e['after_phase']='cs_'+e['after_phase'];e['release_after_phase']='cs_'+e['release_after_phase']
    if not cold:return p.scenario
    s=acquire(cold=True);previous=s['phases'][-1]['name'];s['phases']+=p.scenario['phases'][2:]
    for e in p.scenario['input_events']:
        if e['after_phase']=='cs_anchor':e['after_phase']=previous
        s['input_events'].append(e)
    s['identifier']='pandora-unarmed-console-inspection';return s
