from __future__ import annotations

import struct
import unittest

from src.tests._platform_disk_test_utils import PlatformDiskTestCaseMixin

BLOCK_SIZE = 512
TOTAL_BLOCKS = 1760
ROOT_BLOCK = 880


def _u32(value: int) -> bytes:
    return struct.pack(">I", value & 0xFFFFFFFF)


def _bcpl_text(text: str, max_len: int) -> bytes:
    raw = text.encode("latin-1")
    if len(raw) > max_len:
        raise ValueError(text)
    return bytes([len(raw)]) + raw.ljust(max_len, b"\x00")


def _put_u32(block: bytearray, offset: int, value: int) -> None:
    block[offset : offset + 4] = _u32(value)


def _make_boot_block(root_block: int, flags: int) -> bytes:
    boot = bytearray(BLOCK_SIZE * 2)
    boot[0:3] = b"DOS"
    boot[3] = flags
    _put_u32(boot, 8, root_block)
    return bytes(boot)


def _make_root_block(volume_name: str, entries: list[int]) -> bytes:
    block = bytearray(BLOCK_SIZE)
    _put_u32(block, 0, 2)
    _put_u32(block, 12, 72)
    _put_u32(block, 20, 0)
    for index, entry_block in enumerate(entries):
        _put_u32(block, 24 + index * 4, entry_block)
    block[432:463] = _bcpl_text(volume_name, 30)
    _put_u32(block, 508, 1)
    return bytes(block)


def _make_file_header(block_index: int, name: str, byte_size: int, *, sec_type: int = 0xFFFFFFFD, hash_chain: int = 0) -> bytearray:
    block = bytearray(BLOCK_SIZE)
    _put_u32(block, 0, 2)
    _put_u32(block, 4, block_index)
    _put_u32(block, 20, 0)
    _put_u32(block, 324, byte_size)
    block[432:463] = _bcpl_text(name, 30)
    _put_u32(block, 496, hash_chain)
    _put_u32(block, 508, sec_type)
    return block


def _set_ffs_data_block_pointers(block: bytearray, data_block_indices: list[int]) -> None:
    _put_u32(block, 8, len(data_block_indices))
    start = 72 - len(data_block_indices)
    for offset, data_block_index in enumerate(reversed(data_block_indices)):
        _put_u32(block, 24 + (start + offset) * 4, data_block_index)


def _make_file_extension_block(block_index: int, data_block_indices: list[int], *, next_extension: int = 0) -> bytes:
    block = bytearray(BLOCK_SIZE)
    _put_u32(block, 0, 16)
    _put_u32(block, 4, block_index)
    _set_ffs_data_block_pointers(block, data_block_indices)
    _put_u32(block, 504, next_extension)
    _put_u32(block, 508, 0xFFFFFFFD)
    return bytes(block)


def _make_userdir_block(block_index: int, name: str, entries: list[int]) -> bytearray:
    block = _make_file_header(block_index, name, 0, sec_type=2)
    for index, entry_block in enumerate(entries):
        _put_u32(block, 24 + index * 4, entry_block)
    return block


def _make_ofs_data_block(header_block: int, data: bytes, next_block: int = 0) -> bytes:
    block = bytearray(BLOCK_SIZE)
    _put_u32(block, 0, 8)
    _put_u32(block, 4, header_block)
    _put_u32(block, 12, len(data))
    _put_u32(block, 16, next_block)
    _put_u32(block, 20, 0)
    block[24 : 24 + len(data)] = data
    return bytes(block)


def _make_ffs_adf() -> bytes:
    blocks = [bytearray(BLOCK_SIZE) for _ in range(TOTAL_BLOCKS)]
    blocks[0][:] = _make_boot_block(ROOT_BLOCK, 1)[:BLOCK_SIZE]
    blocks[1][:] = _make_boot_block(ROOT_BLOCK, 1)[BLOCK_SIZE:]
    blocks[ROOT_BLOCK][:] = _make_root_block("Workbench", [900, 901])

    file_header = _make_file_header(900, "HELLO", 6)
    _put_u32(file_header, 8, 1)
    _put_u32(file_header, 24 + 71 * 4, 910)
    blocks[900][:] = file_header

    dir_block = _make_userdir_block(901, "C", [902])
    blocks[901][:] = dir_block

    nested_header = _make_file_header(902, "RUNME", 4)
    _put_u32(nested_header, 8, 1)
    _put_u32(nested_header, 24 + 71 * 4, 911)
    blocks[902][:] = nested_header

    blocks[910][:6] = b"ABCDEF"
    blocks[911][:4] = b"\x60\x1A\x00\x00"
    return b"".join(bytes(block) for block in blocks)


def _make_ofs_adf() -> bytes:
    blocks = [bytearray(BLOCK_SIZE) for _ in range(TOTAL_BLOCKS)]
    blocks[0][:] = _make_boot_block(ROOT_BLOCK, 0)[:BLOCK_SIZE]
    blocks[1][:] = _make_boot_block(ROOT_BLOCK, 0)[BLOCK_SIZE:]
    blocks[ROOT_BLOCK][:] = _make_root_block("Games", [900])

    file_header = _make_file_header(900, "README", 10)
    _put_u32(file_header, 16, 910)
    blocks[900][:] = file_header

    blocks[910][:] = _make_ofs_data_block(900, b"HELLO", 911)
    blocks[911][:] = _make_ofs_data_block(900, b"WORLD", 0)
    return b"".join(bytes(block) for block in blocks)


def _make_ffs_adf_with_extension() -> bytes:
    data_block_indices = list(range(910, 983))
    blocks = [bytearray(BLOCK_SIZE) for _ in range(TOTAL_BLOCKS)]
    blocks[0][:] = _make_boot_block(ROOT_BLOCK, 1)[:BLOCK_SIZE]
    blocks[1][:] = _make_boot_block(ROOT_BLOCK, 1)[BLOCK_SIZE:]
    blocks[ROOT_BLOCK][:] = _make_root_block("Workbench", [900])

    file_header = _make_file_header(900, "BIGFILE", len(data_block_indices) * BLOCK_SIZE)
    _set_ffs_data_block_pointers(file_header, data_block_indices[:72])
    _put_u32(file_header, 504, 983)
    blocks[900][:] = file_header
    blocks[983][:] = _make_file_extension_block(983, data_block_indices[72:])

    for index, block_index in enumerate(data_block_indices):
        blocks[block_index][:] = bytes([index & 0xFF]) * BLOCK_SIZE
    return b"".join(bytes(block) for block in blocks)


def _make_ofs_adf_with_extension() -> bytes:
    data_block_indices = list(range(910, 983))
    blocks = [bytearray(BLOCK_SIZE) for _ in range(TOTAL_BLOCKS)]
    blocks[0][:] = _make_boot_block(ROOT_BLOCK, 0)[:BLOCK_SIZE]
    blocks[1][:] = _make_boot_block(ROOT_BLOCK, 0)[BLOCK_SIZE:]
    blocks[ROOT_BLOCK][:] = _make_root_block("Games", [900])

    file_header = _make_file_header(900, "BIGREADME", len(data_block_indices) * 100)
    _set_ffs_data_block_pointers(file_header, data_block_indices[:72])
    _put_u32(file_header, 504, 983)
    blocks[900][:] = file_header
    blocks[983][:] = _make_file_extension_block(983, data_block_indices[72:])

    for index, block_index in enumerate(data_block_indices):
        payload = bytes([65 + (index % 26)]) * 100
        next_block = data_block_indices[index + 1] if index + 1 < len(data_block_indices) else 0
        blocks[block_index][:] = _make_ofs_data_block(900, payload, next_block)
    return b"".join(bytes(block) for block in blocks)


def _make_ofs_adf_with_invalid_file_extents() -> bytes:
    blocks = [bytearray(BLOCK_SIZE) for _ in range(TOTAL_BLOCKS)]
    blocks[0][:] = _make_boot_block(ROOT_BLOCK, 0)[:BLOCK_SIZE]
    blocks[1][:] = _make_boot_block(ROOT_BLOCK, 0)[BLOCK_SIZE:]
    blocks[ROOT_BLOCK][:] = _make_root_block("Games", [900])

    file_header = _make_file_header(900, "BROKEN", 600)
    _set_ffs_data_block_pointers(file_header, [910, 911])
    blocks[900][:] = file_header
    blocks[910][:] = _make_ofs_data_block(900, b"A" * 100, 0)
    return b"".join(bytes(block) for block in blocks)


def _make_non_dos_adf() -> bytes:
    return b"\x00" * (BLOCK_SIZE * TOTAL_BLOCKS)


def _make_non_dos_bootable_adf() -> bytes:
    image = bytearray(BLOCK_SIZE * TOTAL_BLOCKS)
    image[0:4] = b"\x60\x00\x00\x10"
    image[32:40] = b"BOOTCODE"
    return bytes(image)


def _make_dos_bad_root_pointer_adf() -> bytes:
    blocks = [bytearray(BLOCK_SIZE) for _ in range(TOTAL_BLOCKS)]
    blocks[0][:] = _make_boot_block(TOTAL_BLOCKS + 5, 1)[:BLOCK_SIZE]
    blocks[1][:] = _make_boot_block(TOTAL_BLOCKS + 5, 1)[BLOCK_SIZE:]
    return b"".join(bytes(block) for block in blocks)


def _make_dos_bad_root_block_adf() -> bytes:
    blocks = [bytearray(BLOCK_SIZE) for _ in range(TOTAL_BLOCKS)]
    blocks[0][:] = _make_boot_block(ROOT_BLOCK, 1)[:BLOCK_SIZE]
    blocks[1][:] = _make_boot_block(ROOT_BLOCK, 1)[BLOCK_SIZE:]
    return b"".join(bytes(block) for block in blocks)


def _make_dos_custom_boot_adf() -> bytes:
    blocks = [bytearray(BLOCK_SIZE) for _ in range(TOTAL_BLOCKS)]
    blocks[0][:] = _make_boot_block(TOTAL_BLOCKS + 5, 1)[:BLOCK_SIZE]
    blocks[1][:] = _make_boot_block(TOTAL_BLOCKS + 5, 1)[BLOCK_SIZE:]
    blocks[1][16:24] = b"CUSTOMBT"
    return b"".join(bytes(block) for block in blocks)


class AmigaDiskTests(PlatformDiskTestCaseMixin, unittest.TestCase):

    def test_analyze_ffs_adf(self) -> None:
        actual = self.inspect_disk_buffer("amiga-disk", _make_ffs_adf())
        self.assertEqual(actual["format_kind"], "dos")
        self.assertEqual(actual["root_block"], ROOT_BLOCK)
        self.assertEqual(actual["is_dos"], 1)
        self.assertEqual(actual["dos_flags"], 1)
        self.assertEqual(
            actual["entries"],
            [
                {"path": "Workbench", "kind": 3, "byte_size": 0, "header_block": ROOT_BLOCK, "extents": []},
                {
                    "path": "HELLO",
                    "kind": 1,
                    "byte_size": 6,
                    "header_block": 900,
                    "extents": [{"block_index": 910, "image_offset": 910 * 512, "byte_size": 6}],
                },
                {"path": "C", "kind": 2, "byte_size": 0, "header_block": 901, "extents": []},
                {
                    "path": "C/RUNME",
                    "kind": 1,
                    "byte_size": 4,
                    "header_block": 902,
                    "extents": [{"block_index": 911, "image_offset": 911 * 512, "byte_size": 4}],
                },
            ],
        )

    def test_analyze_ofs_adf(self) -> None:
        actual = self.inspect_disk_buffer("amiga-disk", _make_ofs_adf())
        self.assertEqual(actual["format_kind"], "dos")
        self.assertEqual(actual["root_block"], ROOT_BLOCK)
        self.assertEqual(actual["is_dos"], 1)
        self.assertEqual(actual["dos_flags"], 0)
        self.assertEqual(
            actual["entries"],
            [
                {"path": "Games", "kind": 3, "byte_size": 0, "header_block": ROOT_BLOCK, "extents": []},
                {
                    "path": "README",
                    "kind": 1,
                    "byte_size": 10,
                    "header_block": 900,
                    "extents": [
                        {"block_index": 910, "image_offset": 910 * 512 + 24, "byte_size": 5},
                        {"block_index": 911, "image_offset": 911 * 512 + 24, "byte_size": 5},
                    ],
                },
            ],
        )

    def test_analyze_ffs_adf_with_extension_blocks(self) -> None:
        actual = self.inspect_disk_buffer("amiga-disk", _make_ffs_adf_with_extension())
        self.assertEqual(actual["format_kind"], "dos")
        self.assertEqual(actual["entries"][1]["path"], "BIGFILE")
        self.assertEqual(actual["entries"][1]["byte_size"], 73 * BLOCK_SIZE)
        self.assertEqual(len(actual["entries"][1]["extents"]), 73)
        self.assertEqual(actual["entries"][1]["extents"][0], {"block_index": 910, "image_offset": 910 * 512, "byte_size": 512})
        self.assertEqual(actual["entries"][1]["extents"][-1], {"block_index": 982, "image_offset": 982 * 512, "byte_size": 512})

    def test_analyze_ofs_adf_with_extension_blocks(self) -> None:
        actual = self.inspect_disk_buffer("amiga-disk", _make_ofs_adf_with_extension())
        self.assertEqual(actual["format_kind"], "dos")
        self.assertEqual(actual["entries"][1]["path"], "BIGREADME")
        self.assertEqual(actual["entries"][1]["byte_size"], 73 * 100)
        self.assertEqual(len(actual["entries"][1]["extents"]), 73)
        self.assertEqual(actual["entries"][1]["extents"][0], {"block_index": 910, "image_offset": 910 * 512 + 24, "byte_size": 100})
        self.assertEqual(actual["entries"][1]["extents"][-1], {"block_index": 982, "image_offset": 982 * 512 + 24, "byte_size": 100})

    def test_analyze_ofs_adf_with_invalid_file_extents(self) -> None:
        actual = self.inspect_disk_buffer("amiga-disk", _make_ofs_adf_with_invalid_file_extents())
        self.assertEqual(actual["format_kind"], "dos")
        self.assertEqual(actual["entries"][1]["path"], "BROKEN")
        self.assertEqual(actual["entries"][1]["byte_size"], 600)
        self.assertEqual(actual["entries"][1]["extents"], [])

    def test_classifies_non_dos_adf(self) -> None:
        actual = self.inspect_disk_buffer("amiga-disk", _make_non_dos_adf())
        self.assertEqual(actual["format_kind"], "non-dos-blank")
        self.assertEqual(actual["is_dos"], 0)
        self.assertEqual(actual["entry_count"], 0)

    def test_classifies_non_dos_bootable_adf(self) -> None:
        actual = self.inspect_disk_buffer("amiga-disk", _make_non_dos_bootable_adf())
        self.assertEqual(actual["format_kind"], "non-dos-bootable")
        self.assertEqual(actual["is_dos"], 0)
        self.assertEqual(actual["entry_count"], 0)

    def test_classifies_dos_adf_with_invalid_root_pointer(self) -> None:
        actual = self.inspect_disk_buffer("amiga-disk", _make_dos_bad_root_pointer_adf())
        self.assertEqual(actual["format_kind"], "dos-invalid-root-pointer")
        self.assertEqual(actual["is_dos"], 1)
        self.assertEqual(actual["entry_count"], 0)

    def test_classifies_dos_adf_with_invalid_root_block(self) -> None:
        actual = self.inspect_disk_buffer("amiga-disk", _make_dos_bad_root_block_adf())
        self.assertEqual(actual["format_kind"], "dos-invalid-root-block")
        self.assertEqual(actual["is_dos"], 1)
        self.assertEqual(actual["entry_count"], 0)

    def test_classifies_dos_adf_with_custom_boot(self) -> None:
        actual = self.inspect_disk_buffer("amiga-disk", _make_dos_custom_boot_adf())
        self.assertEqual(actual["format_kind"], "dos-custom-boot")
        self.assertEqual(actual["is_dos"], 1)
        self.assertEqual(actual["entry_count"], 0)


if __name__ == "__main__":
    unittest.main()
