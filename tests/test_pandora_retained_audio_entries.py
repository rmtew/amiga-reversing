"""Conditional execution of retained entries; ordinary activation is unproved."""
from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import APP, title_slots


ENTRIES = [(0x4D2CE, 0x0300), (0x4D2D4, 0x0200),
           (0x4D2DA, 0x0300), (0x4D2E0, 0x0300),
           (0x4D2E6, 0x0300), (0x4D2EC, 0x0300),
           (0x4D2F2, 0x0300), (0x4D2F8, 0x0211)]


def test_retained_entries_load_selector_and_enter_real_shared_call(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    flags = APP + title_slots['app_world_interaction_audio_flags']
    original = bytes(memory[BASE+0x4D2CE:BASE+0x4D2FE])
    for entry, selector in ENTRIES:
        for upper in [0, 0xA5F00000]:
            for flag in [0, 1, 0xFE, 0xFF]:
                for i in range(8):
                    cpu.d[i] = 0x12340000+i
                    if i < 7:
                        cpu.a[i] = 0x45670000+i
                cpu.d[0], cpu.a[6] = upper | 0xFFFF, APP
                before_d, before_a = list(cpu.d), list(cpu.a)[:7]
                write(flags, flag, 1)
                # Stop at the original callee before any audio MMIO access.
                assert run(entry, stop=0x4E3EC, budget=16) == 5
                assert cpu.d[0] == upper | selector
                assert list(cpu.d)[1:] == before_d[1:]
                assert list(cpu.a)[:7] == before_a
                assert read(flags, 1) == flag & ~1
                assert cpu.a[7] == 0x9000-52-4
                assert read(cpu.a[7]) == BASE+0x4D340
                saved = before_d[1:] + before_a[1:]
                assert [read(cpu.a[7]+4+4*i) for i in range(13)] == saved
    assert bytes(memory[BASE+0x4D2CE:BASE+0x4D2FE]) == original
