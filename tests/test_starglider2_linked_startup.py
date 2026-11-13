"""Bounded original-instruction witnesses; private game media is opt-in."""
import os
from pathlib import Path

import pytest

from amiga_reversing.disasm.game_catalog import load_family, materialize, unique_counterpart, verify_correspondence
from amiga_reversing.disasm.mapped_execution import MappedExecution

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not os.getenv('SGII_LINKED_FIXTURES'), reason='bind private SGII sources and set SGII_LINKED_FIXTURES=1')


def payload(target):
    family = load_family(ROOT, 'starglider2')
    return materialize(ROOT, 'starglider2', family['targets'][target]['artifact']).read_bytes()


def test_st_handoff_initializes_only_the_observed_workspace_before_platform_call():
    cpu = MappedExecution(0x80000, register_seed=0xdeadbeef)
    cpu.seed(0x1000, payload('atari_st_starglider2_main'))
    for start, size in [(0xe144, 2), (0x27be, 4), (0x61668, 0x6598)]:
        cpu.allow_write(start, size)
    result = cpu.run(0x1000, 0x10d6, 27000)
    assert result['steps'] == 26025
    assert cpu.read(0x27be, 4) == (0x61668).to_bytes(4, 'big')
    assert cpu.read(0x61668, 0x6598) == bytes(0x6598)
    assert cpu.cpu.a[0] == 0x67c00
    assert cpu.cpu.a[7] == 0x3386
    # Stop before the first platform helper, not after a simulated machine boot.
    assert cpu.cpu.pc == 0x10d6


@pytest.mark.parametrize('first,second', [(0, 0), (0xffffffff, 0xffffffff), (0x12345678, 0x9abcdef0), (0x80000000, 7)])
def test_unique_shared_random_step_has_the_same_bounded_state_contract(first, second):
    link = verify_correspondence(ROOT, 'starglider2', 'shared_prng_step')
    values = []
    for side in ('left', 'right'):
        span = link[side]
        data = payload(span['target'])
        peer = link['right' if side == 'left' else 'left']
        assert unique_counterpart(data, span['offset'], span['size'], payload(peer['target']))['offset'] == peer['offset']
        cpu = MappedExecution(0x80000)
        cpu.seed(0x1000, data)
        cpu.cpu.a[6] = 0x70000
        cpu.cpu.a[7] = 0x76000
        cpu.cpu.d[1] = 0xfeedface
        cpu.seed(0x70060, first.to_bytes(4, 'big') + second.to_bytes(4, 'big'))
        cpu.seed(0x76000, (0x7f000).to_bytes(4, 'big'))
        cpu.allow_write(0x70060, 8)
        cpu.allow_write(0x75ffc, 4)
        cpu.run(0x1000 + span['offset'], 0x7f000, 16)
        assert cpu.cpu.d[1] == 0xfeedface
        assert cpu.cpu.a[7] == 0x76004
        rotated = ((first << 3) | (first >> 29)) & 0xffffffff
        expected = (rotated & 0xffff0000) | (((rotated - 7) ^ second) & 0xffff)
        assert cpu.read(0x70060, 8) == second.to_bytes(4, 'big') + expected.to_bytes(4, 'big')
        assert cpu.cpu.d[0] == expected
        values.append(cpu.read(0x70060, 8))
    assert values[0] == values[1]


def test_game_over_messages_have_unique_qualified_counterparts():
    link = verify_correspondence(ROOT, 'starglider2', 'game_over_message_pair')
    left, right = link['left'], link['right']
    a, b = payload(left['target']), payload(right['target'])
    strings = a[left['offset']:left['offset'] + left['size']].split(b'\0')
    assert [part.strip() for part in strings if part] == [b'POWER DRAINAGE TOO GREAT!', b'ICARUS DESTROYED!']
    assert unique_counterpart(a, left['offset'], left['size'], b)['offset'] == right['offset']
    assert unique_counterpart(b, right['offset'], right['size'], a)['offset'] == left['offset']


def test_protection_view_uses_original_cpu_transform_and_preserves_helper_context():
    import json
    from amiga_reversing.disasm.mapped_recipe import recover_mapped
    original=payload('atari_st_starglider2_main')
    plan=json.loads((ROOT/'targets/atari_st_starglider2_stx/protection_plan.json').read_text())
    report,outputs=recover_mapped(original,plan,register_seed=0xdeadbeef)
    view=outputs['novella_protection_view.bin']
    assert [r['steps'] for r in report['runs']]==[6901,6,13788]
    assert recover_mapped(original,plan)[1]==outputs
    expected=bytearray()
    for i in range(0,0x23e8,4):
        value=(int.from_bytes(original[0x121e0+i:0x121e4+i],'big')-0x32597635-i//4)&0xffffffff
        high,low=value>>16,value&0xffff
        expected.extend(((((high<<2)|(high>>14))&0xffff)<<16 | ((low>>3)|(low<<13))&0xffff).to_bytes(4,'big'))
    assert view[:0x23e8]==expected
    assert view[0x23e8:]==original[0x145c8:0x14808]
    assert view[0x2150:0x2152]==b'\x61\0'  # Original integrity comparison at runtime $15330.
    assert view==payload('atari_st_starglider2_protection_view')


def test_novella_record_families_and_qualified_english_text_match():
    view=payload('atari_st_starglider2_protection_view')
    for start,count,reachable in [(0,163,147),(0xa30,129,128),(0x1240,133,130)]:
        assert reachable<count
        for i in range(count):
            record=view[start+16*i:start+16*(i+1)]
            assert len(record)==16 and all(record[j]>0 for j in range(3))
            answer=record[3:]
            assert b'\0' in answer
            assert all(32<=v<=126 for v in answer[:answer.index(0)])
    link=verify_correspondence(ROOT,'starglider2','novella_english_instructions')
    left,right=link['left'],link['right']
    a,b=payload(left['target']),payload(right['target'])
    assert unique_counterpart(a,left['offset'],left['size'],b)['offset']==right['offset']
    assert unique_counterpart(b,right['offset'],right['size'],a)['offset']==left['offset']


@pytest.mark.parametrize('base,bound,compare,accepted_stop,retry',[
    (0x131e0,147,0x15334,0x1534a,0x15330),
    (0x13c10,128,0x153fa,0x1540e,0x153f6),
    (0x14420,130,0x154c0,0x154d4,0x154bc),
])
@pytest.mark.parametrize('case',['first','last','at_bound','unsigned_max'])
def test_original_language_selectors_enforce_record_bounds_and_stride(base,bound,compare,accepted_stop,retry,case):
    selector={'first':0,'last':bound-1,'at_bound':bound,'unsigned_max':0xffff}[case]
    cpu=MappedExecution(0x80000,register_seed=0xdeadbeef)
    cpu.seed(0x131e0,payload('atari_st_starglider2_protection_view'))
    cpu.cpu.a[6]=0x70000
    cpu.cpu.d[0]=0xdead0000|selector
    cpu.allow_write(0x70068,4)
    accepted=selector<bound
    cpu.run(compare,accepted_stop if accepted else retry,8)
    if accepted:
        expected=base+selector*16
        assert cpu.cpu.a[0]==expected
        assert cpu.read(0x70068,4)==expected.to_bytes(4,'big')
    else:
        assert not any(cpu.known[0x70068:0x7006c])
