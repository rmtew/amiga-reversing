"""Original save/load pointer transforms under supplied RAM state.

No disk, loader, gameplay reachability, or universal pointer-lifetime claim.
In particular the conditional transforms are not invertible for every LONG.
"""
import ctypes
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, state, run, put, STACK, RETURN

FIXED = ['savegame_prefix_rebased_long', 'object_update_cursor', 'distant_objects_cursor',
         'integrating_objects_cursor', 'nearby_objects_cursor', 'visible_objects_cursor',
         'contact_objects_cursor', 'free_object_stack_cursor', 'player_object_reference',
         'carried_neutron_bomb_reference', 'selected_celestial_body_reference', 'tractor_target_reference',
         'previous_tractor_target_reference', 'growing_projector_part_reference', 'nearby_space_station_reference']
ARRAYS = [('free_object_stack_storage', 250), ('distant_object_list_storage', 251),
          ('nearby_object_list_storage', 251), ('visible_object_list_storage', 251),
          ('contact_object_list_storage', 251), ('integrating_object_list_storage', 61)]


@pytest.fixture(scope='module')
def layout(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    additions = {'SG2_SAVE_RELEASED_REFERENCE_DBF_LAST': 9, 'SG2_SAVE_OBJECT_SLOT_DBF_LAST': 249,
        'SG2_SAVE_OBJECT_LIST_WITH_END_DBF_LAST': 250, 'SG2_SAVE_INTEGRATING_LIST_WITH_END_DBF_LAST': 60,
        'SG2_SAVE_LINK_REBASE_GUARD_BYTE_OFFSET': 1, 'serialize_eligible_object_links': 0x10674,
        'serialize_next_world_object_record': 0x106A2, 'restore_eligible_object_links': 0x1075A,
        'restore_next_world_object_record': 0x10788}
    names = FIXED+[name for name, _ in ARRAYS]+['released_object_tracking_references', 'world_object_pool',
        'app_SIZEOF', 'SG2WorldObject_SIZEOF', 'SG2WorldObject_back_link_or_sentinel',
        'SG2WorldObject_linked_record_or_sentinel', 'serialize_workspace_pointers_relative',
        'restore_workspace_pointers_absolute', 'shared_workspace_prefix',
        'copy_saved_workspace_prefix_loop', 'deselect_disk_backend',
        'interrupted_game_available_flag', 'SG2_SAVE_RESTORE_DBF_LAST']+list(additions)
    folder = tmp_path_factory.mktemp('workspace-rebase-symbols'); source, output = folder/'map.s', folder/'map.raw'
    source.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result = subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-m68000',
        '-no-opt', '-I'+str(target/'includes'), '-o', str(output), str(source)], cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    raw = output.read_bytes(); size = 4*len(names)
    assert raw[:-size] == original_image[0]
    values = dict(zip(names, struct.unpack('>'+'I'*len(names), raw[-size:])))
    assert values['SG2WorldObject_SIZEOF'] == 68
    assert values['SG2WorldObject_back_link_or_sentinel'] == 56
    assert values['SG2WorldObject_linked_record_or_sentinel'] == 60
    assert values['world_object_pool']+250*68 == values['app_SIZEOF'] == 0x6598
    assert values['serialize_workspace_pointers_relative'] == 0x105C6
    assert values['restore_workspace_pointers_absolute'] == 0x106AC
    assert {name: values[name] for name in additions} == additions
    return values


def get(memory, address):
    return int.from_bytes(bytes(memory[address:address+4]), 'big')


def sample(original_image, layout, base):
    memory = (ctypes.c_uint8*0x180000)()
    ctypes.memmove(ctypes.addressof(memory)+0x1000, original_image[0], len(original_image[0]))
    size = layout['app_SIZEOF']
    memory[base-8:base+size+8] = bytes((i*37+i//256) & 255 for i in range(size+16))
    values = [0, 0xFFFFFFFF, base, base-1, base+2, base+68, 1, 0x80000000, 0xFFFFFFFC]
    for i, name in enumerate(FIXED): put(memory, base+layout[name], values[i % len(values)])
    for name, count in ARRAYS:
        for i in range(count): put(memory, base+layout[name]+i*4, values[i % len(values)])
    for i in range(10): put(memory, base+layout['released_object_tracking_references']+i*4, values[i % len(values)])
    pool = base+layout['world_object_pool']
    for i in range(250):
        memory[pool+68*i+1] = [0, 127, 128, 255][i % 4]
        for j, offset in enumerate([56, 60]): put(memory, pool+68*i+offset, values[(i+j) % len(values)])
    put(memory, STACK, RETURN)
    return memory


def model_transform(before, layout, base, absolute):
    expected = bytearray(before)
    def transform(address): put(expected, address, (get(expected, address)+(base if absolute else -base)) & 0xFFFFFFFF)
    for name in FIXED: transform(base+layout[name])
    for name, count in ARRAYS:
        for i in range(count): transform(base+layout[name]+i*4)
    for i in range(10):
        address = base+layout['released_object_tracking_references']+i*4
        if get(expected, address): transform(address)
    pool = base+layout['world_object_pool']
    for i in range(250):
        record = pool+i*68
        if expected[record+1] & 128: continue
        for offset in [56, 60]:
            address = record+offset
            if get(expected, address) not in [0, 0xFFFFFFFF]: transform(address)
    return expected


@pytest.mark.parametrize('record_index',[0,1,249])
@pytest.mark.parametrize('record_tag',[0,1,12,30,128,0xFFFF])
def test_load_copy_and_rebase_do_not_validate_player_record_format(original_image,layout,record_index,record_tag):
    """Supplied serialized RAM, not a disk acceptance or normal-save claim.

    Even an in-pool reference can designate a non-player tag. The copy/rebase
    continuation does not promote it to the player orientation layout.
    """
    base=0x90000
    memory=(ctypes.c_uint8*0x180000)()
    ctypes.memmove(ctypes.addressof(memory)+0x1000,original_image[0],len(original_image[0]))
    prefix=layout['savegame_prefix_rebased_long'];size=layout['app_SIZEOF']-prefix
    assert size==0x5EE4 and 4*(layout['SG2_SAVE_RESTORE_DBF_LAST']+1)==size
    source=layout['shared_workspace_prefix']
    memory[source:source+size]=bytes(size)
    pool=layout['world_object_pool'];record=pool+68*record_index
    put(memory,source+layout['player_object_reference']-prefix,record)
    put(memory,source+record-prefix,record_tag<<16)
    rotations=bytes.fromhex('01230abc0fff')
    memory[source+record-prefix+16:source+record-prefix+22]=rotations
    # Avoid sentinel links to unrelated scratch while preserving a real format tag.
    before_source=bytes(memory[source:source+size])
    memory[base+prefix-4:base+prefix]=b'\xA5'*4
    memory[base+layout['app_SIZEOF']:base+layout['app_SIZEOF']+4]=b'\xCC'*4
    cpu=state(memory,layout['copy_saved_workspace_prefix_loop']);cpu.a[6]=base
    cpu.a[0]=base+prefix;cpu.a[1]=source;cpu.d[1]=layout['SG2_SAVE_RESTORE_DBF_LAST']
    run(original_image,memory,cpu,{layout['deselect_disk_backend']},limit=30000)
    assert get(memory,base+layout['player_object_reference'])==base+record
    assert get(memory,base+record)>>16==record_tag
    assert bytes(memory[base+record+16:base+record+22])==rotations
    assert memory[base+layout['interrupted_game_available_flag']]==255
    assert bytes(memory[source:source+size])==before_source
    assert bytes(memory[base+prefix-4:base+prefix])==b'\xA5'*4
    assert bytes(memory[base+layout['app_SIZEOF']:base+layout['app_SIZEOF']+4])==b'\xCC'*4
    assert cpu.a[7]==STACK and get(memory,STACK)==RETURN


def test_save_command_tail_entry_adds_no_return_frame(original_image):
    """Post-key-translation command token, not physical keyboard delivery."""
    memory=(ctypes.c_uint8*0x180000)()
    ctypes.memmove(ctypes.addressof(memory)+0x1000,original_image[0],len(original_image[0]))
    put(memory,STACK,RETURN)
    cpu=state(memory,0x18C8);cpu.d[0]=0x123400A0
    run(original_image,memory,cpu,{0xFFEC})
    assert cpu.a[7]==STACK and get(memory,STACK)==RETURN


@pytest.mark.parametrize('discarded_return',[0x12EC,0x12345678,0xFFFFFF00])
def test_save_success_discards_one_return_long_then_jumps_to_game_resume(original_image,discarded_return):
    """After successful disk/fade helpers, whose device behavior is not tested."""
    memory=(ctypes.c_uint8*0x180000)()
    ctypes.memmove(ctypes.addressof(memory)+0x1000,original_image[0],len(original_image[0]))
    cpu=state(memory,0x1012E);before_d,before_a=list(cpu.d),list(cpu.a)
    put(memory,STACK,discarded_return);put(memory,STACK+4,0xA55AF00D)
    run(original_image,memory,cpu,{0x11E0})
    before_d[2]=discarded_return;before_a[7]=STACK+4
    assert list(cpu.d)==before_d and list(cpu.a)==before_a
    assert get(memory,STACK+4)==0xA55AF00D


def test_save_abort_discards_return_before_disk_cleanup_call(original_image,layout):
    memory=(ctypes.c_uint8*0x180000)()
    ctypes.memmove(ctypes.addressof(memory)+0x1000,original_image[0],len(original_image[0]))
    cpu=state(memory,0x1014C)
    put(memory,STACK,0x12345678);put(memory,STACK+4,0xA55AF00D)
    run(original_image,memory,cpu,{layout['deselect_disk_backend']})
    assert cpu.d[1]==0x12345678 and cpu.a[7]==STACK
    assert get(memory,STACK)==0x10152 and get(memory,STACK+4)==0xA55AF00D


def test_tractor_save_tail_restores_its_15_long_saved_frame_before_entering_save(original_image):
    """Explicit internal saved-frame precondition, not whole mission execution."""
    memory=(ctypes.c_uint8*0x180000)()
    ctypes.memmove(ctypes.addressof(memory)+0x1000,original_image[0],len(original_image[0]))
    saved=[0xA5500000+i for i in range(15)]
    for i,v in enumerate(saved):put(memory,STACK-60+4*i,v)
    put(memory,STACK,RETURN)
    cpu=state(memory,0x354DA);cpu.a[7]=STACK-60
    run(original_image,memory,cpu,{0xFFEC})
    assert list(cpu.d)==saved[:8] and list(cpu.a)[:7]==saved[8:]
    assert cpu.a[7]==STACK and get(memory,STACK)==RETURN


@pytest.mark.parametrize('base', [0x90000, 0x90004, 0xB0000])
@pytest.mark.parametrize('absolute', [False, True])
def test_all_original_transform_spans_and_guarded_links(original_image, layout, base, absolute):
    memory = sample(original_image, layout, base)
    entry = layout['restore_workspace_pointers_absolute' if absolute else 'serialize_workspace_pointers_relative']
    cpu = state(memory, entry); cpu.a[6] = base
    saved_d, saved_a = list(cpu.d), list(cpu.a)
    expected = model_transform(memory, layout, base, absolute)
    run(original_image, memory, cpu, {RETURN}, limit=15000)
    assert bytes(memory) == expected
    assert cpu.d[0] == base and cpu.d[1] == (saved_d[1] & 0xFFFF0000)|65535
    assert list(cpu.d)[2:] == saved_d[2:]
    assert cpu.a[0] == base+layout['app_SIZEOF'] and list(cpu.a)[1:7] == saved_a[1:7]
    assert cpu.a[7] == STACK+4


@pytest.mark.parametrize('base', [0x90000, 0x90004, 0xB0000])
def test_roundtrip_preserves_unconditional_slots_but_keeps_conditional_sentinel_collisions(original_image, layout, base):
    memory = sample(original_image, layout, base); before = bytes(memory)
    cpu = state(memory, layout['serialize_workspace_pointers_relative']); cpu.a[6] = base
    run(original_image, memory, cpu, {RETURN}, limit=15000)
    relative = model_transform(before, layout, base, False)
    assert bytes(memory) == relative
    cpu = state(memory, layout['restore_workspace_pointers_absolute']); cpu.a[6] = base
    run(original_image, memory, cpu, {RETURN}, limit=15000)
    expected = model_transform(relative, layout, base, True)
    assert bytes(memory) == expected
    for name in FIXED:
        address = base+layout[name]; assert get(memory, address) == get(before, address)
    for name, count in ARRAYS:
        start = base+layout[name]; assert bytes(memory[start:start+4*count]) == before[start:start+4*count]
    refs = base+layout['released_object_tracking_references']
    assert get(before, refs+8) == base and get(memory, refs+8) == 0
    pool = base+layout['world_object_pool']
    # Find exercised active links that become reserved relative encodings.
    lost = []
    for i in range(250):
        if before[pool+68*i+1] & 128: continue
        for offset in [56, 60]:
            address = pool+68*i+offset
            if get(before, address) in [base, base-1]:
                lost.append(address)
                assert get(memory, address) == (get(before, address)-base) & 0xFFFFFFFF
    assert len(lost) > 20
