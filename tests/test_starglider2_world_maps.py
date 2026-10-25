import pytest
from amiga_reversing.tools.starglider2_world_maps import decode_map


@pytest.mark.parametrize('stride', [10, 16])
def test_both_strides_and_terminator(stride):
    body = b'\x12\x03'+bytes(stride-2)
    result = decode_map(body+b'\0\0'+b'ignored', 0x1000, stride)
    assert result == dict(start=0x1000, end=0x1000+stride+2, count=1, stride=stride)


def test_empty_map_needs_only_tag():
    assert decode_map(b'\0\0', 0x1000, 16)['end'] == 0x1002


@pytest.mark.parametrize('data', [b'', b'\0', b'\0\x03', b'\0\x03'+bytes(8), b'\0\xff'+bytes(16)])
def test_refuse_truncated_or_outside_type_domain(data):
    with pytest.raises(ValueError):
        decode_map(data, 0x1000, 10)


def test_refuse_capacity_overrun():
    with pytest.raises(ValueError):
        decode_map((b'\0\x01'+bytes(8))*250+b'\0\0', 0x1000, 10)
