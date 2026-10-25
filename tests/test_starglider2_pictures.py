import pytest
from amiga_reversing.tools.starglider2_pictures import decode_plane, plane_byte_offset, audit


def test_repeat_literal_terminator_and_underfill():
    result, end, counts = decode_plane(bytes([3, 0xAA, 0xFE, 0x10, 0x20, 0, 99]))
    assert result == bytes([0xAA]*3+[0x10, 0x20])
    assert end == 6
    assert counts == dict(repeats=1, literals=1)


def test_column_major_addresses():
    assert [plane_byte_offset(i) for i in [0, 1, 199, 200, 7998, 7999]] == [0, 40, 7960, 1, 7959, 7999]
    assert len({plane_byte_offset(i) for i in range(8000)}) == 8000


@pytest.mark.parametrize('data', [b'', b'\x01', b'\x01\xff', b'\xfe\xff', b'\x80'])
def test_refuse_truncated_or_unbounded_streams(data):
    with pytest.raises(ValueError):
        decode_plane(data)


def test_refuse_overflow():
    with pytest.raises(ValueError):
        decode_plane(bytes([127, 42])*64+b'\0')


def test_no_unwritten_fill():
    assert decode_plane(b'\0')[0] == b''


def test_parent_binding():
    with pytest.raises(ValueError):
        audit(bytes(412736))
