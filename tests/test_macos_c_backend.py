from __future__ import annotations

import hashlib
import struct

from amiga_reversing.disasm.c_backend import (
    inspect_macos_hfs_code_summary_with_c_backend,
)
from src.tests._build_helpers import require_built_tools


def _u16(value: int) -> bytes:
    return struct.pack(">H", value)


def _u24(value: int) -> bytes:
    return value.to_bytes(3, "big")


def _u32(value: int) -> bytes:
    return struct.pack(">I", value)


def _put(data: bytearray, offset: int, payload: bytes) -> None:
    data[offset : offset + len(payload)] = payload


def _put_name_key(node: bytearray, offset: int, parent_id: int, name: str) -> None:
    encoded = name.encode("macroman")
    node[offset] = 6 + len(encoded)
    _put(node, offset + 2, _u32(parent_id))
    node[offset + 6] = len(encoded)
    _put(node, offset + 7, encoded)


def _put_extent(data: bytearray, offset: int, start: int, count: int) -> None:
    _put(data, offset, _u16(start) + _u16(count))


def _make_code_resource_fork() -> bytes:
    data = bytearray(512)
    data_offset = 0x100
    map_offset = 0x140
    map_length = 0x60
    code0_payload = data_offset + 4
    code1_record = data_offset + 20
    code1_payload = code1_record + 4
    type_list = map_offset + 28
    ref_list = type_list + 10
    for offset, value in (
        (0, data_offset),
        (4, map_offset),
        (8, 30),
        (12, map_length),
        (map_offset, data_offset),
        (map_offset + 4, map_offset),
        (map_offset + 8, 30),
        (map_offset + 12, map_length),
    ):
        _put(data, offset, _u32(value))
    _put(data, data_offset, _u32(16))
    _put(data, code0_payload, _u32(32) + _u32(64) + _u32(8) + _u32(32))
    _put(data, code1_record, _u32(6))
    _put(data, code1_payload, _u16(4) + _u16(2) + b"\x4e\x75")
    _put(data, map_offset + 24, _u16(28))
    _put(data, map_offset + 26, _u16(58))
    _put(data, type_list, _u16(0) + b"CODE" + _u16(1) + _u16(10))
    _put(data, ref_list, _u16(0) + _u16(0xFFFF) + b"\x20" + _u24(0) + b"\x00\x00\x00\x00")
    _put(data, ref_list + 12, _u16(1) + _u16(0xFFFF) + b"\x00" + _u24(20) + b"\x00\x00\x00\x00")
    return bytes(data)


def _make_hfs_image() -> bytes:
    image = bytearray(4096)
    mdb = 1024
    catalog_offset = 2048
    leaf_offset = catalog_offset + 512
    directory_record = 14
    directory_data = 26
    file_record = 80
    file_data = 90
    image[mdb : mdb + 2] = b"BD"
    _put(image, mdb + 18, _u16(16))
    _put(image, mdb + 20, _u32(512))
    _put(image, mdb + 28, _u16(4))
    image[mdb + 36] = 6
    _put(image, mdb + 37, b"MPW-GM")
    _put(image, mdb + 146, _u32(1024))
    _put_extent(image, mdb + 150, 0, 2)
    _put(image, catalog_offset + 10, _u16(1))
    _put(image, catalog_offset + 512 - 2, _u16(14))
    _put(image, catalog_offset + 14 + 18, _u16(512))
    image[leaf_offset + 8] = 0xFF
    _put(image, leaf_offset + 10, _u16(2))
    _put_name_key(image, leaf_offset + directory_record, 2, "Tools")
    _put(image, leaf_offset + directory_data, _u16(0x0100))
    _put(image, leaf_offset + directory_data + 4, _u16(1))
    _put(image, leaf_offset + directory_data + 6, _u32(42))
    _put_name_key(image, leaf_offset + file_record, 42, "Asm")
    _put(image, leaf_offset + file_data, _u16(0x0200))
    _put(image, leaf_offset + file_data + 4, b"MPST")
    _put(image, leaf_offset + file_data + 8, b"MPS ")
    _put(image, leaf_offset + file_data + 20, _u32(2310))
    _put(image, leaf_offset + file_data + 26, _u32(128))
    _put(image, leaf_offset + file_data + 36, _u32(512))
    _put_extent(image, leaf_offset + file_data + 74, 2, 1)
    _put_extent(image, leaf_offset + file_data + 86, 3, 1)
    _put(image, leaf_offset + 512 - 2, _u16(directory_record))
    _put(image, leaf_offset + 512 - 4, _u16(file_record))
    _put(image, 2048 + 2 * 512, b"DATA-FORK")
    _put(image, 2048 + 3 * 512, _make_code_resource_fork())
    return bytes(image)


def test_python_wrapper_uses_c_macos_hfs_code_summary() -> None:
    require_built_tools()
    summary = inspect_macos_hfs_code_summary_with_c_backend(_make_hfs_image(), "MPW-GM/Tools/Asm")
    assert summary["platform"] == "macos"
    assert summary["container_kind"] == "hfs_resource_code_file"
    assert summary["volume"]["name"] == "MPW-GM"
    assert summary["file"]["path"] == "Tools/Asm"
    assert summary["file"]["type"] == "MPST"
    assert summary["file"]["creator"] == "MPS "
    assert summary["file"]["forks"]["data"]["size"] == 128
    assert summary["file"]["forks"]["resource"]["size"] == 512
    assert summary["resource_fork"]["type_count"] == 1
    assert summary["resource_fork"]["resource_count"] == 2
    assert [item["id"] for item in summary["resource_fork"]["code_resources"]] == [0, 1]
    assert summary["selected_code"]["available"] is True
    assert summary["selected_code"]["payload_size"] == 6
    assert summary["selected_code"]["code_bytes_size"] == 2
    assert summary["selected_code"]["code_bytes_sha256"] == hashlib.sha256(b"\x4e\x75").hexdigest()
