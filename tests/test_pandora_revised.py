import hashlib,json
from pathlib import Path
from amiga_reversing.tools.pandora_revised import prepare_hooligan
from amiga_reversing.tools.pandora_completion import captain
from amiga_reversing.tools.pandora_ochre import approach
from amiga_reversing.tools.pandora_awol import acquire


def test_published_recipe_defaults_preserve_exact_authored_identity():
    for factory,filename,name in [(captain,'pandora-sdi-progression.json','captain-cold-a'),
                                  (approach,'pandora-ochre-progression.json','ochre-cold-b'),
                                  (acquire,'pandora-awol-progression.json','awol-cold-a')]:
        receipt=json.loads((Path('runtime/observations')/filename).read_text())
        run=next(r for r in receipt['runs'] if r['name']==name)
        rendered=json.dumps(factory(cold=True),indent=2)+'\n'
        assert hashlib.sha256(rendered.encode()).hexdigest()==run['authored_sha256']


def test_original_pause_precondition_checks_position_health_delay_and_liveness():
    goal=next(p['until_memory'] for p in prepare_hooligan()['phases'] if p['name']=='rh_wait_hooligan_pause')
    value=bytearray(25);value[:4]=bytes.fromhex('01e5026c');value[12:14]=(60).to_bytes(2,'big');value[20:22]=(50).to_bytes(2,'big')
    mask=bytes.fromhex(goal['expect_mask_hex']);expected=bytes.fromhex(goal['expect_hex'])
    def matches(data):return all(a&m==b&m for a,b,m in zip(data,expected,mask))
    assert goal['address']==0x5A058 and goal['size']==25 and matches(value)
    for offset,replacement in [(3,0),(13,59),(21,40),(24,2)]:
        bad=bytearray(value);bad[offset]=replacement;assert not matches(bad)
    # Original scripts bound the pause at50; the selected mask admits its
    # last safe48..50 ticks, not an arbitrary-record upper-bound theorem.
    for delay in [48,49,50]:value[20:22]=delay.to_bytes(2,'big');assert matches(value)


def test_complete_ending_plan_has_distinct_code_submissions_and_bounded_captures():
    from amiga_reversing.tools.pandora_finale import complete
    from amiga_reversing.tools.copperline_session import validate_capture
    s=complete();names=[p['name'] for p in s['phases']]
    assert len(names)==len(set(names))
    for name in ['disk','scarlet','ochre','blue']:assert 'ac_submit_'+name+'_accepted' in names
    for p in s['phases'][1:]:validate_capture(p['capture'])
    assert names[-2:] == ['es_saved_earth_outcome_selected','es_escape_commit_inhibited']
    assert not any('write' in key for p in s['phases'] for key in p)


def test_connect_preserves_entry_expectations_and_refuses_conflicts():
    import copy,pytest
    from amiga_reversing.tools.pandora_player import PlayerPlan,PLAYER
    from amiga_reversing.tools.pandora_revised import connect
    prefix=PlayerPlan(0x5D6,modal=False,xy=[10,20],held=50).scenario
    section=PlayerPlan(0x5D6,modal=False,xy=[10,20],held=50).action('later',0x5EA).scenario
    joined=connect(copy.deepcopy(prefix),section)
    reads=joined['phases'][1]['capture']['memory_reads']
    assert any(r.get('address')==PLAYER and r.get('size')==4 and r.get('expect_hex')=='000a0014' for r in reads)
    assert section['phases'][1]['name']=='anchor'
    bad=PlayerPlan(0x5D6,modal=False,xy=[11,20],held=50).scenario
    with pytest.raises(ValueError,match='Contradictory'):connect(copy.deepcopy(prefix),bad)
    with pytest.raises(ValueError,match='PCs differ'):connect(copy.deepcopy(prefix),PlayerPlan(0x5EA).scenario)


def test_connect_goal_search_keeps_next_entry_guard_after_transient_visits():
    from amiga_reversing.tools.pandora_player import PlayerPlan,PLAYER,goal
    from amiga_reversing.tools.pandora_revised import connect
    first=PlayerPlan(0x5D6,modal=False,xy=[10,20],held=50)
    first.action('wait_for_producer',0x5EA,until=goal(0x1000,b'\x02'),visits=16)
    second=PlayerPlan(0x5EA,modal=False,xy=[30,20],held=50).action('consume',0x9844,control='port1 right')
    second.scenario['phases'][1]['name']='consumer_entry'
    second.scenario['input_events'][0]['after_phase']='consumer_entry'
    joined=connect(first.scenario,second.scenario)
    producer,entry,consumer=joined['phases'][-3:]
    assert producer['name']=='wait_for_producer' and entry['name']=='consumer_entry'
    assert not any(r.get('address')==PLAYER and r.get('size')==4 and r.get('expect_hex')=='001e0014' for r in producer['capture']['memory_reads'])
    assert any(r.get('address')==PLAYER and r.get('size')==4 and r.get('expect_hex')=='001e0014' for r in entry['capture']['memory_reads'])
    assert joined['input_events'][-1]['after_phase']=='consumer_entry'
    # Exercise the actual shared expectation evaluator over synthetic states.
    # An unfinished producer is valid; only its consumer boundary requiresXY30.
    from amiga_reversing.tools.copperline_runtime import capture_scenario_state
    class State:
        memory={}
        def registers(self):return {}
        def read_memory(self,address,size):return bytes(self.memory.get(address+i,0) for i in range(size))
        def put(self,address,value):self.memory.update({address+i:v for i,v in enumerate(value)})
    state=State()
    for read in entry['capture']['memory_reads']:
        if 'expect_hex' in read:state.put(read['address'],bytes.fromhex(read['expect_hex']))
    def matches(reads):
        result=capture_scenario_state(state,{'memory_reads':reads})
        return all(r.get('expectation',{}).get('matched',True) for r in result['memory_reads'])
    producer_guards=[r for r in producer['capture']['memory_reads'] if 'expect_hex' in r]
    entry_guards=[r for r in entry['capture']['memory_reads'] if 'expect_hex' in r]
    state.put(PLAYER,bytes.fromhex('000a0014'))
    assert matches(producer_guards) and not matches([producer['until_memory']])
    assert not matches(entry_guards)
    state.put(0x1000,b'\x02');state.put(PLAYER,bytes.fromhex('001e0014'))
    assert matches(producer_guards) and matches([producer['until_memory']]) and matches(entry_guards)
    state.put(PLAYER,bytes.fromhex('001f0014'))
    assert matches([producer['until_memory']]) and not matches(entry_guards)
