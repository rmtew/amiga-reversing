"""Original descriptor/world traversals; bounded valid chains, no DMA timing claim."""
from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots

APP = 0x39FC
TABLE = 0x80000
DESCRIPTORS = (0x81000, 0x81020, 0x81040)
STATES = (0x82000, 0x82040, 0x82080)


def activate(cpu_fixture, slots, count=2):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    write(APP+slots['app_active_world_object_ptr_table'], TABLE)
    write(APP+slots['active_world_object_count'], count, 2)
    for i, descriptor in enumerate(DESCRIPTORS):
        write(TABLE+4*i, descriptor)
    return schemas['world_position_descriptor_prefix'], schemas['world_position_state_record']


def test_counted_traversals_bypass_null_tables_and_zero_counts(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    for source in (0x2466, 0x248A, 0x24AE, 0x24FE):
        for table, count in ((0, 123), (TABLE, 0)):
            write(APP+title_slots['app_active_world_object_ptr_table'], table)
            write(APP+title_slots['active_world_object_count'], count, 2)
            before = bytes(memory[TABLE:0x83000])
            run(source)
            assert memory[TABLE:0x83000] == before and cpu.a[7] == 0x9004


def test_snapshot_copies_xy_and_all_attachment_geometry_only_for_counted_descriptors(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    descriptor, state = activate(cpu_fixture, title_slots)
    write(DESCRIPTORS[0]+descriptor['position_state_ptr'], STATES[0])
    write(STATES[0]+state['attachment_state_ptr'], STATES[1])
    for i, address in enumerate(DESCRIPTORS):
        write(address+descriptor['world_x'], 0x12345678+i)
        write(address+descriptor['previous_world_x'], 0xA5A5A5A5)
    for i, address in enumerate(STATES):
        write(address+state['current_geometry_ptr'], 0x60000+0x100*i)
        write(address+state['previous_geometry_ptr'], 0xA5A5A5A5)
        write(address+state['interaction_flags'], 255, 1)
    run(0x24AE)
    for address in DESCRIPTORS[:2]:
        assert read(address+descriptor['previous_world_x']) == read(address+descriptor['world_x'])
    assert read(DESCRIPTORS[2]+descriptor['previous_world_x']) == 0xA5A5A5A5
    for address in STATES[:2]:
        assert read(address+state['previous_geometry_ptr']) == read(address+state['current_geometry_ptr'])
        assert read(address+state['interaction_flags'], 1) == 255
    assert read(STATES[2]+state['previous_geometry_ptr']) == 0xA5A5A5A5
    assert cpu.a[0] == TABLE+8 and cpu.d[7] & 65535 == 65535


def test_xy_wrapper_walks_35_objects_but_repeats_inherited_a5_copy(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    obj, descriptor = schemas['world_object_shared_prefix'], schemas['world_position_descriptor_prefix']
    inherited, destination = 0x80000, 0x81000
    write(inherited+obj['position_descriptor_ptr'], destination)
    write(inherited+obj['world_x'], 0x0123FEDC)
    cpu.a[5] = inherited
    original_image = bytes(memory[BASE:BASE+349040])
    run(0x24F0, budget=1024)
    assert read(destination+descriptor['world_x']) == 0x0123FEDC
    assert cpu.a[5] == inherited
    assert cpu.a[1] == BASE+0x309A  # Thirty-five original entries and NULL.
    assert cpu.a[0] == read(BASE+0x300A+34*4)
    assert memory[BASE:BASE+349040] == original_image


def test_draw_and_restore_wrappers_visit_counted_empty_geometry_chains(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    descriptor, state = activate(cpu_fixture, title_slots)
    write(DESCRIPTORS[0]+descriptor['position_state_ptr'], STATES[0])
    write(STATES[0]+state['attachment_state_ptr'], STATES[1])
    write(DESCRIPTORS[1]+descriptor['position_state_ptr'], STATES[2])
    before = bytes(memory[TABLE:0x83000])
    for source in (0x2466, 0x248A):
        run(source, budget=512)
        assert cpu.a[1] == TABLE+8 and cpu.d[7] & 65535 == 65535
        assert cpu.a[7] == 0x9004 and memory[TABLE:0x83000] == before
    # Zero geometry pointers avoid all Blitter work; this proves traversal and
    # caller loop-state preservation, not rendering or background restoration.


def test_animation_wrapper_skips_flagged_state_but_advances_following_attachment(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    descriptor, state = activate(cpu_fixture, title_slots)
    node = schemas['WorldPositionStateNode']
    write(DESCRIPTORS[0]+descriptor['position_state_ptr'], STATES[0])
    write(STATES[0]+state['attachment_state_ptr'], STATES[1])
    write(STATES[0]+state['interaction_flags'], 1, 1)
    write(STATES[0]+state['state_node_ptr'], 0xFFFFF0)  # Must never be followed.
    write(STATES[1]+state['state_node_ptr'], 0x85000)
    write(0x85000+node['frame_sequence_ptr'], 0x86000)
    write(0x85000+node['frame_index_and_phase'], 0x1201, 2)
    write(0x85000+node['phase_step'], 2, 1)
    run(0x24FE)
    assert read(0x85000+node['frame_index_and_phase'], 2) == 0x1203
    assert read(STATES[0]+state['state_node_ptr']) == 0xFFFFF0
    assert cpu.a[4] == STATES[1]  # Direct update retains its owning state.
    assert cpu.a[0] == TABLE+8 and cpu.d[7] & 65535 == 65535 and cpu.a[7] == 0x9004


def test_script_wrapper_filters_both_flag_bits_before_even_delay_service(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    obj = schemas['world_object_shared_prefix']
    objects = [read(BASE+0x300A+4*i) for i in range(35)]
    assert len(set(objects)) == 35 and read(BASE+0x300A+35*4) == 0
    flags = [0, 2, 64, 66, 4, 128]
    for i, address in enumerate(objects):
        write(address+obj['world_object_flags'], flags[i % len(flags)], 1)
        write(address+obj['behavior_script_ptr'], 0x80000)
        write(address+obj['behavior_script_delay_ticks'], 2, 2)
    run(0x253C, budget=2048)
    for i, address in enumerate(objects):
        value = flags[i % len(flags)]
        assert read(address+obj['behavior_script_delay_ticks'], 2) == (2 if value & 66 else 1)
        assert read(address+obj['world_object_flags'], 1) == value
        assert read(address+obj['behavior_script_ptr']) == 0x80000
    assert cpu.a[0] == BASE+0x309A and cpu.a[7] == 0x9004
