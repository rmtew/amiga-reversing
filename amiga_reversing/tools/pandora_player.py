"""Small state-aware Pandora action plans over the existing headless runner.

Actions use normal inputs. The observer decodes established original-layout
fields; it does not steer the player, inject state, or collect memory watches.
Emit a scenario for copperline_session; summarize its private runner report.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from .pandora_app_interaction_watch_scenario import build_route
from .pandora_terminal_modal_scenario import build_approach, capture, phase

PLAYER = 0x5C352
HEADER = 0x3BB2
UI = 0x3C2A
CURSOR = 0x3C10
CACHE = 0x3D16


def goal(address, value):
    return {'address': address, 'size': len(value), 'expect_hex': value.hex()}


def observe(captured):
    """Decode snapshots only, never infer a guest memory-access event."""
    memory = {}
    for r in (captured or {}).get('memory_reads', []):
        address=int(r['address'],0);value=bytes.fromhex(r['bytes'])
        if len(value)>len(memory.get(address,b'')):memory[address]=value
    p, h = memory.get(PLAYER), memory.get(HEADER)
    state = {}
    if p:
        state.update(xy=[int.from_bytes(p[i:i+2], 'big') for i in (0, 2)],
                     health=int.from_bytes(p[12:14], 'big'), held=p[22],
                     inactive=bool(p[24] & 2))
    if h:
        state['map'] = [int.from_bytes(h[a:b], 'big') for a,b in ((8,12),(12,14),(14,16))]
    if UI in memory:
        state['ui'] = memory[UI][0]
        if state['ui'] & 2:state['position_domain']='combat_x_bias_10000'
    if CACHE in memory:state['cached_id'] = memory[CACHE][0]
    if CURSOR in memory:
        c=memory[CURSOR];state['cursor']=[int.from_bytes(c[i:i+2], 'big') for i in (0,2)]
    for key,address,size in [('carried',0x3B92,4),('display_ids',0x3CB6,4),('deposit',0x3CD6,1)]:
        if address in memory:state[key]=list(memory[address][:size])
    # Modal capture includes the owner pointer and four staged IDs together.
    if 0x3CB2 in memory:state['display_ids']=list(memory[0x3CB2][4:8])
    return state


class PlayerPlan:
    """Compose bounded semantic actions, with independent state goals/guards."""
    def __init__(self, anchor=0x9074, *, modal=True, xy=None, held=54, expected_health=95):
        base=build_approach()
        self.scenario={k:copy.deepcopy(v) for k,v in base.items() if k not in ('phases','input_events')}
        self.scenario.update(identifier='pandora-state-aware-player',
            phases=[{'name':'checkpoint','observable':'verified_checkpoint'}, phase('anchor',anchor,1)],
            input_events=[])
        self.expected_health=expected_health
        self.expected_held=held
        self.modal=modal
        self._guards(self.scenario['phases'][-1])
        origin=xy if xy is not None else ([640,734] if modal else [241,942])
        self.scenario['phases'][-1]['capture']['memory_reads'] += [
            goal(PLAYER,b''.join(n.to_bytes(2,'big') for n in origin)),goal(PLAYER+22,bytes([held]))]

    def _guards(self,p):
        # Positive health is diagnosed separately; inactive bit must remain clear.
        p['capture']['memory_reads']=[r for r in p['capture']['memory_reads'] if r.get('address') not in (0x3C77,0x5C72A,0x3CD0,0x3D64)]
        reads=p['capture']['memory_reads']
        reads.append({'address':PLAYER+24,'size':1,'expect_hex':'00','expect_mask_hex':'02'})
        reads.append(goal(PLAYER+12,self.expected_health.to_bytes(2,'big')))
        map_value=(0x18A20).to_bytes(4,'big')+bytes.fromhex('00140008') if self.modal else bytes.fromhex('00004000005a0081')
        reads.append(goal(HEADER+8,map_value))

    def action(self,name,pc,*,control=None,until=None,visits=1,frames=360,guard=True):
        previous=self.scenario['phases'][-1]['name']
        stem=name;ordinal=2
        while any(q.get('name')==name for q in self.scenario['phases']):
            name=f'{stem}_{ordinal}';ordinal+=1
        p=phase(name,pc,visits);p['max_frames']=frames
        # Common capture has15 selectors. Guards use independent small reads;
        # discard unrelated status/position diagnostics to stay within16.
        p['capture']['memory_reads']=[r for r in capture()['memory_reads']
            if r.get('address') not in (0x3C77,0x5C72A,0x3CD0,0x3D64)]
        if guard:self._guards(p)
        if until is not None:p['until_memory']=until
        self.scenario['phases'].append(p)
        if control:self.scenario['input_events'].append({'after_phase':previous,'control':control,'release_after_phase':name})
        return self

    def move_to(self,name,direction,xy):
        value=b''.join(n.to_bytes(2,'big') for n in xy)
        self.action(name,0x9844,control='port1 '+direction,until=goal(PLAYER,value),visits=64)
        self.scenario['phases'][-1]['capture']['memory_reads'].append(goal(PLAYER+22,bytes([self.expected_held])))
        return self

    def inventory_open(self):
        return self.action('inventory_open',0x28D4,control='key 64',
            until={'address':UI,'size':1,'expect_hex':'04','expect_mask_hex':'04'},visits=16)

    def cursor_to(self,xy,direction):
        # Input was sampled before $28D4. Brake one service before the final
        # step, so that the last in-flight step cannot start a second move.
        step={'down':(0,2),'up':(0,-2),'right':(12,0),'left':(-12,0)}[direction]
        braking=[xy[i]-step[i] for i in range(2)]
        name='cursor_to_'+str(xy[0])+'_'+str(xy[1])+'_'+direction
        self.action(name+'_brake',0x28D4,control='port1 '+direction,
            until=goal(CURSOR,b''.join(n.to_bytes(2,'big') for n in braking)),visits=32)
        return self.action(name+'_settled',0x28D4,
            until=goal(CURSOR,b''.join(n.to_bytes(2,'big') for n in xy)),visits=8)

    def select(self,name,held):
        # One released-input service after cursor completion clears the fire latch.
        self.action(name+'_ready',0x28D4,visits=2)
        self.action(name,0x28D4,control='port1 fire',until=goal(PLAYER+22,bytes([held])),visits=16)
        self.expected_held=held
        return self

    def close_inventory(self):
        self.action('key_release_services',0x28D4,until=goal(0x39BC,b'\x00'),visits=64,frames=180)
        self.action('inventory_closed',0x9074 if self.modal else 0x5D6,control='key 64',
            until={'address':UI,'size':1,'expect_hex':'00','expect_mask_hex':'04'},visits=16)
        return self.action('released_close_key',0x9074 if self.modal else 0x5D6,visits=3)

    def exit_terminal(self):
        self.action('exit_direction',0x9088,control='port1 down')
        self.modal=False
        self.action('world_restored',0x90B0)
        return self.action('world_main',0x5D6)


def card_interaction(*, provision=False):
    p=PlayerPlan()
    p.inventory_open().cursor_to([192,147],'down').select('take_engineer_card',50)
    p.action('terminal_card_displayed',0x9078,until=goal(CACHE,b'\x32'),visits=8)
    if provision:
        p.cursor_to([192,139],'up').cursor_to([0,139],'left').select('store_engineer',0)
        p.cursor_to([192,139],'right').select('take_sonicdriver',5)
        p.action('terminal_noncard_display',0x9078,until=goal(CACHE,b'\x05'),visits=8)
    p.close_inventory().exit_terminal()
    p.scenario['phases'][-1]['capture']['memory_reads'].append(goal(PLAYER+22,bytes([5 if provision else 50])))
    if provision:p.scenario['phases'][-1]['capture']['memory_reads'].append(goal(0x3B92,b'\x32'))
    p.scenario['identifier']='pandora-player-terminal-engineer-card'
    return p.scenario


def northern_approach():
    p=PlayerPlan(0x9844,modal=False)
    for name,direction,xy in [('north','up',[241,794]),('east','right',[549,794]),
        ('opening_row','up',[542,702]),('cross_opening','right',[598,702]),('console_row','down',[591,734])]:
        p.move_to(name,direction,xy)
    p.action('terminal_entry',0x8FF2,control='port1 right')
    p.modal=True;p.action('terminal_display',0x9074)
    return p.scenario


def inventory_deposit():
    s=build_route()
    for i,p in enumerate(s['phases'][1:],1):
        p['capture']=capture()
        # Keep deposit observation and do not apply modal-map guards to boot/UI.
        p['capture']['memory_reads']=[r for r in p['capture']['memory_reads'] if r.get('address')!=0x5C72A]
        p['capture']['memory_reads'].append({'address':0x3CD6,'size':1})
        if i>1:p['max_frames']=600
    expected={'store_selection_committed':(0,54),'retrieve_selection_committed':(54,0),
              'terminal_deposit_committed':(0,0)}
    for p in s['phases']:
        if p['name'] in expected:
            held,carried=expected[p['name']]
            p['capture']['memory_reads'] += [goal(PLAYER+22,bytes([held])),goal(0x3B92,bytes([carried]))]
            # At most16 descriptors: remove unneeded slot diagnostics.
            p['capture']['memory_reads']=[r for r in p['capture']['memory_reads'] if r.get('address') not in (0x3CD0,0x3D64)]
    return s


def walkthrough(*, provision=False):
    """Cold boot through card exchange (optionally keep card and take tool)."""
    prefix=inventory_deposit()
    end=next(i for i,p in enumerate(prefix['phases']) if p['name']=='down_19_before_inventory')
    prefix['phases']=prefix['phases'][:end+1]
    names={p['name'] for p in prefix['phases']}
    prefix['input_events']=[e for e in prefix['input_events'] if e['after_phase'] in names and e['release_after_phase'] in names]
    for continuation in [northern_approach(),card_interaction(provision=provision)]:
        previous=prefix['phases'][-1]['name']
        boundary=prefix['phases'][-1]
        boundary['capture']=copy.deepcopy(continuation['phases'][1]['capture'])
        if boundary.get('occurrences',1)>1:
            origin=next(r for r in boundary['capture']['memory_reads'] if r.get('address')==PLAYER and r['size']==4)
            boundary['capture']['memory_reads'].remove(origin)
            boundary.update(until_memory=origin,occurrences=64,max_frames=600)
        prefix['phases']+=continuation['phases'][2:]
        for e in continuation['input_events']:
            e=copy.deepcopy(e)
            if e['after_phase']=='anchor':e['after_phase']=previous
            prefix['input_events'].append(e)
    prefix['identifier']='pandora-player-cold-boot-card'+('-and-sonicdriver' if provision else '')
    return prefix


def summarize(report):
    runner=report.get('runner',report)
    scenario=runner.get('observation',{}).get('scenario',{})
    actions=[]
    for p in scenario.get('phases',[]):
        diagnostic=p.get('diagnostic_capture') if p.get('status')!='hit' else None
        state=observe(diagnostic or p.get('capture'))
        reason=p.get('termination')
        if state.get('inactive') or state.get('health')==0:reason='player_dead'
        elif p.get('status')!='hit' and state.get('ui',0)&2 and p.get('stable_key','').startswith('s0:00009844:'):
            reason='combat_blocks_movement'
        action={'action':p['name'],'status':p['status'],'reason':reason,
            'frame':(p.get('stop_event') or {}).get('frame'),'state':state,
            'visits':p.get('occurrences_observed')}
        if diagnostic:
            action.update(state_origin='diagnostic_stop',
                last_canonical_state=observe(p.get('capture')))
        actions.append(action)
    return {'status':runner['status'],'actions':actions,'input_trace':scenario.get('input_trace',[]),
            'limits':'Original layout snapshots; CPU navigation only. No DMA/watch inference or disk-loader parity.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',choices=('inventory-deposit','north-terminal','card','walkthrough','provision'))
    parser.add_argument('--report',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if bool(args.plan)==bool(args.report):parser.error('Choose one of --plan or --report')
    result=summarize(json.loads(args.report.read_text())) if args.report else {
        'inventory-deposit':inventory_deposit,'north-terminal':northern_approach,'card':card_interaction,
        'walkthrough':walkthrough,'provision':lambda:walkthrough(provision=True)}[args.plan]()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
