import pytest
from amiga_reversing.tools.starglider2_disk_audio import mfm_word, decode_nibble


def test_known_mfm_words_and_previous_bit():
    assert mfm_word(0) == 0x2AAA
    assert mfm_word(0, 0) == 0xAAAA
    assert mfm_word(255) == mfm_word(255, 0) == 0x5555
    assert mfm_word(128) == 0x4AAA


@pytest.mark.parametrize('previous', [0, 1])
def test_all_bytes_decode_without_clock_bits(previous):
    for value in range(256):
        word = mfm_word(value, previous)
        decoded = decode_nibble((word >> 8) & 127) << 4 | decode_nibble(word & 127)
        assert decoded == value


@pytest.mark.parametrize('value,previous', [(-1, 0), (256, 1), (0, 2)])
def test_refuse_invalid_encode_inputs(value, previous):
    with pytest.raises(ValueError):
        mfm_word(value, previous)
