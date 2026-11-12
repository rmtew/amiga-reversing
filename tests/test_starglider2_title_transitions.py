"""Original title predicates, command unwind and matched-phrase continuations.

Supplied RAM/keys cover these local CPU paths. They do not stand in for keyboard
delivery, music/fade completion, disk I/O, or whole-menu/gameplay qualification.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, STACK, RETURN

NAMES = ['pending_key_scancode', 'mouse_primary_button_flag', 'primary_fire_flag',
         'title_idle_rate_windows_remaining', 'title_page_cycle_counter',
         'debug_features_enabled_flag', 'fixed_sight_mode_flag', 'negative_speed_control_accumulator',
         'icarus_power_reserve', 'icarus_shield_strength', 'weapon_energy_reserve']


@pytest.fixture(scope='module')
def fields(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder = tmp_path_factory.mktemp('title-transitions'); asm, out = folder/'fields.s', folder/'fields.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(NAMES)+'\n')
    result = subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'), '-quiet', '-m68000',
        '-no-opt', '-Fbin', '-I'+str(target/'includes'), '-o', str(out), str(asm)], cwd=target,
        capture_output=True, text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    raw = out.read_bytes(); assert raw[:-4*len(NAMES)] == original_image[0]
    return {n:APP+v for n,v in zip(NAMES,struct.unpack('>'+'I'*len(NAMES),raw[-4*len(NAMES):]))}


def poll(image, m, f, key, mouse, fire, remaining, page):
    m[f['pending_key_scancode']] = key
    m[f['mouse_primary_button_flag']] = mouse
    m[f['primary_fire_flag']] = fire
    put(m,f['title_idle_rate_windows_remaining'],remaining,2)
    put(m,f['title_page_cycle_counter'],page,2)
    # Continuation after the original PRNG call, stopping before the next call.
    cpu = state(m,0x118E)
    run(image,m,cpu,{0x118A,0x11C6,0x11EE,0x116A,0x34AA})
    return cpu


@pytest.mark.parametrize('key',[1,128,255])
@pytest.mark.parametrize('mouse,fire',[(0,0),(1,0),(0,1),(255,255)])
@pytest.mark.parametrize('remaining',[0,65535])
def test_any_title_key_wins_over_fire_and_expiry(original_image,memory,fields,key,mouse,fire,remaining):
    cpu = poll(original_image,memory,fields,key,mouse,fire,remaining,1)
    assert cpu.pc == 0x11C6 and cpu.a[7] == STACK


@pytest.mark.parametrize('mouse,fire',[(1,0),(0,1),(255,255)])
@pytest.mark.parametrize('remaining',[0,32767,32768,65535])
def test_without_key_any_fire_enters_release_wait_before_timer(original_image,memory,fields,mouse,fire,remaining):
    cpu = poll(original_image,memory,fields,0,mouse,fire,remaining,1)
    assert cpu.pc == 0x11EE and cpu.a[7] == STACK


@pytest.mark.parametrize('remaining',[0,32767,32768,65535])
@pytest.mark.parametrize('page',[0,1,2,65535])
def test_negative_idle_word_selects_page_parity_otherwise_waits(original_image,memory,fields,remaining,page):
    cpu = poll(original_image,memory,fields,0,0,0,remaining,page)
    expected = 0x118A if remaining < 32768 else 0x34AA if page&1 else 0x116A
    assert cpu.pc == expected
    assert cpu.a[7] == STACK-(4 if expected==0x34AA else 0)


@pytest.mark.parametrize('key',[0,128,255])
def test_title_options_call_clears_pending_key_before_entering_ui(original_image,memory,fields,key):
    memory[fields['pending_key_scancode']] = key
    cpu = state(memory,0x11C6)
    run(original_image,memory,cpu,{0xE12C})
    assert memory[fields['pending_key_scancode']] == 0
    assert cpu.a[7] == STACK-4 and get(memory,STACK-4) == 0x11DE


@pytest.mark.parametrize('token',[0,26,27,28,128,255])
@pytest.mark.parametrize('upper',[0,0x12345600])
def test_escape_discards_only_the_command_return_and_reenters_title(original_image,memory,token,upper):
    cpu = state(memory,0x18C8); cpu.d[0] = upper|token
    before = cpu.d[1]
    run(original_image,memory,cpu,{0x1158,0x18D0})
    if token == 27:
        assert cpu.pc == 0x1158 and cpu.a[7] == STACK+4 and cpu.d[1] == RETURN
    else:
        assert cpu.pc == 0x18D0 and cpu.a[7] == STACK and cpu.d[1] == before


@pytest.mark.parametrize('debug',[0,1,128,255])
@pytest.mark.parametrize('counter',[0,1,32768,65535])
@pytest.mark.parametrize('fixed',[0,255])
@pytest.mark.parametrize('speed',[0,1,32768])
def test_matched_phrase_gate_keeps_word_wrap_and_clears_before_conditions(
        original_image,memory,fields,debug,counter,fixed,speed):
    m,f = memory,fields
    m[f['debug_features_enabled_flag']] = debug; m[f['fixed_sight_mode_flag']] = fixed
    put(m,f['negative_speed_control_accumulator'],speed,2); put(m,APP+0x1D6,counter,2)
    cpu = state(m,0x1E18)  # continuation after all original tail characters matched
    run(original_image,m,cpu,{0x1E3A,0x1E50})
    incremented = (counter+1)&65535
    accepted = bool(debug) or incremented==1
    assert get(m,APP+0x1D6,2) == (0 if accepted else incremented)
    assert cpu.pc == (0x1E3A if accepted and fixed and not speed else 0x1E50)


@pytest.mark.parametrize('debug',[0,1,128,255])
def test_post_message_debug_effect_fills_reserves_and_complements_entire_byte(original_image,memory,fields,debug):
    m,f = memory,fields; m[f['debug_features_enabled_flag']] = debug
    for i,n in enumerate(['icarus_power_reserve','icarus_shield_strength','weapon_energy_reserve']):
        put(m,f[n],i+1,2)
    cpu = state(m,0x1E3E)  # continuation after the real message helper
    run(original_image,m,cpu,{0x1E50})
    assert cpu.d[0] == 0xFFFFFFFF and m[f['debug_features_enabled_flag']] == debug^255
    assert all(get(m,f[n],2)==65535 for n in ['icarus_power_reserve','icarus_shield_strength','weapon_energy_reserve'])


@pytest.mark.parametrize('mismatch',[None,0,5,25])
def test_modal_w_phrase_uses_26_tail_keys_and_retained_dbf_drain(original_image,memory,fields,mismatch):
    m,f = memory,fields
    tail = b'ERE ON A MISSION FROM GOD1'
    assert len(tail)==26 and bytes(m[0x24B1:0x24B1+26])==tail
    tokens = tail if mismatch is None else tail[:mismatch]+b'Z'+b'X'*(26-mismatch)
    translation = bytes(m[0xDF0C:0xDF0C+126])
    keys = iter(translation.index(c) for c in tokens); seen = []
    m[f['mouse_primary_button_flag']] = m[f['primary_fire_flag']] = 0
    put(m,APP+0x1D6,0x1234,2)
    def provide(pc):
        if pc==0xD7AA:
            key=next(keys,None);assert key is not None,'unexpected extra original key request'
            seen.append(key);m[f['pending_key_scancode']]=key
    cpu=state(m,0x1E06)
    run(original_image,m,cpu,{0x1E18,0x1DEA},provide)
    assert cpu.pc==(0x1E18 if mismatch is None else 0x1DEA)
    assert len(seen)==(26 if mismatch is None else 27) and list(keys)==[]
    assert cpu.a[0]==0x24B1+(26 if mismatch is None else mismatch+1)
    assert cpu.d[7]&65535==65535 and get(m,APP+0x1D6,2)==0x1234
