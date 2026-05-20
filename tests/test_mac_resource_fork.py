from __future__ import annotations

from src.scripts.inspect_mac_resource_fork import parse_resource_fork


def _u16(value: int) -> bytes:
    return value.to_bytes(2, "big")


def _u24(value: int) -> bytes:
    return value.to_bytes(3, "big")


def _u32(value: int) -> bytes:
    return value.to_bytes(4, "big")


def test_parse_resource_fork_reports_code_zero_metadata() -> None:
    payload = _u32(32) + _u32(64) + _u32(8) + _u32(32)
    resource_data = _u32(len(payload)) + payload
    data_offset = 0x100
    map_offset = 0x120
    resource_map = bytearray(64)
    resource_map[0:16] = _u32(data_offset) + _u32(map_offset) + _u32(len(resource_data)) + _u32(len(resource_map))
    resource_map[24:26] = _u16(28)
    resource_map[26:28] = _u16(52)
    resource_map[28:30] = _u16(0)
    resource_map[30:34] = b"CODE"
    resource_map[34:36] = _u16(0)
    resource_map[36:38] = _u16(10)
    resource_map[38:40] = _u16(0)
    resource_map[40:42] = _u16(0xFFFF)
    resource_map[42] = 0x20
    resource_map[43:46] = _u24(0)

    data = bytearray(map_offset + len(resource_map))
    data[0:16] = _u32(data_offset) + _u32(map_offset) + _u32(len(resource_data)) + _u32(len(resource_map))
    data[data_offset : data_offset + len(resource_data)] = resource_data
    data[map_offset : map_offset + len(resource_map)] = resource_map

    summary = parse_resource_fork(bytes(data), "synthetic")

    assert summary["types"] == [{"type": "CODE", "count": 1}]
    resource = summary["resources"][0]
    assert resource["type"] == "CODE"
    assert resource["id"] == 0
    assert resource["size"] == 16
    assert resource["code"] == {
        "kind": "jump_table_segment",
        "above_a5_size": 32,
        "below_a5_size": 64,
        "jump_table_length": 8,
        "jump_table_offset_from_a5": 32,
    }
