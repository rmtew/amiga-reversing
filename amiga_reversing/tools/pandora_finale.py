"""Normal-input console and escape plans for the measured HP49 prefix.

Checkpoint development precedes the single complete cold qualification.
No memory or register writes are used by these action plans.
"""
from .pandora_player import PlayerPlan,goal,PLAYER,UI
from .pandora_revised import connect,revised_prefix

INVENTORY_READY=bytes.fromhex('3037310b26242123')
INVENTORY_ARMED=bytes.fromhex('3037310b00000000')
CONSOLE_LEGS=[('up',[927,1748]),('down',[927,1772]),('left',[871,1772]),
 ('down',[878,1772]),('up',[878,1660]),('left',[787,1660]),
 ('right',[794,1660]),('down',[787,1660]),('up',[787,1648]),
 ('left',[507,1648]),('left',[395,1648]),('down',[402,1772]),
 ('right',[486,1772]),('down',[479,1772]),('up',[479,1748]),
 ('up',[479,1708]),('right',[500,1708])]


def namespace(s,prefix):
    for p in s['phases'][1:]:p['name']=prefix+p['name']
    for event in s['input_events']:
        event['after_phase']=prefix+event['after_phase'];event['release_after_phase']=prefix+event['release_after_phase']
    return s


def _inventory_expect(p,expected):
    next(r for r in p.scenario['phases'][-1]['capture']['memory_reads'] if r.get('address')==0x3B92).update(expect_hex=expected.hex())


def _console_close(p):
    # Self-destruct modal is$9C88, not the terminal's$9074.
    p.action('key_release',0x28D4,until=goal(0x39BC,b'\x00'),visits=64,frames=180)
    p.action('console_inventory_closed',0x9C88,control='key 64',until={'address':UI,'size':1,'expect_hex':'00','expect_mask_hex':'04'},visits=16)
    p.action('close_key_released',0x9C88,visits=3)


def _submission_check(p,name,count,state):
    p.action(name,0x9C88)
    # Qualifying, defeated count, timer WORD, submitted count, state.
    p.scenario['phases'][-1]['capture']['memory_reads'] += [
        {'address':0x3D22,'size':6,'expect_hex':bytes([count,0,0,0,count,state]).hex(),'expect_mask_hex':'ff000000ffff'},
        goal(PLAYER+22,b'\x00')]


def _submit(p,name,count,state):
    p.action(name,0x9C88,control='port1 fire',until=goal(PLAYER+22,b'\x00'),visits=16,frames=90)
    p.expected_held=0
    _submission_check(p,name+'_accepted',count,state)


def console(*,arm=False):
    p=PlayerPlan(0x5D6,modal=False,xy=[934,1748],held=50,expected_health=49)
    _inventory_expect(p,INVENTORY_READY)
    p.action('wait_patrol_east',0x5D6,until={'address':0x5BBE6,'size':4,'expect_hex':'04000694','expect_mask_hex':'ff00ffff'},visits=1024,frames=1600)
    for i,(direction,xy) in enumerate(CONSOLE_LEGS):p.move_to(f'console_approach_{i}',direction,xy)
    if arm:
        p.action('inventory_open',0x2754,control='key 64')
        p.cursor_to([96,139],'right').select('equip_sdi',38).close_inventory()
    p.action('console_entry',0x9C00,control='port1 right')
    p.modal=True;p.action('console_ready',0x9C88)
    p.scenario['phases'][-1]['capture']['memory_reads'] += [goal(0x3D27,b'\x00'),goal(PLAYER+22,bytes([38 if arm else 50]))]
    if arm:
        _submit(p,'submit_disk',0,1)
        for name,item,row,n in [('scarlet',35,163,1),('ochre',36,147,2),('blue',33,155,3)]:
            p.action('inventory_open',0x2754,control='key 64')
            p.cursor_to([96,139],'right')
            if row!=139:p.cursor_to([96,row],'down')
            p.select('equip_'+name,item);_console_close(p)
            _submit(p,'submit_'+name,n,255 if n==3 else 1)
        p.action('inventory_open',0x2754,control='key 64')
        p.cursor_to([96,139],'right').select('recover_engineer',50);_console_close(p)
    p.action('leave_console',0x9C9C,control='port1 down')
    p.modal=False;p.action('world_context',0x9CBC).action('world_ready',0x5D6)
    reads=p.scenario['phases'][-1]['capture']['memory_reads']
    reads[:]=[r for r in reads if r.get('address') not in (0x3D16,0x3CA2)]
    reads += [goal(0x3D27,bytes([255 if arm else 0])),goal(PLAYER+22,b'\x32'),goal(PLAYER,(507 if arm else 514).to_bytes(2,'big')+(1708).to_bytes(2,'big'))]
    _inventory_expect(p,INVENTORY_ARMED if arm else INVENTORY_READY)
    return namespace(p.scenario,'ac_' if arm else 'uc_')


DEPART_LEGS=[('down',[507,1772]),('left',[395,1772]),('down',[402,1772]),
 ('up',[402,1648]),('right',[682,1648]),('right',[780,1648]),('left',[773,1648]),
 ('up',[780,1648]),('down',[780,1692]),('right',[1060,1692]),('right',[1067,1692]),
 ('left',[1060,1692]),('down',[1067,1752]),('right',[1298,1752]),
 ('left',[1291,1752]),('down',[1298,1752]),('up',[1298,1592]),
 ('up',[1298,1512]),('up',[1298,1352]),('up',[1298,1320])]


def depart(*,armed=False):
    p=PlayerPlan(0x5D6,modal=False,xy=[507 if armed else 514,1708],held=50,expected_health=49)
    _inventory_expect(p,INVENTORY_ARMED if armed else INVENTORY_READY)
    if armed:p.move_to('restore_console_exit_alignment','right',[514,1708])
    for i,(direction,xy) in enumerate(DEPART_LEGS):
        if i==9:
            # Original patrol's top-left turn; no timing assumption from a
            # previous, shorter body approach is reused here.
            expected=bytearray(25);mask=bytearray(25)
            expected[:4]=bytes.fromhex('03600690');mask[:4]=bytes.fromhex('fff0fff0')
            expected[12:14]=(95).to_bytes(2,'big');mask[12:14]=b'\xff\xff';mask[24]=2
            p.action('wait_patrol_northwest',0x5D6,until={'address':0x5BBE6,'size':25,'expect_hex':expected.hex(),'expect_mask_hex':mask.hex()},visits=1024,frames=1600)
        p.move_to(f'engineering_departure_{i}',direction,xy)
    p.action('outside_engineering',0x5D6)
    p.scenario['phases'][-1]['capture']['memory_reads'] += [goal(0x3D27,bytes([255 if armed else 0])),goal(PLAYER+22,b'\x32')]
    _inventory_expect(p,INVENTORY_ARMED if armed else INVENTORY_READY)
    return namespace(p.scenario,'ad_' if armed else 'ud_')


def wrap_return(*,armed=False):
    p=PlayerPlan(0x5D6,modal=False,xy=[1298,1320],held=50,expected_health=49)
    _inventory_expect(p,INVENTORY_ARMED if armed else INVENTORY_READY)
    for i,yy in enumerate([1480,1640,1800,1960]):
        p.move_to(f'right_shaft_down_{i}','down',[1298,yy]);p.scenario['phases'][-1]['max_frames']=600
    p.action('bottom_to_top_wrap',0x9966,control='port1 down',frames=600)
    p.scenario['phases'][-1]['capture']['memory_reads'].append(goal(PLAYER,bytes.fromhex('05120010')))
    p.action('top_world',0x5D6)
    p.scenario['phases'][-1]['capture']['memory_reads'].append({'address':0x59DC2,'size':1,'expect_hex':'02','expect_mask_hex':'02'})
    p.move_to('past_dead_icelord_1','down',[1298,144]).move_to('past_dead_icelord_2','down',[1298,232])
    p.action('upper_return_ready',0x5D6)
    p.scenario['phases'][-1]['capture']['memory_reads'] += [goal(0x3D27,bytes([255 if armed else 0])),goal(PLAYER+22,b'\x32')]
    _inventory_expect(p,INVENTORY_ARMED if armed else INVENTORY_READY)
    return namespace(p.scenario,'aw_' if armed else 'uw_')


def upper_return():
    """Clear the original Thief strip empty-handed, then authorize AWOL."""
    p=PlayerPlan(0x5D6,modal=False,xy=[1298,232],held=50,expected_health=49)
    _inventory_expect(p,INVENTORY_ARMED)
    legs=[('left',[1018,232]),('left',[962,232]),('right',[969,232]),
          ('down',[962,312]),('left',[682,312]),('left',[479,312]),
          ('right',[486,312]),('down',[479,476])]
    for i,(direction,xy) in enumerate(legs):p.move_to(f'upper_corridor_{i}',direction,xy)
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([96,139],'right').select('protect_engineer',0).close_inventory()
    for i,(direction,xy) in enumerate([('down',[479,648]),('left',[430,648]),
                                     ('right',[437,648]),('down',[430,792]),('left',[220,792])]):
        p.move_to(f'escape_approach_{i}',direction,xy)
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([0,147],'down').select('equip_awol',55).close_inventory()
    p.move_to('awol_contact','left',[164,792])
    p.action('awol_authorized',0x5D6,until={'address':0x3D38,'size':1,'expect_hex':'10','expect_mask_hex':'10'},visits=64,frames=180)
    reads=p.scenario['phases'][-1]['capture']['memory_reads']
    reads[:]=[r for r in reads if r.get('address') not in (0x3D16,0x3CA2,0x3CB2)]
    reads += [goal(0x3D27,b'\xff'),{'address':0x3D22,'size':6}, {'address':0x3C82,'size':2}]
    _inventory_expect(p,bytes.fromhex('3000310b32000000'))
    return namespace(p.scenario,'ur_')


def escape():
    """Horizontal escape-tile probe and the original saved-Earth outcome."""
    p=PlayerPlan(0x5D6,modal=False,xy=[164,792],held=55,expected_health=49)
    p.move_to('escape_side_drift','down',[171,792]).move_to('escape_tile_row','down',[171,804])
    p.action('escape_outcome_entry',0x4C994,control='port1 left',frames=180)
    p.action('saved_earth_outcome_selected',0x4C9DC,frames=30)
    reads=p.scenario['phases'][-1]['capture']['memory_reads']
    reads[:]=[r for r in reads if r.get('address') not in (0x3D16,0x3CA2,0x3CB2)]
    reads += [goal(0x3D27,b'\xff'),{'address':0x3D38,'size':1,'expect_hex':'58','expect_mask_hex':'58'}, {'address':0x3C82,'size':2}]
    # LEA source$4C9BC + PC displacement$0127 selects source$4CAE5.
    # A0 is also independently checked in the qualification receipt.
    reads += [{'base_register':'a0','offset':0,'size':8}]
    p.action('escape_commit_inhibited',0x4C99C,frames=30)
    p.scenario['phases'][-1]['capture']['memory_reads'] += [{'address':0x3D38,'size':1,'expect_hex':'58','expect_mask_hex':'58'},goal(0x3CD4,b'\xff')]
    return namespace(p.scenario,'es_')


def complete(*,cold=True):
    s=revised_prefix(cold=cold)
    for section in [console(arm=True),depart(armed=True),wrap_return(armed=True),upper_return(),escape()]:connect(s,section)
    s['identifier']='pandora-normal-input-saved-earth-ending'
    return s


def main():
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['complete','console','arm','depart','armed-depart','wrap','armed-wrap','upper','escape'],default='complete')
    parser.add_argument('--checkpoint',action='store_true',help='Complete recipe starts at the verified Commander checkpoint instead of cold boot')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    stages={'complete':lambda:complete(cold=not args.checkpoint),'console':console,'arm':lambda:console(arm=True),'depart':depart,'armed-depart':lambda:depart(armed=True),'wrap':wrap_return,'armed-wrap':lambda:wrap_return(armed=True),'upper':upper_return,'escape':escape}
    args.output.write_text(json.dumps(stages[args.stage](),indent=2)+'\n')


if __name__=='__main__':main()
