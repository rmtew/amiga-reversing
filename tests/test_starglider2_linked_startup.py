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
