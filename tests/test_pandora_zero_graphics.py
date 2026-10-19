"""Shared original zero inputs; MMIO shadows do not simulate graphics DMA."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
BANK = BASE + 0x4D5DE


def test_original_frame_headers_bound_shared_zero_pixels_and_masks(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    pixel_spans, mask_spans = [], []
    for offset, height in [(0x48588, 16), (0x4C5A4, 32)]:
        frame = BASE + offset
        assert read(frame) == read(frame + 4) == BANK
        stride = read(frame + 8, 2)
        assert (stride, read(frame + 10, 2), read(frame + 12, 2)) == (2, height, 32)
        assert read(frame + 14) == 0
        pixel_spans.append(8 * stride * height)
        mask_spans.append(2 * stride * height)
    assert max(pixel_spans) == 512 and max(mask_spans) == 128
    assert memory[BANK:BANK + max(pixel_spans)] == bytes(512)
    # The next byte belongs to the separately decoded audio entry, not the bank.
    assert BANK + max(pixel_spans) == BASE + 0x4D7DE
    assert memory[BANK + 512:BANK + 514] != bytes(2)


def test_exit_palette_prefix_selects_zero_bank_and_copies_exactly_sixteen_colors(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    app, colors = 0x39FC, 0xDFF180
    cpu.a[6] = app
    run(0x72A, stop=0x734)
    assert read(app + 0x27C) == BANK
    memory[colors - 4:colors + 36] = bytes([0xA5]) * 40
    bank_before = bytes(memory[BANK:BANK + 512])
    run(0x752)
    assert memory[colors:colors + 32] == bytes(32)
    assert memory[colors - 4:colors] == memory[colors + 32:colors + 36] == bytes([0xA5]) * 4
    assert memory[BANK:BANK + 512] == bank_before
    assert cpu.a[0] == BANK + 32 and cpu.a[1] == colors + 32
