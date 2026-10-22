"""Early Icelord return-route prerequisite, before consuming sonicdriver."""
from .pandora_player import PlayerPlan,goal,PLAYER
from .pandora_icelord import fight
from .pandora_completion import commander

ICELORD_LEGS=[('up', [115, 306]), ('right', [395, 306]), ('right', [535, 306]), ('right', [682, 306]), ('left', [675, 306]), ('down', [682, 314]), ('right', [962, 314]), ('right', [969, 314]), ('down', [962, 314]), ('up', [962, 230]), ('right', [1242, 230]), ('right', [1305, 230])]


def early_icelord(*,cold=False):
    p=PlayerPlan(0x5D6,modal=False,xy=[115,446],held=49,expected_health=95)
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([0,147],'down').select('equip_sonicdriver',5).close_inventory()
    for i,(direction,xy) in enumerate(ICELORD_LEGS):
        p.move_to(f'early_icelord_{i}',direction,xy);p.scenario['phases'][-1]['max_frames']=600
    # Final geometry/root is the existing qualified Sonicdriver combat case.
    f=fight();previous=p.scenario['phases'][-1]['name']
    p.scenario['phases']+=f['phases'][2:]
    for event in f['input_events']:
        if event['after_phase']=='anchor':event['after_phase']=previous
        p.scenario['input_events'].append(event)
    p.expected_health=70
    p.action('early_icelord_result',0x5D6)
    reads=p.scenario['phases'][-1]['capture']['memory_reads']
    reads[:]=[r for r in reads if r.get('address') not in (0x3D16,0x3CA2,0x3CB2)]
    reads += [goal(PLAYER+22,b'\x05'),goal(0x3B92,bytes.fromhex('3231300000002123')),{'address':0x59D7A,'size':64},{'address':0x59DBA,'size':20}]
    for q in p.scenario['phases'][1:]:q['name']='ei_'+q['name']
    for event in p.scenario['input_events']:
        event['after_phase']='ei_'+event['after_phase'];event['release_after_phase']='ei_'+event['release_after_phase']
    if not cold:return p.scenario
    s=gate_exit(cold=True);previous=s['phases'][-1]['name'];s['phases']+=p.scenario['phases'][2:]
    for event in p.scenario['input_events']:
        if event['after_phase']=='ei_anchor':event['after_phase']=previous
        s['input_events'].append(event)
    s['identifier']='pandora-early-icelord-return-prerequisite';return s


def gate_exit(*,cold=False):
    from .pandora_completion import captain
    s=captain();j=next(i for i,q in enumerate(s['phases']) if q['name']=='cp_corridor_midpoint');s['phases']=s['phases'][:j+1]
    names={q['name'] for q in s['phases']};s['input_events']=[e for e in s['input_events'] if e['after_phase'] in names and e['release_after_phase'] in names]
    p=PlayerPlan(0x5D6,modal=False,xy=[115,446],held=49,expected_health=95);p.action('gate_exit_root',0x5D6)
    reads=p.scenario['phases'][-1]['capture']['memory_reads'];reads += [goal(PLAYER,bytes.fromhex('007301be')),goal(PLAYER+22,bytes([49]))]
    next(r for r in reads if r.get('address')==0x3B92).update(expect_hex='3205300000002123')
    s['phases'].append(p.scenario['phases'][-1])
    if not cold:return s
    prefix=commander(cold=True);previous=prefix['phases'][-1]['name'];prefix['phases']+=s['phases'][2:]
    for event in s['input_events']:
        if event['after_phase']=='cp_anchor':event['after_phase']=previous
        prefix['input_events'].append(event)
    return prefix


def loot_icelord():
    p=PlayerPlan(0x5D6,modal=False,xy=[1298,206],held=5,expected_health=70)
    p.move_to('icelord_body_row','up',[1298,190])
    p.action('icelord_body_ready',0x5EA,until=goal(0x3B9A,(0x59D7A).to_bytes(4,'big')),visits=64,frames=180)
    p.action('inventory_open',0x27EA,control='key 64')
    p.cursor_to([192,147],'down').select('take_thermolance',11)
    p.cursor_to([0,147],'left').cursor_to([0,163],'down').select('carry_thermolance',0)
    p.cursor_to([192,163],'right').cursor_to([192,147],'up').select('recover_sonicdriver',5).close_inventory()
    p.action('weapon_retained',0x5D6)
    reads=p.scenario['phases'][-1]['capture']['memory_reads']
    reads += [goal(PLAYER+22,b'\x05'),goal(0x3B92,bytes.fromhex('3231300b00002123'))]
    for q in p.scenario['phases'][1:]:q['name']='il_'+q['name']
    for e in p.scenario['input_events']:
        e['after_phase']='il_'+e['after_phase'];e['release_after_phase']='il_'+e['release_after_phase']
    return p.scenario


RETURN_LEGS=[('down', [1298, 218]), ('left', [1018, 218]), ('left', [962, 218]), ('right', [969, 218]), ('down', [962, 314]), ('left', [682, 314]), ('left', [542, 314]), ('left', [479, 314]), ('right', [486, 314]), ('down', [479, 470]), ('down', [479, 514]), ('left', [199, 514]), ('left', [108, 514]), ('down', [115, 542])]


def prepare_hooligan():
    p=PlayerPlan(0x5D6,modal=False,xy=[1298,190],held=5,expected_health=70)
    for i,(direction,xy) in enumerate(RETURN_LEGS):
        p.move_to(f'return_from_icelord_{i}',direction,xy);p.scenario['phases'][-1]['max_frames']=600
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([0,147],'down').select('restore_sonicdriver_storage',49)
    p.cursor_to([0,155],'down').select('restore_commander_holding',48)
    p.cursor_to([0,139],'up').cursor_to([96,139],'right').select('protect_commander_in_pocket',0).close_inventory()
    p.move_to('thief_cross_1','right',[395,542]).move_to('thief_cross_2','right',[500,542])
    p.move_to('below_thief_turn','left',[493,542]).move_to('outside_thief_range','down',[500,550])
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([0,163],'down').select('equip_thermolance',11).close_inventory()
    # Original script source$1CD4 pauses50 ticks at485620. Require48..50
    # remaining, HP60 and active before the short approach; no guest writes.
    expected=bytearray(25);mask=bytearray(25)
    expected[:4]=bytes.fromhex('01e5026c');mask[:4]=b'\xff'*4
    expected[12:14]=b'\x00\x3c';mask[12:14]=b'\xff\xff'
    expected[20:22]=b'\x00\x30';mask[20:22]=b'\xff\xf0';mask[24]=2
    p.action('wait_hooligan_pause',0x5D6,
        until={'address':0x5A058,'size':25,'expect_hex':expected.hex(),'expect_mask_hex':mask.hex()},
        visits=1024,frames=2400)
    p.action('natural_hooligan_entry',0x7792,control='port1 down',frames=180)
    p.scenario['phases'][-1]['capture']['memory_reads'].append(goal(PLAYER,bytes.fromhex('01f4025e')))
    for q in p.scenario['phases'][1:]:q['name']='rh_'+q['name']
    for e in p.scenario['input_events']:
        e['after_phase']='rh_'+e['after_phase'];e['release_after_phase']='rh_'+e['release_after_phase']
    return p.scenario


def thermolance_hooligan():
    actor=0x5A028
    p=PlayerPlan(0x7792,modal=False,xy=[500,606],held=11,expected_health=70)
    def combat(name,pc,**kwargs):
        p.action(name,pc,guard=False,**kwargs)
        reads=p.scenario['phases'][-1]['capture']['memory_reads']
        reads[:]=[r for r in reads if r.get('address') not in (0x39BC,0x3D16,0x3CD4)]
        reads += [{'address':actor+48,'size':36},{'address':0x3CAA,'size':10},
                  goal(0x3B9E,actor.to_bytes(4,'big')),
                  {'address':PLAYER+24,'size':1,'expect_hex':'00','expect_mask_hex':'02'},
                  goal(PLAYER+22,b'\x0b'),goal(0x3BBA,bytes.fromhex('00004000005a0081'))]
    combat('thermolance_configured',0x7938)
    for n,hp in enumerate([35,10,None],1):
        combat(f'thermolance_charge_{n}',0x7938,until=goal(0x3CAA,b'\x00\x18'),visits=64,frames=240)
        if hp is not None:
            combat(f'thermolance_hit_{n}',0x7938,control='port1 fire',until=goal(actor+60,hp.to_bytes(2,'big')),visits=16,frames=90)
        else:
            combat('thermolance_hooligan_defeated',0x5D6,control='port1 fire',until={'address':actor+72,'size':1,'expect_hex':'02','expect_mask_hex':'02'},visits=16,frames=120)
    return p.scenario


def revised_captain():
    from .pandora_completion import finish_captain
    p=PlayerPlan(0x5D6,modal=False,xy=[500,606],held=11,expected_health=49)
    p.move_to('clear_hooligan_body','down',[500,686])
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([0,163],'down').select('store_thermolance',0)
    p.cursor_to([0,139],'up').cursor_to([96,139],'right').select('recover_commander',48).close_inventory()
    finish_captain(p,skip_central_shaft=True,pocket_disk=True,inventory_expected=bytes.fromhex('3205310b26002123'))
    for q in p.scenario['phases'][1:]:q['name']='rc_'+q['name']
    for e in p.scenario['input_events']:
        e['after_phase']='rc_'+e['after_phase'];e['release_after_phase']='rc_'+e['release_after_phase']
    return p.scenario


NORTH_CORRIDOR_LEGS=[('left', [528, 934]), ('right', [535, 934]), ('down', [528, 934]), ('up', [528, 774]), ('up', [528, 694]), ('up', [528, 646]), ('left', [493, 646]), ('down', [500, 646]), ('up', [500, 550])]


def revised_ochre():
    from .pandora_ochre import EXIT,complete_trade
    p=PlayerPlan(0x5D6,modal=False,xy=[647,986],held=48,expected_health=49)
    for i,(direction,xy) in enumerate(EXIT):p.move_to(f'captain_exit_{i}',direction,xy)
    p.action('inventory_open',0x2754,control='key 64').select('equip_engineer',50).close_inventory()
    # The narrow northbound corridor passed live, but leftward Y550 did
    # not. Cross Thief empty-handed to the already-proved Y514 corridor.
    for i,(direction,xy) in enumerate(NORTH_CORRIDOR_LEGS):
        p.move_to(f'to_top_shaft_{i}',direction,xy);p.scenario['phases'][-1]['max_frames']=600
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([96,139],'right').cursor_to([96,147],'down').select('protect_engineer',0).close_inventory()
    p.move_to('north_thief_empty','up',[500,514])
    p.move_to('north_thief_clear_1','left',[220,514]).move_to('north_thief_clear_2','left',[115,514])
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([96,139],'right').cursor_to([96,147],'down').select('recover_engineer',50).close_inventory()
    p.move_to('left_shaft_align','right',[122,514]).move_to('left_shaft_vertical','up',[115,514])
    p.move_to('left_shaft_up_1','up',[115,354]).move_to('left_shaft_up_2','up',[115,306])
    for i,(direction,xy) in enumerate(ICELORD_LEGS[1:]):
        p.move_to(f'known_upper_corridor_{i}',direction,xy);p.scenario['phases'][-1]['max_frames']=600
    p.move_to('top_shaft_vertical','up',[1298,230])
    p.move_to('top_shaft_up_1','up',[1298,70]).move_to('top_shaft_up_2','up',[1298,30])
    p.move_to('top_align_right','right',[1305,30]).move_to('top_align_left','left',[1298,30])
    p.action('camera_wrap_to_bottom',0x9930,control='port1 up',frames=180)
    p.scenario['phases'][-1]['capture']['memory_reads'].append(goal(PLAYER,bytes.fromhex('051907e0')))
    p.action('bottom_world',0x5D6)
    p.move_to('bottom_align_left','left',[1298,2016]).move_to('bottom_align_right','right',[1305,2016])
    p.move_to('bottom_vertical_align','up',[1298,2016])
    p.move_to('right_shaft_midpoint','up',[1298,1856]).move_to('engineering_door_row','up',[1298,1752])
    expected=bytearray(25);mask=bytearray(25)
    expected[:4]=bytes.fromhex('03600750');mask[:4]=bytes.fromhex('fff0fff0')
    expected[12:14]=(95).to_bytes(2,'big');mask[12:14]=b'\xff\xff';mask[24]=2
    p.action('wait_kwik_bottom_left',0x5D6,until={'address':0x5BBE6,'size':25,'expect_hex':expected.hex(),'expect_mask_hex':mask.hex()},visits=1024,frames=1600)
    for i,(direction,xy) in enumerate([('left',[1067,1752]),('down',[1074,1752]),('up',[1074,1656]),('left',[794,1656]),('left',[787,1656]),('right',[794,1656]),('down',[787,1656]),('up',[787,1640]),('left',[549,1640]),('down',[556,1640]),('up',[556,1604])]):
        p.move_to(f'wrapped_engineering_{i}',direction,xy);p.scenario['phases'][-1]['max_frames']=600
    complete_trade(p,inventory_expected=bytes.fromhex('3032310b26002123'))
    for q in p.scenario['phases'][1:]:q['name']='ro_'+q['name']
    for e in p.scenario['input_events']:
        e['after_phase']='ro_'+e['after_phase'];e['release_after_phase']='ro_'+e['release_after_phase']
    return p.scenario


def revised_awol():
    # Camera wrap fixes Y modulo4 to0. The body probe is(16,31), so
    # finish at1748, not the old parity2 route's1746 or its shifted1744.
    p=PlayerPlan(0x5D6,modal=False,xy=[556,1604],held=36,expected_health=49)
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([96,139],'right').cursor_to([96,147],'down').select('store_ochre',0)
    p.cursor_to([0,147],'left').select('equip_engineer',50).close_inventory()
    legs=[('down',[556,1640]),('right',[780,1640]),('left',[773,1640]),('down',[780,1692]),('right',[885,1692]),('down',[878,1768]),('right',[927,1768]),('left',[920,1768]),('down',[927,1768]),('up',[927,1748]),('right',[934,1748])]
    for i,(direction,xy) in enumerate(legs):
        if i==4:
            p.action('kwik_staging',0x5D6)
            p.action('wait_kwik_east',0x5D6,until={'address':0x5BBE6,'size':4,'expect_hex':'04000694','expect_mask_hex':'ff00ffff'},visits=1024,frames=1600)
        p.move_to(f'awol_approach_{i}',direction,xy)
    p.action('body_context_ready',0x5EA,until=goal(0x3B9A,(0x5AA7E).to_bytes(4,'big')),visits=64,frames=180)
    p.action('inventory_open',0x27EA,control='key 64').select('take_awol',55)
    p.cursor_to([0,139],'left').cursor_to([0,147],'down').select('carry_awol',0)
    p.cursor_to([192,147],'right').cursor_to([192,139],'up').select('recover_engineer',50).close_inventory()
    p.action('awol_objective',0x5D6)
    p.scenario['phases'][-1]['capture']['memory_reads'] += [goal(PLAYER+22,b'\x32'),goal(0x3B92,bytes.fromhex('3037310b26242123'))]
    for q in p.scenario['phases'][1:]:q['name']='ra_'+q['name']
    for e in p.scenario['input_events']:
        e['after_phase']='ra_'+e['after_phase'];e['release_after_phase']='ra_'+e['release_after_phase']
    return p.scenario


def connect(prefix,section):
    """Join paused canonical sections without losing their entry guards.

    No additional guest execution or input is introduced. Compatible masked
    expectations on an identical selector are combined; contradictory guards
    refuse composition. Unconstrained diagnostics may yield to entry guards.
    """
    import copy
    section=copy.deepcopy(section);tail=prefix['phases'][-1];anchor=section['phases'][1]
    if tail['breakpoint_stable_key']!=anchor['breakpoint_stable_key']:
        raise ValueError('Section boundary PCs differ')
    if 'until_memory' in tail:
        # Capture expectations are checked on EVERY goal-search visit. The
        # next entry's state is required only AFTER that search succeeds.
        # Retain an explicit bounded entry phase instead of strengthening the
        # transient producer state. This adds one original-PC visit, not a
        # guest-state write; wait-based patrol actions tolerate that timing.
        prefix['phases']+=section['phases'][1:]
        prefix['input_events']+=section['input_events']
        return prefix
    reads=copy.deepcopy(tail['capture']['memory_reads'])
    def selector(r):return (r.get('address'),r.get('base_register'),r.get('offset',0),r['size'])
    for incoming in anchor['capture']['memory_reads']:
        if 'expect_hex' not in incoming:continue
        existing=next((r for r in reads if selector(r)==selector(incoming)),None)
        if existing is None:reads.append(copy.deepcopy(incoming));continue
        size=incoming['size'];value=bytes.fromhex(incoming['expect_hex']);mask=bytes.fromhex(incoming.get('expect_mask_hex','ff'*size))
        prior=bytes.fromhex(existing.get('expect_hex','00'*size));prior_mask=bytes.fromhex(existing.get('expect_mask_hex','ff'*size) if 'expect_hex' in existing else '00'*size)
        if any((a^b)&m&n for a,b,m,n in zip(value,prior,mask,prior_mask)):
            raise ValueError('Contradictory section entry expectations')
        existing['expect_hex']=bytes((a&m)|(b&n) for a,b,m,n in zip(value,prior,mask,prior_mask)).hex()
        existing['expect_mask_hex']=bytes(m|n for m,n in zip(mask,prior_mask)).hex()
    while len(reads)>16:
        optional=next((r for r in reversed(reads) if 'expect_hex' not in r and r.get('address') not in (PLAYER,0x3BB2,0x3B92,0x3C2A)),None)
        if optional is None:raise ValueError('Section entry guards exceed capture budget')
        reads.remove(optional)
    tail['capture']['memory_reads']=reads
    previous=tail['name'];anchor_name=anchor['name']
    prefix['phases']+=section['phases'][2:]
    for event in section['input_events']:
        if event['after_phase']==anchor_name:event['after_phase']=previous
        prefix['input_events'].append(event)
    return prefix

def revised_prefix(*,cold=False):
    s=gate_exit(cold=cold)
    for section in [early_icelord,loot_icelord,prepare_hooligan,thermolance_hooligan,revised_captain,revised_ochre,revised_awol]:connect(s,section())
    s['identifier']='pandora-revised-required-item-prefix';return s


def main():
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cold',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.write_text(json.dumps(revised_prefix(cold=args.cold),indent=2)+'\n')


if __name__=='__main__':main()
