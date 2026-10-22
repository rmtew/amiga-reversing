"""Required-item route toward Pandora's SDI ending, omitting optional Icelord.

Next dependency: preserve Engineer/sonicdriver and acquire Lt Commander ID.
Waypoint candidates require live validation; see the target plan's G01..G08.
"""
from .pandora_player import PlayerPlan,walkthrough,goal,PLAYER

LEGS=[('up',[633,730]),('left',[591,730]),('right',[598,730]),
      ('down',[591,730]),('up',[591,698]),('left',[535,698]),
      ('down',[542,698]),('up',[542,650]),('left',[493,650]),
      ('down',[500,650]),('up',[500,410]),('up',[500,170]),
      ('up',[500,114]),('left',[381,114]),('down',[388,162])]


def lieutenant(*,cold=False):
    p=PlayerPlan(0x5D6,modal=False,xy=[640,734],held=5)
    p.move_to('initial_turn','up',[633,734])
    for i,(direction,xy) in enumerate(LEGS):
        p.move_to(f'waypoint_{i}',direction,xy);p.scenario['phases'][-1]['max_frames']=600
    p.inventory_open().cursor_to([192,147],'down').cursor_to([0,147],'left')
    p.select('store_sonicdriver',0).cursor_to([192,147],'right').cursor_to([192,155],'down')
    p.select('take_lieutenant_id',49).close_inventory()
    p.action('objective',0x5D6)
    p.scenario['phases'][-1]['capture']['memory_reads'] += [goal(PLAYER+22,b'\x31'),goal(0x3B92,b'\x32\x05')]
    # Namespace reused actions so a continuous route has unique hooks.
    s=p.scenario
    for phase in s['phases'][1:]:phase['name']='lc_'+phase['name']
    for e in s['input_events']:
        e['after_phase']='lc_'+e['after_phase'];e['release_after_phase']='lc_'+e['release_after_phase']
    if not cold:return s
    prefix=walkthrough(provision=True)
    s['input_events'][0]['after_phase']='world_main'
    prefix['phases']+=s['phases'][2:]
    prefix['input_events']+=s['input_events']
    prefix['identifier']='pandora-completion-lieutenant-id'
    return prefix


def main():
    import argparse,json
    from pathlib import Path
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['lieutenant','commander','captain'],default='lieutenant');p.add_argument('--cold',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'lieutenant':lieutenant,'commander':commander,'captain':captain}[a.stage](cold=a.cold),indent=2)+'\n')




def commander(*,codes=True,cold=False):
    p=PlayerPlan(0x5D6,modal=False,xy=[388,162],held=49)
    for i,(dr,xy) in enumerate([('up',[388,114]),('left',[108,114]),('down',[115,202]),('right',[199,202]),('down',[192,202]),('up',[192,190])]):
        p.move_to(f'commander_waypoint_{i}',dr,xy);p.scenario['phases'][-1]['max_frames']=600
    p.action('inventory_open',0x27EA,control='key 64').select('take_commander_id',48)
    if codes:
        p.cursor_to([192,155],'down').cursor_to([0,155],'left').select('store_commander_id',0)
        p.cursor_to([192,155],'right').select('take_blue',33)
        p.cursor_to([96,155],'left').select('store_blue',0)
        p.cursor_to([192,155],'right').cursor_to([192,163],'down').select('take_scarlet',35)
        p.cursor_to([96,163],'left').select('store_scarlet',0)
        p.cursor_to([0,163],'left').cursor_to([0,155],'up').select('retrieve_commander_id',48)
    p.close_inventory()
    p.action('commander_objective',0x5D6)
    p.scenario['phases'][-1]['capture']['memory_reads'].append(goal(PLAYER+22,b'\x30'))
    if codes:
        pocket=next(r for r in p.scenario['phases'][-1]['capture']['memory_reads'] if r.get('address')==0x3B92)
        pocket.update(expect_hex='3205000000002123',expect_mask_hex='ffffffffffffffff')
    for q in p.scenario['phases'][1:]:q['name']='cm_'+q['name']
    for e in p.scenario['input_events']:
        e['after_phase']='cm_'+e['after_phase'];e['release_after_phase']='cm_'+e['release_after_phase']
    if not cold:return p.scenario
    prefix=lieutenant(cold=True)
    final=prefix['phases'][-1]['name'];prefix['phases']+=p.scenario['phases'][2:]
    for e in p.scenario['input_events']:
        if e['after_phase']=='cm_anchor':e['after_phase']=final
        prefix['input_events'].append(e)
    prefix['identifier']='pandora-required-commander-and-code-cards'
    return prefix




def captain(*,cold=False):
    p=PlayerPlan(0x5D6,modal=False,xy=[192,190],held=48)
    legs=[('down',[192,210]),('left',[108,210]),('down',[115,446]),
          ('down',[115,542]),('right',[500,542]),('left',[493,542]),
          ('down',[500,686]),('right',[542,686]),('left',[535,686]),
          ('down',[542,842]),('down',[542,922]),('down',[542,954]),('right',[591,954]),
          ('left',[584,954]),('down',[591,986]),('right',[647,986])]
    # Exact-card gates are directional route obligations. Leave this area
    # holding Lt Commander, then retrieve Commander outside its gate.
    p.action('inventory_open',0x27EA,control='key 64')
    p.cursor_to([192,155],'down').cursor_to([0,155],'left').select('store_commander_for_exit',0)
    p.cursor_to([192,155],'right').cursor_to([192,139],'up').select('retrieve_lieutenant',49)
    p.close_inventory()
    p.move_to('leave_body_row','down',[192,210]).move_to('leave_lieutenant_gate','left',[108,210])
    p.move_to('clear_lieutenant_gate','down',[115,370]).move_to('corridor_midpoint','down',[115,446])
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([0,155],'down').select('switch_to_commander_outside_gate',48).close_inventory()
    p.move_to('before_thief','down',[115,542])
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([0,163],'down').select('protect_commander_from_thief',0).close_inventory()
    p.move_to('cross_thief_patrol_1','right',[395,542]).move_to('cross_thief_patrol_2','right',[500,542])
    p.move_to('turn_below_thief','left',[493,542]).move_to('outside_thief_y_range','down',[500,550])
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([0,163],'down').select('retrieve_commander_after_thief',48).close_inventory()
    p.action('hooligan_encounter',0x7792,control='port1 down',frames=180)
    f=hooligan_fight()
    p.scenario['phases']+=f['phases'][2:]
    p.scenario['input_events']+=f['input_events']
    p.expected_health=32
    finish_captain(p)
    for q in p.scenario['phases'][1:]:q['name']='cp_'+q['name']
    for e in p.scenario['input_events']:
        e['after_phase']='cp_'+e['after_phase'];e['release_after_phase']='cp_'+e['release_after_phase']
    if not cold:return p.scenario
    s=commander(cold=True);previous=s['phases'][-1]['name'];s['phases']+=p.scenario['phases'][2:]
    for e in p.scenario['input_events']:
        if e['after_phase']=='cp_anchor':e['after_phase']=previous
        s['input_events'].append(e)
    s['identifier']='pandora-required-sdi-disk';return s


def hooligan_fight():
    """Resume the verified naturally reached combat-entry checkpoint."""
    actor=0x5A028
    p=PlayerPlan(0x7792,modal=False,xy=[500,606],held=48)
    def combat(name,pc,**kwargs):
        p.action(name,pc,guard=False,**kwargs)
        reads=p.scenario['phases'][-1]['capture']['memory_reads']
        reads[:]=[r for r in reads if r.get('address') not in (0x39BC,0x3D16,0x3CD4)]
        reads += [{'address':actor+48,'size':36},{'address':0x3CAA,'size':10},
                  {'address':0x3B9E,'size':4,'expect_hex':'0005a028'},
                  {'address':PLAYER+24,'size':1,'expect_hex':'00','expect_mask_hex':'02'},
                  goal(PLAYER+22,b'\x30'),goal(0x3BBA,bytes.fromhex('00004000005a0081'))]
    combat('hooligan_configured',0x7938)
    for n in range(1,13):
        combat(f'hooligan_charge_{n}',0x7938,until=goal(0x3CAA,b'\x00\x18'),visits=64,frames=240)
        if n<12:
            combat(f'hooligan_hit_{n}',0x7938,control='port1 fire',
                until=goal(actor+60,(60-n*5).to_bytes(2,'big')),visits=16,frames=90)
        else:
            combat('hooligan_defeated_world',0x5D6,control='port1 fire',
                until={'address':actor+72,'size':1,'expect_hex':'02','expect_mask_hex':'02'},visits=16,frames=120)
    return p.scenario


def finish_captain(p,*,skip_central_shaft=False,pocket_disk=False,inventory_expected=None):
    if not skip_central_shaft:p.move_to('central_shaft','down',[500,686])
    for i,(dr,xy) in enumerate([('right',[542,686]),('left',[535,686]),('down',[542,842]),('down',[542,922]),('down',[542,954]),('right',[591,954]),('left',[584,954]),('down',[591,986]),('right',[647,986])]):
        p.move_to(f'waypoint_{i}',dr,xy);p.scenario['phases'][-1]['max_frames']=600
    p.action('inventory_open',0x27EA,control='key 64')
    p.cursor_to([192,147],'down').select('take_sdi_disk',38)
    if pocket_disk:
        p.cursor_to([96,147],'left').cursor_to([96,139],'up').select('store_sdi_disk',0)
        p.cursor_to([192,139],'right').cursor_to([192,147],'down').select('retrieve_commander',48)
    else:
        p.cursor_to([0,147],'left').cursor_to([0,163],'down').select('store_sdi_disk',0)
        p.cursor_to([192,163],'right').cursor_to([192,147],'up').select('retrieve_commander',48)
    p.close_inventory().action('objective',0x5D6)
    final=p.scenario['phases'][-1]
    final['capture']['memory_reads'].append(goal(PLAYER+22,b'\x30'))
    ids=next(r for r in final['capture']['memory_reads'] if r.get('address')==0x3B92)
    expected=inventory_expected if inventory_expected is not None else bytes.fromhex('3205312600002123')
    if len(expected)!=8:raise ValueError('Captain inventory profile must contain8 IDs')
    ids.update(expect_hex=expected.hex(),expect_mask_hex='ffffffffffffffff')
    return p


def captain_resume():
    p=PlayerPlan(0x5D6,modal=False,xy=[500,606],held=48,expected_health=32)
    finish_captain(p)
    return p.scenario


if __name__=='__main__':main()
