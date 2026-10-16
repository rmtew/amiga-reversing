"""Original callback/queue CPU paths in bounded modeled contexts, without hardware."""
from __future__ import annotations

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import TARGET, BASE, cpu_fixture

APP = 0x70000


@pytest.fixture
def diabetic_fixture(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    metadata = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    constants = {e.name: e.value for e in metadata.target_equates}
    slots = {r.symbol: r.offset for r in metadata.rsset_layout_regions if r.symbol}
    obj = schemas['world_object_shared_prefix']
    state = schemas['world_position_state_record']
    node_fields = schemas['WorldPositionStateNode']
    giver, player = BASE + 0x4B728, BASE + 0x4C322
    cpu.a[5], cpu.a[6] = giver, APP
    run(0x13F4)
    primary = read(read(giver + obj['position_descriptor_ptr']))
    attachment = read(primary + state['attachment_state_ptr'])
    node = read(attachment + state['state_node_ptr'])
    assert node == BASE + 0x4B814
    # A preactivated queue with one valid message avoids entering text drawing.
    # The original enqueue body tests bit 5 at A6+$2A6 and bounds tail at +$272.
    queue = APP + slots['app_scrolling_message_queue_head']
    write(queue, BASE + 0x4CFB4)
    write(queue+4, 0)
    write(APP + slots['app_scrolling_message_queue_tail'], queue+4)
    write(APP + 0x2A6, 1 << 5, 1)
    write(giver + obj['selected_item_id'], constants['ITEM_ID_HYPODERMIC'], 1)
    write(player + obj['selected_item_id'], constants['ITEM_ID_INSULIN'], 1)
    write(giver + obj['context_prompt_cooldown'], 77, 2)
    write(player + obj['world_x'], read(giver + obj['world_x'], 2), 2)
    write(player + obj['world_y'], read(giver + obj['world_y'], 2), 2)
    return cpu, memory, schemas, read, write, run, constants, slots, giver, player, attachment, node, queue


def pose_snapshot(memory, attachment, node):
    return (bytes(memory[attachment:attachment+26]),
            bytes(memory[node:node+26]))  # Node and its two pointer slots.


@pytest.mark.parametrize('dx,dy,accepted', [(0, 0, True), (23, 15, True),
                                           (24, 0, False), (0, 16, False),
                                           (-23, -15, True), (-24, 0, False),
                                           (0, -16, False)])
def test_treatment_latches_advice_without_consuming_items_or_replacing_pose(diabetic_fixture, dx, dy, accepted):
    cpu, memory, schemas, read, write, run, constants, slots, giver, player, attachment, node, queue = diabetic_fixture
    obj = schemas['world_object_shared_prefix']
    write(player + obj['world_x'], read(giver + obj['world_x'], 2) + dx, 2)
    write(player + obj['world_y'], read(giver + obj['world_y'], 2) + dy, 2)
    before_object = bytes(memory[giver:giver+84])
    before_player = bytes(memory[player:player+84])
    inventory_ranges = [read(owner + obj['inventory_slots_ptr']) for owner in [giver, player]]
    before_inventories = [bytes(memory[a:a+8]) for a in inventory_ranges]
    before_pose = pose_snapshot(memory, attachment, node)
    tail_slot = APP + slots['app_scrolling_message_queue_tail']
    flags = APP + slots['app_world_interaction_flags']
    run(0x4D568, budget=4096)  # Actual range helper and both enqueue bodies.
    assert cpu.a[5] == giver and not cpu.sr & 1
    assert bytes(memory[giver:giver+84]) == before_object
    assert bytes(memory[player:player+84]) == before_player
    assert pose_snapshot(memory, attachment, node) == before_pose
    assert read(player + obj['selected_item_id'], 1) == constants['ITEM_ID_INSULIN']
    assert [bytes(memory[a:a+8]) for a in inventory_ranges] == before_inventories
    assert bool(read(flags, 1) & (1 << constants['INTERACTION_FLAG_DIABETIC_TREATED'])) == accepted
    if accepted:
        assert read(queue+4) == BASE + 0x4CFE0
        assert read(queue+8) == BASE + 0x4D011
        assert read(tail_slot) == queue+12 and read(queue+12) == 0
        # The latch prevents repeat advice, independently of pose/script state.
        run(0x4D568, budget=4096)
        assert read(tail_slot) == queue+12
        run(0xA07C, stop=0xA080)  # Original global interaction-flags reset.
        assert read(flags, 1) == 0
        run(0x4D568, budget=4096)
        assert read(tail_slot) == queue+20
    else:
        assert read(tail_slot) == queue+4
    assert pose_snapshot(memory, attachment, node) == before_pose


@pytest.mark.parametrize('has_needle,carried_slot,message', [
    (False, None, 0x4CFB4), (True, None, 0x4CF8E),
    (True, 0, None), (True, 3, None), (True, 4, 0x4CF8E),
])
def test_diabetic_prompts_distinguish_missing_needle_from_carried_insulin(diabetic_fixture, has_needle, carried_slot, message):
    cpu, memory, schemas, read, write, run, constants, slots, giver, player, attachment, node, queue = diabetic_fixture
    obj = schemas['world_object_shared_prefix']
    if not has_needle:
        write(giver + obj['selected_item_id'], 0, 1)
    else:
        write(player + obj['selected_item_id'], 54, 1)
    carried = APP + slots['app_carried_item_ids']
    if carried_slot is not None:
        write(carried + carried_slot, constants['ITEM_ID_INSULIN'], 1)
    old_message = read(giver + obj['interaction_message_ptr'])
    before_pose = pose_snapshot(memory, attachment, node)
    run(0x4D568, budget=4096)
    assert cpu.a[5] == giver and bool(cpu.sr & 1) == (message is not None)
    assert read(giver + obj['interaction_message_ptr']) == (BASE + message if message is not None else old_message)
    assert read(giver + obj['context_prompt_cooldown'], 2) == (250 if message is not None else 77)
    assert read(APP + slots['app_world_interaction_flags'], 1) == 0
    assert read(APP + slots['app_scrolling_message_queue_tail']) == queue+4
    assert pose_snapshot(memory, attachment, node) == before_pose


def test_full_queue_still_latches_advice_and_pose_loop_continues(diabetic_fixture):
    cpu, memory, schemas, read, write, run, constants, slots, giver, player, attachment, node, queue = diabetic_fixture
    obj = schemas['world_object_shared_prefix']
    state = schemas['world_position_state_record']
    fields = schemas['WorldPositionStateNode']
    limit = APP + 0x272  # Grounded original LEA/cmp bound in enqueue.
    for offset in range(0, limit-queue, 4):
        write(queue+offset, BASE + 0x4CFB4)
    tail_slot = APP + slots['app_scrolling_message_queue_tail']
    write(tail_slot, limit)
    before_queue = bytes(memory[queue:limit+4])
    before_pose = pose_snapshot(memory, attachment, node)
    run(0x4D568, budget=4096)
    assert read(APP + slots['app_world_interaction_flags'], 1) & (1 << constants['INTERACTION_FLAG_DIABETIC_TREATED'])
    assert not cpu.sr & 1 and read(tail_slot) == limit
    assert bytes(memory[queue:limit+4]) == before_queue
    assert pose_snapshot(memory, attachment, node) == before_pose
    # Original script still reaches its hold toggle after the 100-count delay.
    for _ in range(100):
        run(0x13F4)
    assert read(giver + obj['behavior_script_ptr']) == BASE + 0x21E6
    assert read(giver + obj['behavior_script_delay_ticks'], 2) == 6
    assert read(attachment + state['state_node_ptr']) == node
    assert read(node + fields['mode_flags'], 1) == 1
    for _ in range(32):
        cpu.a[4] = attachment
        run(0x951A)
        assert read(attachment + state['state_node_ptr']) == node
        assert read(attachment + state['current_geometry_ptr']) == BASE + 0x4B78E
    for _ in range(6):
        run(0x13F4)
    cpu.a[4] = attachment
    run(0x951A)
    assert read(node + fields['mode_flags'], 1) == 0
    assert read(attachment + state['state_node_ptr']) == node
    assert read(attachment + state['current_geometry_ptr']) == BASE + 0x4B77C
    for _ in range(32):
        cpu.a[4] = attachment
        run(0x951A)
        assert read(attachment + state['state_node_ptr']) == node
        assert read(node + fields['mode_flags'], 1) == 0
        assert read(attachment + state['current_geometry_ptr']) == BASE + 0x4B77C
