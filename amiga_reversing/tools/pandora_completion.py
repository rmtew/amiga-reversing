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
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['lieutenant','commander'],default='lieutenant');p.add_argument('--cold',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps((lieutenant if a.stage=='lieutenant' else commander)(cold=a.cold),indent=2)+'\n')




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


if __name__=='__main__':main()
