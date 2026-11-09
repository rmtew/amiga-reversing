"""Original ring arithmetic and CPU continuations with supplied readable RAM.

Device addresses are RAM. No disk, PCM, interrupt delivery, concurrent writer,
normal-startup, arbitrary selector or writable-buffer lifetime claim follows.
"""
import pytest
from tests.test_starglider2_text_editor import original_image, state, run, put, get, INPUT, STACK
from tests.test_starglider2_object_sound_handlers import memory, small_memory

TABLE, READ, PRODUCER, BLOCKS, ADVANCED = 0x104C6, 0x10590, 0x10592, 0x10594, 0x10598
SHARED, TRANSFER, BLOCK_BYTES, SAMPLE_BYTES, SAMPLE_OPERAND = 0x41848, 0x121C0, 0x121B8, 0x11EC6, 0x11684
CUSTOM = 0xDFF000


def advance(value):
    result = (value + 4) & 65535
    return 0 if result == 28 else result


def initialize(image, memory):
    before = bytes(memory[TABLE - 4:TABLE]), bytes(memory[TABLE + 28:TABLE + 32])
    cpu = state(memory, 0x1027A)
    run(image, memory, cpu, {0x10290})
    assert [get(memory, TABLE + 4*i) for i in range(7)] == [SHARED + 5632*i for i in range(7)]
    assert (bytes(memory[TABLE - 4:TABLE]), bytes(memory[TABLE + 28:TABLE + 32])) == before
    assert cpu.a[0] == SHARED + 7*5632 and cpu.a[1] == TABLE + 28


def test_original_initializer_writes_exactly_seven_strided_pointers(original_image, memory):
    initialize(original_image, memory)


@pytest.mark.parametrize('alternate', [False, True])
@pytest.mark.parametrize('remaining', [0, 1, 2, 32768, 32769, 65535])
@pytest.mark.parametrize('offset', [0, 4, 20, 24, 28, 65532])
def test_consumer_exact_wrap_and_distinct_stop_conditions(original_image, memory, alternate, remaining, offset):
    put(memory, READ, offset, 2); put(memory, BLOCKS, remaining, 2)
    put(memory, CUSTOM + 0x1E, 0x200, 2)
    cpu = state(memory, 0x11ECA if alternate else 0x104E2)
    following, stopped = (0x11EEA, 0x11F0A) if alternate else (0x10516, 0x10564)
    run(original_image, memory, cpu, {following, stopped})
    left = (remaining - 1) & 65535
    continues = left != 0 and (not alternate or left < 32768)
    assert get(memory, BLOCKS, 2) == left
    assert cpu.pc == (following if continues else stopped)
    assert get(memory, READ, 2) == (advance(offset) if continues else offset)
    # Exact equality is not a clamp: supplied 28 advances to out-of-table 32.
    if continues and offset == 28: assert get(memory, READ, 2) == 32


@pytest.mark.parametrize('entry,stop', [(0x1034C, 0x10376), (0x114D8, 0x11502)])
@pytest.mark.parametrize('offset', [0, 4, 20, 24, 28, 65532])
def test_prefill_pointer_selection_preserves_unchecked_word_alias(original_image, memory, entry, stop, offset):
    initialize(original_image, memory); put(memory, PRODUCER, offset, 2)
    expected = advance(offset); signed = expected if expected < 32768 else expected - 65536
    pointer = get(memory, TABLE + signed)
    cpu = state(memory, entry); run(original_image, memory, cpu, {stop})
    assert get(memory, PRODUCER, 2) == expected and get(memory, TRANSFER) == pointer


@pytest.mark.parametrize('entry,stop', [(0x1041E, 0x1044E), (0x11546, 0x11576)])
@pytest.mark.parametrize('offset', [0, 4, 8, 12, 16, 20, 24, 28, 65532])
def test_producer_wait_tests_two_slots_ahead_after_its_own_advance(original_image, memory, entry, stop, offset):
    put(memory, PRODUCER, offset, 2)
    cpu = state(memory, entry); run(original_image, memory, cpu, {stop})
    value = advance(offset)
    assert get(memory, PRODUCER, 2) == value
    assert cpu.d[0] & 65535 == advance(advance(value))


@pytest.mark.parametrize('pending,remaining', [(False, 2), (True, 1), (True, 2)])
def test_amiga_interrupt_restores_saved_registers_before_rte(original_image, memory, pending, remaining):
    initialize(original_image, memory)
    put(memory, READ, 24, 2); put(memory, BLOCKS, remaining, 2); memory[ADVANCED] = 0x55
    put(memory, CUSTOM + 0x1E, 0x200 if pending else 0, 2)
    for off in [0xA4, 0xA6, 0xC4, 0xC6, 0xC8, 0x96, 0x9A]: put(memory, CUSTOM + off, 0xA55A, 2)
    cpu = state(memory, 0x104E2); before_d, before_a = list(cpu.d), list(cpu.a); delays = 0
    def observe(pc):
        nonlocal delays
        if pc == 0x1051C: delays += 1
    run(original_image, memory, cpu, {0x10556}, observe, limit=66000)
    assert list(cpu.d) == before_d and list(cpu.a) == before_a and cpu.a[7] == STACK
    assert get(memory, CUSTOM + 0x9C, 2) == 0x380 and get(memory, CUSTOM + 0x180, 2) == 0
    if not pending:
        assert get(memory, BLOCKS, 2) == remaining and get(memory, READ, 2) == 24
        assert memory[ADVANCED] == 0x55 and delays == 0
        assert get(memory, CUSTOM + 0xA4, 2) == 0xA55A
    elif remaining == 1:
        assert get(memory, READ, 2) == 24 and memory[ADVANCED] == 0x55 and delays == 0
        assert all(get(memory, CUSTOM + off, 2) == 1 for off in [0xA4, 0xA6, 0xC4, 0xC6])
        assert get(memory, CUSTOM + 0x9A, 2) == 0x380 and get(memory, CUSTOM + 0x96, 2) == 5
        assert get(memory, CUSTOM + 0xC8, 2) == 0
    else:
        assert get(memory, READ, 2) == 0 and memory[ADVANCED] == 255 and delays == 65536
        assert get(memory, CUSTOM + 0xA0) == get(memory, CUSTOM + 0xC0) == SHARED
        assert get(memory, CUSTOM + 0xA4, 2) == get(memory, CUSTOM + 0xC4, 2) == 2816
        assert get(memory, CUSTOM + 0xA6, 2) == get(memory, CUSTOM + 0xC6, 2) == 0xA55A
        assert get(memory, CUSTOM + 0x96, 2) == get(memory, CUSTOM + 0x9A, 2) == 0xA55A


@pytest.mark.parametrize('offset', range(0, 28, 4))
def test_alternate_handoff_patches_pointer_and_reloads_byte_count(original_image, memory, offset):
    initialize(original_image, memory); put(memory, READ, offset, 2); put(memory, BLOCK_BYTES, 5632)
    cpu = state(memory, 0x11EEA); run(original_image, memory, cpu, {0x116BA})
    assert get(memory, SAMPLE_OPERAND) == SHARED + offset//4*5632
    assert get(memory, SAMPLE_BYTES) == 5632


@pytest.mark.parametrize('alternate', [False, True])
@pytest.mark.parametrize('equal', [False, True])
@pytest.mark.parametrize('lookahead', [0, 4, 24, 65535])
def test_wait_branch_reloads_consumer_and_retries_only_on_exact_equality(original_image, memory, alternate, equal, lookahead):
    start, branch, following = (0x11576, 0x1157C, 0x1157E) if alternate else (0x1044E, 0x10454, 0x10456)
    put(memory, READ, lookahead if equal else lookahead ^ 4, 2)
    cpu = state(memory, start); cpu.d[0] = 0xABCD0000 | lookahead
    run(original_image, memory, cpu, {branch})
    run(original_image, memory, cpu, {start, following})
    assert cpu.pc == (start if equal else following)
    assert cpu.d[0] == 0xABCD0000 | lookahead
