"""Finite target recipe invariants; no proprietary fixtures required."""
import pytest
from amiga_reversing.tools.starglider2_protection import SIZE, KEY, decode, encode, extract, subtract_stage


def test_known_words_and_long_carry():
    # Encoded zero -> subtraction with borrow; rotations cross each WORD edge.
    encoded = bytes(SIZE)
    first = (-KEY & 0xFFFFFFFF)
    assert subtract_stage(encoded)[:4] == first.to_bytes(4, 'big')
    a, b = first >> 16, first & 0xFFFF
    expected = (((a << 2 | a >> 14) & 0xFFFF).to_bytes(2, 'big')
                + ((b >> 3 | b << 13) & 0xFFFF).to_bytes(2, 'big'))
    assert decode(encoded)[:4] == expected
    assert subtract_stage(encoded)[-4:] == (-KEY-(SIZE//4-1) & 0xFFFFFFFF).to_bytes(4, 'big')


@pytest.mark.parametrize('payload', [bytes(SIZE), bytes([255])*SIZE,
                                   bytes(i % 256 for i in range(SIZE))])
def test_bidirectional_inverse(payload):
    assert encode(decode(payload)) == payload
    assert decode(encode(payload)) == payload


@pytest.mark.parametrize('operation', [decode, encode, subtract_stage])
@pytest.mark.parametrize('size', [0, SIZE-2, SIZE+2])
def test_refuse_partial_or_declared_but_unprocessed_tail(operation, size):
    with pytest.raises(ValueError):
        operation(bytes(size))


def test_refuse_unreviewed_parent():
    with pytest.raises(ValueError):
        extract(bytes(412736))


def test_known_zero_plaintext_encoding_is_incrementing_key():
    encoded = encode(bytes(SIZE))
    assert encoded[:4] == KEY.to_bytes(4, 'big')
    assert encoded[-4:] == (KEY+SIZE//4-1).to_bytes(4, 'big')
