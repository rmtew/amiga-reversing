"""Bounded normal-input priest completion candidate, using the known cold prefix.

The new approach is a candidate until a live receipt establishes it. Four
original stores are observed around execution; no game state is injected.
"""
import argparse
import hashlib
import json
from pathlib import Path
from .pandora_player import PlayerPlan,goal,PLAYER
from .pandora_finale import complete,namespace
from .pandora_terminal_modal_scenario import phase

PRIEST=0x59B32
CELL=0x64C0


def review(report_path):
    """Check the eight scoped witnesses; this is not a bus-event collector."""
    from .observed_layout_mapping import observed_address
    from .runtime_allocation import plan_digest
    def require(ok,message):
        if not ok:raise ValueError(message)
    r=json.loads(report_path.read_text());plan=r['config']['layout_plan']
    require(r['status']=='bounded_output_prefix_complete' and r['prefix_end']=='pp_passage_callback_finished','Incomplete priest route')
    require(plan_digest(plan)==r['config']['layout_plan_sha256'],'Layout identity changed')
    lease=r['runtime_allocation']['lease'];admitted=r['runtime_allocation']['native_admission']
    require(admitted['status']=='actual_placement_valid' and admitted['layout']['items'][0]==plan,'Native placement differs')
    owner=next(p for p in plan['regions'] if p['region_id']=='pandora_cpu_workspace')
    require(lease['base']==owner['runtime_address'] and lease['size']==owner['size'],'CPU lease/owner binding differs')
    require(r['handoff']['runtime_allocation']==lease and
            r['handoff']['payload_sha256']==r['config']['runtime_payload_sha256'] and
            r['native_materialization']['full_prefix_verified'],'Patched guest image not verified')
    counters=r['loss_monitor']['counters']
    require(counters['events']>0 and counters['dropped_events']==counters['dropped_notifications']==0,'Incomplete events')
    rows={p['name']:p for p in r['scenario']['phases']}
    require(len(rows)==len(r['scenario']['phases'])==230 and all(p['status']=='hit' for p in rows.values()),'Missing/duplicate/unhit phases')
    cell=observed_address(plan,CELL,4)
    closed=observed_address(plan,0x24C28,128);opened=observed_address(plan,0x1E928,128)
    witnesses=[]
    sites=[('passage_reset_store',0x9F38,None),('passage_reset_written',0x9F40,closed),
        ('pp_combat_open_store',0x78C4,None),('pp_combat_open_written',0x78CC,opened),
        ('pp_completion_closed_store',0x79F2,opened),('pp_priest_completion_store',0x4B0CE,closed),
        ('pp_priest_completion_written',0x4B0D6,opened),('pp_passage_callback_finished',0x5D6,opened)]
    for name,source,expected in sites:
        p=rows[name];capture=p['capture'];payload=p['payload']
        require(int(p['pc'],0)==observed_address(plan,0x10000+source),'Unexpected witness PC')
        require(payload['status']=='pc_matched' and int(payload['payload_offset'],0)==source and
                payload['payload_sha256']==r['config']['runtime_payload_sha256'],'Witness input identity differs')
        require(int(capture['registers']['a6'],0)==lease['base'],'A6 does not name the admitted CPU owner')
        memory={int(m['address'],0):bytes.fromhex(m['bytes']) for m in capture['memory_reads']}
        value=int.from_bytes(memory[cell],'big')
        require(len(memory[cell])==4 and (expected is None or value==expected),'Unexpected passage cell')
        witnesses.append(dict(name=name,source_offset=source,runtime_pc=int(p['pc'],0),frame=p['stop_event']['frame'],
            A6=lease['base'],cell_address=cell,cell_value=value,stack_return=p.get('stack_return_address')))
    require(int(rows['pp_priest_completion_store']['stack_return_address'],0)==observed_address(plan,0x17A02),'Not the original combat callback return')
    final={int(m['address'],0):bytes.fromhex(m['bytes']) for m in rows['pp_passage_callback_finished']['capture']['memory_reads']}
    player=final[observed_address(plan,PLAYER,36)];actor=final[observed_address(plan,PRIEST+48,36)]
    health=int.from_bytes(player[12:14],'big')
    require(health>0 and not player[24]&2 and actor[24]&2,'Live-player/defeated-priest predicate failed')
    return dict(status='four_stores_exercised_with_paired_PC_and_cell_snapshots',report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        phases=230,lease=lease,health=health,player_xy=[int.from_bytes(player[i:i+2],'big') for i in (0,2)],
        loss_counters=counters,witnesses=witnesses,natural_callback_caller_source=0x7A00,
        limits=['Snapshots plus matched executed instruction coordinates, not CPU write events.',
                'Reset/open stores can rewrite the existing value; only the closing/callback pair changes it here.',
                'Combat callback exercised; ranged callback remains covered by the earlier conditional static A6 contract only.',
                'No new graphics/PCM equality, arbitrary-entry or OS-return claim.'])


def store_capture():
    return {'registers':[f'd{i}' for i in range(8)]+[f'a{i}' for i in range(8)]+['sr'],
            'memory_reads':[{'address':CELL,'size':4},{'address':PRIEST+48,'size':36},
                {'address':PLAYER,'size':36},{'address':0x3CAA,'size':10},
                {'address':0x3B9E,'size':4}]}


def build():
    s=complete()
    end=next(i for i,p in enumerate(s['phases']) if p['name']=='rh_return_from_icelord_13')
    s['phases']=s['phases'][:end+1]
    names={p['name'] for p in s['phases']}
    s['input_events']=[e for e in s['input_events'] if e['after_phase'] in names and e['release_after_phase'] in names]
    reset=[]
    for name,pc in [('passage_reset_store',0x9F38),('passage_reset_written',0x9F40)]:
        q=phase(name,pc);q['capture']=store_capture();reset.append(q)
    s['phases'][1:1]=reset
    p=PlayerPlan(0x5D6,modal=False,xy=[115,542],held=5,expected_health=70)
    p.action('inventory_open',0x2754,control='key 64')
    p.cursor_to([0,163],'down').select('equip_thermolance',11).close_inventory()
    p.expected_held=11
    # Existing all-pose collision model: enter below the west wall through
    # the southern doorway. The last turn leaves Y410, outside the priest's
    # strict16-pixel gate; the following UP reaches the encounter naturally.
    legs=[('up',[115,458]),('right',[206,458]),('left',[199,458]),
          ('down',[206,458]),('up',[206,410]),('left',[192,410]),('down',[199,410])]
    for i,(direction,xy) in enumerate(legs):p.move_to(f'priest_approach_{i}',direction,xy)
    def combat(name,pc,**kwargs):
        p.action(name,pc,guard=False,**kwargs)
        p.scenario['phases'][-1]['capture']=store_capture()
    combat('combat_open_store',0x78C4,control='port1 up',frames=180)
    combat('combat_open_written',0x78CC)
    for n,hp in enumerate((42,17),1):
        combat(f'charge_{n}',0x7938,until=goal(0x3CAA,b'\x00\x18'),visits=64,frames=240)
        combat(f'hit_{n}',0x7938,control='port1 fire',until=goal(PRIEST+60,hp.to_bytes(2,'big')),visits=16,frames=120)
    combat('charge_3',0x7938,until=goal(0x3CAA,b'\x00\x18'),visits=64,frames=240)
    combat('completion_closed_store',0x79F2,control='port1 fire',frames=120)
    combat('priest_completion_store',0x4B0CE)
    combat('priest_completion_written',0x4B0D6)
    combat('passage_callback_finished',0x5D6,until={'address':PRIEST+72,'size':1,'expect_hex':'02','expect_mask_hex':'02'},visits=16,frames=120)
    namespace(p.scenario,'pp_')
    # Explicit world-entry phase preserves position/health/item guards, rather
    # than strengthening the preceding movement goal's intermediate visits.
    s['phases']+=p.scenario['phases'][1:]
    s['input_events']+=p.scenario['input_events']
    s['identifier']='pandora-cold-priest-passage-completion'
    return s


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--report',type=Path,help='Review a completed private route report instead of emitting the candidate')
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(review(args.report) if args.report else build(),indent=2)+'\n')


if __name__=='__main__':main()
