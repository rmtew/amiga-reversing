"""Original attack clocks, damage branches, charge pixels and paired feedback."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer
from tests.test_pandora_framebuffer_lifetime import fill_rows

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
APP, OPPONENT, PLAYER = 0x39FC, 0x82000, BASE+0x4C322
PRIMARY, SECONDARY = BASE+0x485B2, BASE+0x485CC
PRIMARY_DESC, SECONDARY_DESC = BASE+0x4859A, BASE+0x485A6
IDLE, FEEDBACK_TABLE = BASE+0x48588, BASE+0x485E6


def combat(cpu_fixture, slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6], cpu.a[5] = APP, OPPONENT
    write(APP+slots['app_interaction_object_ptr'], OPPONENT)
    return cpu, memory, schemas['world_object_shared_prefix'], read, write, run


def test_all_item_bytes_select_seven_weapon_pairs_or_exact_fallback(cpu_fixture,title_slots):
    cpu,memory,obj,read,write,run = combat(cpu_fixture,title_slots)
    reloads,damages = (4,5,2,1,4,3,2),(35,21,9,7,25,14,8)
    for item in range(256):
        write(OPPONENT+obj['selected_item_id'],item,1)
        cpu.d[0],cpu.d[1] = 0xABCD1234,0xBEEF5678
        before_a = list(cpu.a[:7])
        run(0x864C)
        if 7<=item<14:
            assert cpu.d[0] == 0xABCD0000|reloads[item-7]
            assert cpu.d[1] == 0xBEEF0000|damages[item-7]
            assert cpu.sr&1
        else:
            assert list(cpu.d[:2]) == [3,5] and not cpu.sr&1
        assert list(cpu.a[:7]) == before_a


def test_equipment_setup_applies_cached_kriptonite_then_specific_actor_overrides(cpu_fixture,title_slots):
    cpu,memory,obj,read,write,run = combat(cpu_fixture,title_slots)
    from amiga_reversing.disasm.effective_metadata import effective_target_metadata
    from amiga_reversing.disasm.project_paths import resolve_project_paths
    from tests.test_pandora_state_transitions import TARGET
    constants = {e.name:e.value for e in effective_target_metadata(resolve_project_paths(TARGET).target_dir).target_equates}
    bit = constants['GAME_EVENT_KRIPTONITE_CACHED_BIT']
    for actor in [0,constants['ITEM_ID_ICELORD'],constants['ITEM_ID_THIEF']]:
        for item in [0,7,constants['ITEM_ID_SONICBLASTER'],constants['ITEM_ID_SONICDRIVER']]:
            for cached in [0,1]:
                write(OPPONENT+obj['item_definition_id'],actor,1)
                write(OPPONENT+obj['selected_item_id'],0,1)
                write(PLAYER+obj['selected_item_id'],item,1)
                write(APP+title_slots['app_game_event_flags'],cached<<bit,1)
                write(OPPONENT+obj['world_x'],400,2)
                write(PLAYER+obj['world_x'],800,2)
                advance = sequencer(cpu,memory,write)
                assert advance(0x77B8,stop=0x786C).stop_reason == 1
                own_reload,own_damage = ((4,35) if item==7 else (3,5))
                if 7<=item<14:
                    own_reload = [4,5,2,1,4,3,2][item-7]
                    own_damage = [35,21,9,7,25,14,8][item-7]
                other_reload,other_damage = 3,5>>cached
                if actor==constants['ITEM_ID_ICELORD']:
                    if item==constants['ITEM_ID_SONICBLASTER']:own_reload,own_damage = 2,50
                    if item==constants['ITEM_ID_SONICDRIVER']:own_reload,own_damage = 2,20
                elif actor==constants['ITEM_ID_THIEF']:other_reload,other_damage = 2,50
                for side,reload,damage in [('player',own_reload,own_damage),('opponent',other_reload,other_damage)]:
                    assert read(APP+title_slots[f'app_{side}_attack_charge_countdown'],1) == reload
                    assert read(APP+title_slots[f'app_{side}_attack_charge_reload'],1) == reload
                    assert read(APP+title_slots[f'app_{side}_attack_damage'],1) == damage
                assert read(OPPONENT+obj['world_x'],2) == 10400
                assert read(PLAYER+obj['world_x'],2) == 10800


def test_opponent_clock_uses_byte_countdown_low_charge_byte_and_extra_step_for_reload_one(cpu_fixture,title_slots):
    cpu,memory,obj,read,write,run = combat(cpu_fixture,title_slots)
    write(APP+0x7EE,0xFFFF,2)  # Workspace selector, distinct from absolute $7EE.
    write(OPPONENT+0x40,0,2)  # Force every attempted attack to fail its comparand gate.
    for reload in [0,1,2,255]:
        for countdown in [0,1,2,255]:
            for charge in [0,20,21,22,23,24,255,256,0xFFFF]:
                write(APP+title_slots['app_opponent_attack_charge_countdown'],countdown,1)
                write(APP+title_slots['app_opponent_attack_charge_reload'],reload,1)
                write(APP+title_slots['app_opponent_attack_charge'],charge,2)
                cpu.a[5] = OPPONENT
                assert sequencer(cpu,memory,write)(0x78DE,stop=0x7938,budget=64).stop_reason == 1
                count = (countdown-1)&255
                expected = charge
                if count==0:
                    count = reload
                    expected = (charge+1+(reload==1))&0xFFFF
                    if expected&255>=23:expected = 0
                assert read(APP+title_slots['app_opponent_attack_charge_countdown'],1) == count
                assert read(APP+title_slots['app_opponent_attack_charge'],2) == expected


def test_opponent_attack_gate_compares_only_low_bytes_and_accepts_equality(cpu_fixture,title_slots):
    cpu,memory,obj,read,write,run = combat(cpu_fixture,title_slots)
    for selector in range(256):
        half = selector>>1
        for value in sorted({0,255,max(0,half-1),half,min(255,half+1)}):
            write(APP+0x7EE,0xA500|selector,2)
            write(OPPONENT+0x40,0x5A00|value,2)
            cpu.a[5] = OPPONENT
            hit = value>=half
            assert sequencer(cpu,memory,write)(0x7906,stop=0x791A if hit else 0x7938,budget=24).stop_reason == 1
            assert cpu.d[0]&255 == half and cpu.d[1]&255 == value


@pytest.mark.parametrize('side',['player','opponent'])
def test_damage_uses_unsigned_borrow_for_player_but_result_sign_for_opponent(cpu_fixture,title_slots,side):
    cpu,memory,obj,read,write,run = combat(cpu_fixture,title_slots)
    for hp in range(256):
        for damage in [0,1,50,128,255]:
            address = PLAYER if side=='player' else OPPONENT
            write(address+obj['hit_points'],0xA500|hp,2)
            result = (hp-damage)&255
            if side=='player':
                cpu.a[4] = PLAYER
                write(APP+title_slots['app_opponent_attack_damage'],damage,1)
                dead = hp<=damage
                entry,stop = 0x7920,(0x79A8 if dead else 0x7934)
            else:
                cpu.a[5],cpu.d[0] = OPPONENT,damage
                dead = result==0 or bool(result&128)
                entry,stop = 0x796C,(0x79E4 if dead else 0x797C)
            assert sequencer(cpu,memory,write)(entry,stop=stop,budget=16).stop_reason == 1
            expected = hp if side=='player' and dead else result
            assert read(address+obj['hit_points'],2) == 0xA500|expected
    # Synthetic high health/damage bytes expose original branch semantics;
    # this does not admit those states through the full encounter entry.


def test_player_fire_uses_half_full_and_discard_windows_on_charge_low_byte(cpu_fixture,title_slots):
    cpu,memory,obj,read,write,run = combat(cpu_fixture,title_slots)
    for high in [0,1,255]:
        for low in range(256):
            for fire in [0,255]:
                charge = (high<<8)|low
                write(APP+title_slots['app_player_attack_charge'],charge,2)
                write(APP+title_slots['app_player_attack_damage'],255,1)
                write(APP+title_slots['app_input_fire_pressed_ff'],fire,1)
                attack = bool(fire) and 17<=low<25
                assert sequencer(cpu,memory,write)(0x7938,stop=0x796C if attack else 0x7980,budget=32).stop_reason == 1
                if attack:assert cpu.d[0]&255 == (127 if low<23 else 255)
                assert read(APP+title_slots['app_player_attack_charge'],2) == (0 if fire and low<17 else charge)


def test_player_clock_requires_overlay_sign_and_has_inverse_reload_one_step(cpu_fixture,title_slots):
    cpu,memory,obj,read,write,run = combat(cpu_fixture,title_slots)
    descriptor = BASE+0x335A
    # TST.W starts at the one-byte state_flags field; its high bit gates work.
    write(descriptor+cpu_fixture[2]['ui_overlay_descriptor']['state_flags'],0x7FFF,2)
    write(APP+title_slots['app_player_attack_charge_countdown'],1,1)
    write(APP+title_slots['app_player_attack_charge'],10,2)
    assert sequencer(cpu,memory,write)(0x817A).stop_reason == 1
    assert read(APP+title_slots['app_player_attack_charge_countdown'],1) == 1
    assert read(APP+title_slots['app_player_attack_charge'],2) == 10
    write(descriptor+cpu_fixture[2]['ui_overlay_descriptor']['state_flags'],0x8000,2)
    for reload in [0,1,2,255]:
        for countdown in [0,1,2,255]:
            for charge in [0,39,40,41,65534,65535]:
                write(APP+title_slots['app_player_attack_charge_countdown'],countdown,1)
                write(APP+title_slots['app_player_attack_charge_reload'],reload,1)
                write(APP+title_slots['app_player_attack_charge'],charge,2)
                assert sequencer(cpu,memory,write)(0x817A,stop=0x81B2).stop_reason == 1
                count = (countdown-1)&255
                expected = charge
                if count==0:
                    count = reload
                    expected = (charge+1+(reload!=1))&0xFFFF
                    if expected>40:expected = 0
                assert read(APP+title_slots['app_player_attack_charge_countdown'],1) == count
                assert read(APP+title_slots['app_player_attack_charge'],2) == expected


def test_charge_gauge_all_41_normal_charges_match_complete_cpu_pixel_writes(cpu_fixture,title_slots):
    cpu,memory,obj,read,write,run = combat(cpu_fixture,title_slots)
    fill_rows(cpu,memory,run)
    descriptor = BASE+0x335A
    write(descriptor+cpu_fixture[2]['ui_overlay_descriptor']['state_flags'],0x8000,2)
    x,y = read(descriptor,1),read(descriptor+1,1)
    origin = 0x70000+1280*((y+1)&31)+((x+1)&63)
    assert origin&1
    patterns = bytes(memory[BASE+0x82D4:BASE+0x82E8])
    masks = bytes(memory[BASE+0x82E8:BASE+0x82F0])
    for charge in range(41):
        memory[0x70000:0x78000] = b'\xA5'*0x8000
        expected = bytearray(memory[0x70000:0x78000])
        for row in range(24):
            offset = origin+160+40*row-0x70000
            expected[offset:offset+5] = bytes(5)
        full,remainder = divmod(charge,8)
        for cell in range(full):
            for row in range(24):expected[origin+160+40*row+cell-0x70000] = patterns[4*cell+row%4]
        if remainder:
            for row in range(24):expected[origin+160+40*row+full-0x70000] = patterns[4*full+row%4]&masks[remainder]
        write(APP+title_slots['app_player_attack_charge'],charge,2)
        write(APP+title_slots['app_player_attack_charge_countdown'],2,1)
        assert sequencer(cpu,memory,write)(0x817A,budget=3000).stop_reason == 1
        assert bytes(memory[0x70000:0x78000]) == expected
        assert read(APP+title_slots['app_text_cursor_ptr']) == origin+full
    # Trace write ranges may overflow; complete memory and fences are compared.


@pytest.mark.parametrize('side,entry,state,descriptor',[('player',0x7A94,PRIMARY,PRIMARY_DESC),('opponent',0x7AE8,SECONDARY,SECONDARY_DESC)])
def test_feedback_uses_distinct_selector_bits_and_actor_coordinates_then_restores_registers(cpu_fixture,title_slots,side,entry,state,descriptor):
    cpu,memory,obj,read,write,run = combat(cpu_fixture,title_slots)
    choices = [read(FEEDBACK_TABLE+4*i) for i in range(9)]
    assert choices == [BASE+0x484F8+18*i for i in range(9)]
    for selector in range(256):
        write(APP+0x7EF,selector,1)
        for address,x,y in [(PLAYER,10000+selector,0xAB00|selector),(OPPONENT,11000+selector,0xCD00|selector)]:
            write(address+obj['world_x'],x,2)
            write(address+obj['world_y'],y,2)
        for i in range(8):
            cpu.d[i] = 0xABCD0000+i
            if i<6:cpu.a[i] = 0xCAFE0000+i
        cpu.a[6] = APP
        saved_d,saved_a = list(cpu.d),list(cpu.a[:7])
        assert sequencer(cpu,memory,write)(entry,budget=5000).stop_reason == 1
        choice = ((selector&28)>>2) if side=='player' else selector&7
        assert read(state) == read(state+4) == choices[choice]
        assert read(descriptor+4,2) == selector+(0 if side=='player' else 1000)
        assert read(descriptor+6,2) == (0xAB00 if side=='player' else 0xCD00)|selector
        assert read(APP+title_slots[f'app_{side}_hit_feedback_ticks_remaining'],1) == 10
        assert list(cpu.d) == saved_d and list(cpu.a[:7]) == saved_a and cpu.a[7] == 0x9004


def test_feedback_expiry_and_clear_change_current_geometry_but_retain_previous(cpu_fixture,title_slots):
    cpu,memory,obj,read,write,run = combat(cpu_fixture,title_slots)
    for player in [0,1,2,255]:
        for opponent in [0,1,2,255]:
            for state,value in [(PRIMARY,0x12345678),(SECONDARY,0x87654321)]:
                write(state,value)
                write(state+4,0xABCD1234)
            for side,count in [('player',player),('opponent',opponent)]:write(APP+title_slots[f'app_{side}_hit_feedback_ticks_remaining'],count,1)
            run(0x7B3C)
            for side,state,value,count in [('player',PRIMARY,0x12345678,player),('opponent',SECONDARY,0x87654321,opponent)]:
                assert read(APP+title_slots[f'app_{side}_hit_feedback_ticks_remaining'],1) == (count-1 if count else 0)
                assert read(state) == (IDLE if count==1 else value)
                assert read(state+4) == 0xABCD1234
            counts = [read(APP+title_slots[f'app_{side}_hit_feedback_ticks_remaining'],1) for side in ['player','opponent']]
            run(0x7B6E)
            assert read(PRIMARY) == read(SECONDARY) == IDLE
            assert read(PRIMARY+4) == read(SECONDARY+4) == 0xABCD1234
            assert [read(APP+title_slots[f'app_{side}_hit_feedback_ticks_remaining'],1) for side in ['player','opponent']] == counts


def test_original_grid_builder_supplies_the_overlapping_combat_selector(cpu_fixture,title_slots):
    cpu,memory,obj,read,write,run = combat(cpu_fixture,title_slots)
    from tests.test_pandora_state_transitions import RETURN
    for name,value,size in [('app_tilemap_base',0x4000,4),('app_tilemap_width',90,2),('app_tilemap_height',129,2)]:
        write(APP+title_slots[name],value,size)
    write(APP+0x7EE,0xDEAD,2)
    tile_id = read(BASE+0x3502+2*10,2)
    offset = read(BASE+0x3F16+18*tile_id+10,2)
    pointer = BASE+0xD0A8+offset
    assert tile_id==131 and offset==0x6F00 and pointer==0x23FA8
    advance = sequencer(cpu,memory,write)
    cpu.a[7] = 0x98000
    write(0x98000,RETURN)
    assert advance(0xA198,budget=100000).stop_reason == 1
    assert APP+0x7EE == 0x4000+122*4+2
    assert read(0x4000+122*4) == pointer
    assert read(APP+0x7EE,2) == 0x3FA8 and read(APP+0x7EF,1) == 0xA8
    all_offsets = [read(BASE+0x3F16+2*i,2) for i in range(468*9)]
    assert all(o%128==0 for o in all_offsets)
    assert {((BASE+0xD0A8+o)&28)>>2 for o in all_offsets} == {2}
    assert {(BASE+0xD0A8+o)&7 for o in all_offsets} == {0}
    for address in [PLAYER,OPPONENT]:
        write(address+obj['world_x'],10001,2)
        write(address+obj['world_y'],200,2)
    for entry,state,index in [(0x7A94,PRIMARY,2),(0x7AE8,SECONDARY,0)]:
        cpu.a[7] = 0x98000
        write(0x98000,RETURN)
        assert advance(entry,budget=5000).stop_reason == 1
        assert read(state) == read(FEEDBACK_TABLE+4*index)
        assert read(APP+0x7EF,1) == 0xA8
    for value,stop in [(83,0x7938),(84,0x791A)]:
        cpu.a[5],cpu.a[7] = OPPONENT,0x98000
        write(0x98000,RETURN)
        write(OPPONENT+0x40,value,2)
        assert advance(0x7906,stop=stop,budget=24).stop_reason == 1
        assert cpu.d[0]&255 == 84
    # Fixed A6 and the original initializer establish this writer/alias witness.
    # Other grid writes and remapped workspaces are not excluded by this test.
