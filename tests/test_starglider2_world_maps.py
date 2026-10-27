import pytest
from amiga_reversing.tools.starglider2_world_maps import (
    decode_map, depot_service_domain, type94_service_byte,
)


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


@pytest.mark.parametrize('initial,world,expected', [
    (0, 16, 0), (0, 31, 0), (1, 19, 1), (4, 23, 4),
    (165, 19, 165), (1, 24, 2), (255, 24, 2), (1, 25, 5),
    (1, 30, 10), (1, 31, 11), (1, 16, 252), (1, 18, 254),
])
def test_type94_constructor_branches_and_byte_wrap(initial, world, expected):
    assert type94_service_byte(initial, world) == expected


@pytest.mark.parametrize('initial,world', [
    (-1, 19), (256, 19), (True, 19), (1.5, 19),
    (1, 15), (1, 32), (1, True), (1, 24.5),
])
def test_type94_refuses_wrong_input_domains(initial, world):
    with pytest.raises(ValueError):
        type94_service_byte(initial, world)


def test_aliased_placement_has_world_dependent_service_identity():
    payload = b'\x01\x5e' + bytes(14) + b'\0\0'
    mapping = dict(start=0x1000, count=1, stride=16, indices=[24, 25])
    result = depot_service_domain(payload, [mapping])
    assert result['service_ids'] == [2, 5]
    assert [r['source_offset'] for r in result['records']] == [0, 0]
    assert [r['world_index'] for r in result['records']] == [24, 25]
    # A neighboring different type is not given the depot interpretation.
    assert depot_service_domain(b'\x01\x5d' + bytes(14), [mapping])['records'] == []
