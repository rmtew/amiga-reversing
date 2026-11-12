"""Original Emma grant/launcher gate with supplied transport, RAM and queue.

No full mission, normal-game reachability, actual projectile, hardware delivery
or general queue-capacity proof follows from these bounded phases.
"""
import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, STACK
from tests.test_starglider2_tractor_state import fields, POOL
from tests.test_starglider2_message_lines import QUEUE, COUNT, TIMER

EVENTS = 0x37B68


@pytest.mark.parametrize('kind', [1, 8])
@pytest.mark.parametrize('enabled', [0, 1, 127, 128, 255])
@pytest.mark.parametrize('phase', [0, 14, 15, 255])
@pytest.mark.parametrize('available', [0, 1, 128, 255])
def test_radio_wrap_grants_launcher_once_and_queues_original_message_pointers(original_image, memory, fields, kind, enabled, phase, available):
    m = memory; slot = fields['model_type_population_counts']+84
    put(m, POOL, kind, 2); m[POOL+31] = phase; m[POOL+34] = enabled; m[slot] = available
    put(m, COUNT, 1, 2); put(m, TIMER, 33, 2); put(m, QUEUE, 0x123456)
    m[QUEUE+4:QUEUE+40] = b'\xCC'*36
    cpu = state(m, 0x35320); cpu.a[0] = POOL
    run(original_image, m, cpu, {0x3539C})
    active = kind == 8 and bool(enabled&128)
    new_phase = (phase+1)&15 if active else phase
    broadcast = active and new_phase == 0
    indexes = ([31, 32]+([51, 76] if not available else [])+[35]) if broadcast else []
    assert m[POOL+31] == new_phase and m[POOL+34] == enabled
    assert m[slot] == (1 if broadcast and not available else available)
    assert get(m, COUNT, 2) == 1+len(indexes) and get(m, TIMER, 2) == 33
    assert get(m, QUEUE) == 0x123456
    assert [get(m, QUEUE+4+4*i) for i in range(len(indexes))] == [get(m, EVENTS+4*i) for i in indexes]
    assert bytes(m[QUEUE+4+4*len(indexes):QUEUE+40]) == b'\xCC'*(36-4*len(indexes))
    assert cpu.a[0] == POOL and cpu.a[7] == STACK


@pytest.mark.parametrize('available', [0, 1, 127, 128, 255])
def test_launcher_permission_is_nonzero_and_not_consumed_before_energy_gate(original_image, memory, fields, available):
    m = memory; slot = fields['model_type_population_counts']+84
    m[slot] = available; cpu = state(m, 0x724E); cpu.a[1] = fields['model_type_population_counts']
    run(original_image, m, cpu, {0x7256, 0x73DA})
    assert cpu.pc == (0x7256 if available else 0x73DA)
    assert m[slot] == available and cpu.a[7] == STACK
