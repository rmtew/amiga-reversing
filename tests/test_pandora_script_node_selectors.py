"""Original indirect script node commands in controlled finite RAM chains.

Script bytes are data inputs; no instruction/callee is patched. These checks
establish local selection, shared node writes and continuation, not ordinary
script admission, exclusive node ownership or any rendered pixels.
"""
import pytest

from tests.test_pandora_state_transitions import BASE,cpu_fixture
from tests.test_pandora_render_order import sequencer

ACTOR,DESC,ROOT,ATTACHED,NODE,OLD_ROOT,OLD_ATTACHED,OBSERVER=range(0x80000,0x80800,0x100)
SCRIPT,FRAMES,NEW_FRAMES=0x82000,0x83000,0x83100
WIDTHS={25:6,26:6,27:6,28:10,29:10,30:10,31:2,32:2}
HEAD_ONLY={25,28}
SET_SELECTOR={26,29,31}


@pytest.fixture
def selectors(cpu_fixture):
    cpu,memory,schemas,read,write,run=cpu_fixture
    obj,state,node=(schemas[n] for n in ['world_object_shared_prefix','world_position_state_record','WorldPositionStateNode'])
    def prepare(opcode,root_flags=0,attached_flags=8,*,same=False):
        memory[ACTOR:OBSERVER+26]=bytes(OBSERVER+26-ACTOR)
        write(ACTOR+obj['position_descriptor_ptr'],DESC)
        write(ACTOR+obj['behavior_script_ptr'],SCRIPT)
        write(DESC,ROOT)
        for address,old,flags in [(ROOT,OLD_ROOT,root_flags),(ATTACHED,OLD_ATTACHED,attached_flags)]:
            write(address+state['state_node_ptr'],NODE if same else old)
            write(address+state['current_geometry_ptr'],0x87654321)
            write(address+state['world_object_flags'],flags,1)
            write(old+node['frame_index_and_phase'],0x3456,2)
        write(ROOT+state['attachment_state_ptr'],ATTACHED)
        # An unrelated state already references the incoming mutable node.
        write(OBSERVER+state['state_node_ptr'],NODE)
        write(OBSERVER+state['current_geometry_ptr'],0x12345678)
        write(NODE+node['position_descriptor_ptr'],0x76543210)
        write(NODE+node['frame_count'],3,1);write(NODE+node['phase_step'],64,1)
        write(NODE+node['frame_sequence_ptr'],FRAMES)
        write(NODE+node['mode_flags'],5,1)
        write(NODE+node['xy_sequence_ptr'],0)
        write(NODE+node['frame_index_and_phase'],0x1234,2)
        for sequence in [FRAMES,NEW_FRAMES]:
            for i in range(4):write(sequence+4*i,sequence+0x40+18*i)
        width=WIDTHS[opcode]
        memory[SCRIPT:SCRIPT+32]=bytes(32)
        write(SCRIPT,opcode,2)
        if opcode<31:write(SCRIPT+2,NODE)
        if opcode in [28,29,30]:write(SCRIPT+6,NEW_FRAMES)
        write(SCRIPT+width,5,2);write(SCRIPT+width+2,1,2)
        cpu.a[5]=ACTOR
        return sequencer(cpu,memory,write)
    return cpu,memory,read,write,obj,state,node,prepare


def selected(opcode,root_flags,attached_flags):
    wants_set=opcode in SET_SELECTOR
    for address,flags in [(ROOT,root_flags),(ATTACHED,attached_flags)]:
        if bool(flags&8)==wants_set:return address
        if opcode in HEAD_ONLY:return None
    return None


def test_all_eight_commands_and_all_head_flag_bytes_return_through_the_real_interpreter(selectors):
    cpu,memory,read,write,obj,state,node,prepare=selectors
    for opcode in WIDTHS:
        for flags in range(256):
            advance=prepare(opcode,flags,flags^8)
            before=[bytes(memory[a:a+26]) for a in [ROOT,ATTACHED]]
            assert advance(0x13F4,budget=512).stop_reason==1
            chosen=selected(opcode,flags,flags^8)
            assert cpu.a[5]==ACTOR and cpu.a[4]==SCRIPT+WIDTHS[opcode]+4
            assert read(ACTOR+obj['behavior_script_ptr'])==cpu.a[4]
            assert read(ACTOR+obj['behavior_script_delay_ticks'],2)==1
            for i,address in enumerate([ROOT,ATTACHED]):
                if address!=chosen or opcode>=31:assert bytes(memory[address:address+26])==before[i]
                else:
                    expected=bytearray(before[i]);at=state['state_node_ptr'];expected[at:at+4]=NODE.to_bytes(4,'big')
                    assert bytes(memory[address:address+26])==expected
            if opcode>=31:
                old=OLD_ROOT if chosen==ROOT else OLD_ATTACHED
                assert read(old+node['mode_flags'],1)==1
                assert read(old+node['frame_index_and_phase'],2)==0x3456
                assert read(NODE+node['frame_index_and_phase'],2)==0x1234
            else:
                assert read(NODE+node['frame_index_and_phase'],2)==(0x1234 if chosen is None else 0)
                assert read(NODE+node['mode_flags'],1)==(5 if chosen is None else 4)
                assert read(NODE+node['frame_sequence_ptr'])==(NEW_FRAMES if chosen is not None and opcode in [28,29,30] else FRAMES)
            assert read(NODE+node['position_descriptor_ptr'])==0x76543210
            assert read(OBSERVER+state['state_node_ptr'])==NODE
            assert read(OBSERVER+state['current_geometry_ptr'])==0x12345678


def test_head_only_rejection_never_falls_back_and_walkers_take_the_first_match(selectors):
    cpu,memory,read,write,obj,state,node,prepare=selectors
    for opcode in WIDTHS:
        for flags in [(0,0),(8,8),(8,0),(0,8)]:
            advance=prepare(opcode,*flags)
            before=bytes(memory[ROOT:OBSERVER+26])
            assert advance(0x13F4,budget=512).stop_reason==1
            chosen=selected(opcode,*flags)
            if chosen is None:assert bytes(memory[ROOT:OBSERVER+26])==before
            elif opcode<31:
                assert read(chosen+state['state_node_ptr'])==NODE
                other=ATTACHED if chosen==ROOT else ROOT
                assert read(other+state['state_node_ptr'])==(OLD_ATTACHED if other==ATTACHED else OLD_ROOT)


def test_same_node_reselection_restarts_shared_clock_but_toggles_preserve_it(selectors):
    cpu,memory,read,write,obj,state,node,prepare=selectors
    for opcode in WIDTHS:
        flags=8 if opcode in SET_SELECTOR else 0
        advance=prepare(opcode,flags,flags^8,same=True)
        before=bytes(memory[NODE:NODE+18])
        assert advance(0x13F4,budget=512).stop_reason==1
        assert read(ROOT+state['state_node_ptr'])==read(OBSERVER+state['state_node_ptr'])==NODE
        expected=bytearray(before)
        if opcode>=31:expected[node['mode_flags']]^=1
        else:
            expected[node['mode_flags']]&=~1;at=node['frame_index_and_phase'];expected[at:at+2]=bytes(2)
            if opcode in [28,29,30]:at=node['frame_sequence_ptr'];expected[at:at+4]=NEW_FRAMES.to_bytes(4,'big')
        assert bytes(memory[NODE:NODE+18])==expected
        assert read(ROOT+state['current_geometry_ptr'])==0x87654321
        assert read(OBSERVER+state['current_geometry_ptr'])==0x12345678


def test_sequence_install_preserves_count_and_cached_geometry_until_the_phase_turns_negative(selectors):
    cpu,memory,read,write,obj,state,node,prepare=selectors
    advance=prepare(28)
    assert advance(0x13F4,budget=512).stop_reason==1
    assert read(NODE+node['frame_count'],1)==3 and read(NODE+node['phase_step'],1)==64
    assert read(NODE+node['position_descriptor_ptr'])==0x76543210
    assert read(NODE+node['xy_sequence_ptr'])==0
    cpu.a[4]=ROOT
    for service in range(1,3):
        assert sequencer(cpu,memory,write)(0x951A,budget=128).stop_reason==1
        assert read(NODE+node['frame_index_and_phase'],2)==(64 if service==1 else 0x100)
        assert read(ROOT+state['current_geometry_ptr'])==(0x87654321 if service==1 else read(NEW_FRAMES+8))
    # The observer's cached geometry is separate, although its node clock changed.
    assert read(OBSERVER+state['current_geometry_ptr'])==0x12345678


def test_nonmatching_cycle_has_no_traversal_bound_and_never_commits_the_cursor(selectors):
    cpu,memory,read,write,obj,state,node,prepare=selectors
    for opcode in [26,27,29,30,31,32]:
        flags=0 if opcode in SET_SELECTOR else 8
        advance=prepare(opcode,flags,flags)
        write(ATTACHED+state['attachment_state_ptr'],ROOT)
        before=bytes(memory[NODE:NODE+18])
        assert advance(0x13F4,budget=128).stop_reason==3
        assert read(ACTOR+obj['behavior_script_ptr'])==SCRIPT
        assert read(ACTOR+obj['behavior_script_delay_ticks'],2)==0
        assert bytes(memory[NODE:NODE+18])==before
        assert cpu.a[5]==ACTOR
