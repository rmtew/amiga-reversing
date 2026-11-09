"""Original depot exchange continuations and message-pointer construction.

Recipe indices and readable backing are fixture preconditions, not a universal
service-id bound. Entry is after service dispatch (service 10 normally takes
the inventory path). Weapon subpaths are tested directly: the nine original reward
bytes do not select those branches. No complete dialogue/gameplay proof follows.
"""
import struct
import subprocess
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, STACK, RETURN
from tests.test_starglider2_cockpit_restore import symbols as cockpit_symbols, prepare

REQUIRED, REWARD = 0x390DC, 0x390E5
STOP, OFFER, COMPLETE = 0x34358, 0x34316, 0x34322


@pytest.fixture(scope='module')
def symbols(tmp_path_factory, original_image, cockpit_symbols):
    target = Path(__file__).resolve().parents[1] / 'targets/amiga_raw_starglider2_game'
    names = ['current_structure_service_id', 'shared_inventory_depot_message_pointers',
             'object_name_pointers', 'depot_trade_offer_template', 'depot_trade_completion_template']
    temp = tmp_path_factory.mktemp('depot-exchange-symbols'); asm, out = temp / 'fields.s', temp / 'fields.raw'
    asm.write_text((target / 'starglider2_game.s').read_text() + '\n dc.l ' + ','.join(names) + '\n')
    result = subprocess.run([str(target.parents[1] / 'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-m68000', '-no-opt',
                             '-I' + str(target / 'includes'), '-o', str(out), str(asm)],
                            cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    data = out.read_bytes(); tail = 4 * len(names); assert data[:-tail] == original_image[0]
    values = struct.unpack('>' + str(len(names)) + 'I', data[-tail:])
    result = dict(cockpit_symbols)
    result.update({n: v + (APP if i < 2 else 0) for i, (n, v) in enumerate(zip(names, values))})
    return result


def expected_message(memory, symbols, index, completed):
    template = symbols['depot_trade_completion_template' if completed else 'depot_trade_offer_template']
    directory = symbols['object_name_pointers']
    a, b, c = [get(memory, template + 4*i) for i in range(3)]
    return [a, b, get(memory, directory + 4*memory[REQUIRED + index]),
            c, get(memory, directory + 4*memory[REWARD + index]), 0xFFFFFFFF]


@pytest.mark.parametrize('index', range(9))
@pytest.mark.parametrize('completed', [False, True])
def test_original_recipe_tables_build_interleaved_text_pointer_list(original_image, memory, symbols, index, completed):
    dest = symbols['shared_inventory_depot_message_pointers']
    template = symbols['depot_trade_completion_template' if completed else 'depot_trade_offer_template']
    assert list(memory[REQUIRED:REQUIRED+9]) == [24, 55, 51, 71, 10, 73, 11, 3, 24]
    assert list(memory[REWARD:REWARD+9]) == [100, 83, 101, 102, 38, 29, 87, 73, 100]
    expected = expected_message(memory, symbols, index, completed)
    memory[dest-4:dest+28] = b'\xCC'*32
    cpu = state(memory, 0x3432E); cpu.d[0] = index
    cpu.a[0], cpu.a[1], cpu.a[2], cpu.a[3], cpu.a[4] = template, dest, REQUIRED, REWARD, symbols['object_name_pointers']
    run(original_image, memory, cpu, {RETURN})
    assert [get(memory, dest+4*i) for i in range(6)] == expected
    assert bytes(memory[dest-4:dest]) == bytes(memory[dest+24:dest+28]) == b'\xCC'*4
    assert cpu.a[0] == template+12 and cpu.a[1] == dest+20 and cpu.a[2] == REQUIRED and cpu.a[3] == REWARD
    assert cpu.d[0] == index and cpu.d[1] & 65535 == 4*memory[REWARD+index] and cpu.a[7] == STACK+4


@pytest.mark.parametrize('index', range(9))
@pytest.mark.parametrize('owned', [0, 1, 2])
@pytest.mark.parametrize('other', [0, 1, 2, 3])
def test_exchange_requires_below_three_counted_items_and_consumes_one_required_type(original_image, memory, symbols, index, owned, other):
    counts = symbols['model_type_population_counts']; dest = symbols['shared_inventory_depot_message_pointers']
    memory[counts:counts+104] = bytes(104)
    required, reward = memory[REQUIRED+index], memory[REWARD+index]
    memory[counts+required] = owned; memory[counts] = other
    before = bytes(memory[counts:counts+104]); expected = bytearray(before)
    completed = owned != 0 and owned + other < 3
    if completed: expected[required] -= 1; expected[reward] += 1
    put(memory, symbols['current_structure_service_id'], index+3, 2)
    memory[dest-4:dest+28] = b'\xCC'*32
    cpu = state(memory, 0x3425A); run(original_image, memory, cpu, {STOP})
    assert bytes(memory[counts:counts+104]) == expected
    assert [get(memory, dest+4*i) for i in range(6)] == expected_message(memory, symbols, index, completed)
    assert bytes(memory[dest-4:dest]) == bytes(memory[dest+24:dest+28]) == b'\xCC'*4
    assert cpu.a[7] == STACK and cpu.a[6] == APP


@pytest.mark.parametrize('count', [0, 1, 126, 127, 128, 129, 254, 255])
def test_ordinary_reward_increment_clamps_only_negative_byte_result(original_image, memory, symbols, count):
    counts = symbols['model_type_population_counts']; reward = memory[REWARD]
    memory[counts+reward] = count
    cpu = state(memory, 0x342A8); cpu.d[0] = 0; cpu.a[0] = counts; cpu.a[3] = REWARD
    run(original_image, memory, cpu, {OFFER, COMPLETE})
    value = (count+1) & 255
    assert cpu.pc == COMPLETE and memory[counts+reward] == (127 if value & 128 else value)


@pytest.mark.parametrize('homing', [False, True])
@pytest.mark.parametrize('count', [0, 3, 4, 126, 127, 128, 131, 132, 254, 255])
def test_direct_weapon_reward_subpaths_preserve_byte_overflow_and_n_only_compare(original_image, memory, symbols, homing, count):
    prepare(memory, symbols)
    for name in ['homing_missile_hud_icon_count', 'bouncing_bomb_hud_icon_count']: put(memory, symbols[name], 0, 2)
    kind = 12 if homing else 91; counts = symbols['model_type_population_counts']; memory[counts+kind] = count
    cpu = state(memory, 0x342CA if homing else 0x342F0); cpu.d[1] = kind; cpu.a[0] = counts
    calls = []
    def observe(pc):
        if pc in (symbols['add_homing_missile_hud_icon'], symbols['add_bouncing_bomb_hud_icon']): calls.append(pc)
    run(original_image, memory, cpu, {OFFER, COMPLETE}, observe)
    incremented = (count+1) & 255; accepted = bool(((incremented-5) & 255) & 128)
    assert memory[counts+kind] == (incremented if accepted else 4)
    assert cpu.pc == (COMPLETE if accepted else OFFER) and cpu.a[7] == STACK
    assert len(calls) == int(accepted)
    name = 'homing_missile_hud_icon_count' if homing else 'bouncing_bomb_hud_icon_count'
    assert get(memory, symbols[name], 2) == int(accepted)
