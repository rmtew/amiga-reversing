import pytest
from amiga_reversing.tools.starglider2_flight_probe import contact_list_records


def capture(pointers, **changes):
    pool = b'\x00\x16' + bytes(66) + b'\x00\x92' + bytes(66)
    arguments = dict(cursor=0x1010, storage_start=0x1000, storage_size=32,
                     pool_base=0x2000, stride=68)
    arguments.update(changes)
    return contact_list_records(b''.join(p.to_bytes(4, 'big') for p in pointers), pool, **arguments)


def test_original_tags_order_and_duplicate_membership_are_retained():
    result = capture([0x2044, 0x2000, 0x2044])
    assert [r['stored_type'] for r in result] == [146, 22, 146]
    assert [r['pool_record'] for r in result] == [1, 0, 1]
    assert all(len(bytes.fromhex(r['bytes_hex'])) == 68 for r in result)


def test_empty_end_cursor_is_valid_but_does_not_imply_a_reader():
    assert capture([], cursor=0x1020) == []


@pytest.mark.parametrize('changes', [dict(cursor=0x0ffc), dict(cursor=0x101c)])
def test_list_span_outside_backing_refuses(changes):
    with pytest.raises(ValueError, match='backing'):
        capture([0x2000, 0x2044], **changes)


@pytest.mark.parametrize('pointer', [0, 0xffffffff, 0x2002, 0x2088])
def test_unmapped_unaligned_or_one_past_pool_record_refuses(pointer):
    with pytest.raises(ValueError, match='pool record'):
        capture([pointer])
