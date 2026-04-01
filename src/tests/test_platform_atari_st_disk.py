from __future__ import annotations

import struct
import unittest

from src.tests._platform_disk_test_utils import PlatformDiskTestCaseMixin


def _u16(value: int) -> bytes:
    return struct.pack("<H", value)


def _u32(value: int) -> bytes:
    return struct.pack("<I", value)


def _pack_dir_entry(name: str, ext: str, attr: int, first_cluster: int, file_size: int) -> bytes:
    name_raw = name.encode("ascii").ljust(8, b" ")
    ext_raw = ext.encode("ascii").ljust(3, b" ")
    return (
        name_raw
        + ext_raw
        + bytes([attr])
        + (b"\x00" * 10)
        + _u16(0)
        + _u16(0)
        + _u16(first_cluster)
        + _u32(file_size)
    )


def _encode_fat12(entries: dict[int, int], fat_size_bytes: int, media_descriptor: int = 0xF9) -> bytes:
    max_index = max(entries.keys(), default=1)
    values = [0] * (max_index + 1)
    values[0] = media_descriptor | 0xF00
    values[1] = 0xFFF
    for index, value in entries.items():
        values[index] = value & 0xFFF
    fat = bytearray(fat_size_bytes)
    for index, value in enumerate(values):
        offset = (index * 3) // 2
        if offset + 1 >= fat_size_bytes:
            break
        if index & 1:
            word = fat[offset] | (fat[offset + 1] << 8)
            word = (word & 0x000F) | (value << 4)
        else:
            word = fat[offset] | (fat[offset + 1] << 8)
            word = (word & 0xF000) | value
        fat[offset] = word & 0xFF
        fat[offset + 1] = (word >> 8) & 0xFF
    return bytes(fat)


def _make_boot_sector(
    *,
    bytes_per_sector: int,
    sectors_per_cluster: int,
    reserved_sector_count: int,
    fat_count: int,
    root_entry_count: int,
    total_sectors: int,
    sectors_per_fat: int,
    sectors_per_track: int,
    side_count: int,
) -> bytes:
    boot = bytearray(512)
    boot[0:3] = b"\x60\x00\x00"
    boot[3:11] = b"GEMDOS  "
    boot[11:13] = _u16(bytes_per_sector)
    boot[13] = sectors_per_cluster
    boot[14:16] = _u16(reserved_sector_count)
    boot[16] = fat_count
    boot[17:19] = _u16(root_entry_count)
    boot[19:21] = _u16(total_sectors)
    boot[21] = 0xF9
    boot[22:24] = _u16(sectors_per_fat)
    boot[24:26] = _u16(sectors_per_track)
    boot[26:28] = _u16(side_count)
    boot[28:30] = _u16(0)
    return bytes(boot)


def _make_synthetic_st_disk_with_subdir() -> bytes:
    boot = _make_boot_sector(
        bytes_per_sector=512,
        sectors_per_cluster=1,
        reserved_sector_count=1,
        fat_count=1,
        root_entry_count=16,
        total_sectors=10,
        sectors_per_fat=1,
        sectors_per_track=10,
        side_count=1,
    )
    fat = _encode_fat12({2: 0xFFF, 3: 0xFFF, 4: 0xFFF}, 512)
    root = bytearray(512)
    root[0:32] = _pack_dir_entry("TESTDISK", "", 0x08, 0, 0)
    root[32:64] = _pack_dir_entry("HELLO", "PRG", 0x20, 2, 6)
    root[64:96] = _pack_dir_entry("AUTO", "", 0x10, 3, 0)
    root[96] = 0
    cluster2 = b"ABCDEF" + (b"\x00" * (512 - 6))
    cluster3 = bytearray(512)
    cluster3[0:32] = _pack_dir_entry(".", "", 0x10, 3, 0)
    cluster3[32:64] = _pack_dir_entry("..", "", 0x10, 0, 0)
    cluster3[64:96] = _pack_dir_entry("BOOT", "PRG", 0x20, 4, 4)
    cluster3[96] = 0
    cluster4 = b"\x60\x1A\x00\x00" + (b"\x00" * (512 - 4))
    clusters = cluster2 + bytes(cluster3) + cluster4 + (b"\x00" * (512 * 4))
    return boot + fat + bytes(root) + clusters


def _make_synthetic_st_disk_with_multicluster_subdir() -> bytes:
    boot = _make_boot_sector(
        bytes_per_sector=512,
        sectors_per_cluster=1,
        reserved_sector_count=1,
        fat_count=1,
        root_entry_count=16,
        total_sectors=10,
        sectors_per_fat=1,
        sectors_per_track=10,
        side_count=1,
    )
    fat = _encode_fat12({3: 4, 4: 0xFFF, 5: 0xFFF}, 512)
    root = bytearray(512)
    root[0:32] = _pack_dir_entry("AUTO", "", 0x10, 3, 0)
    root[32] = 0
    cluster2 = b"\x00" * 512
    cluster3 = bytearray(512)
    cluster3[0:32] = _pack_dir_entry(".", "", 0x10, 3, 0)
    cluster3[32:64] = _pack_dir_entry("..", "", 0x10, 0, 0)
    cluster3[64:96] = _pack_dir_entry("DUMMY", "TXT", 0x20, 0, 0)
    for offset in range(96, 512, 32):
        cluster3[offset] = 0xE5
    cluster4 = bytearray(512)
    cluster4[0:32] = _pack_dir_entry("BOOT", "PRG", 0x20, 5, 4)
    cluster4[32] = 0
    cluster5 = b"\x60\x1A\x00\x00" + (b"\x00" * (512 - 4))
    clusters = cluster2 + bytes(cluster3) + bytes(cluster4) + cluster5 + (b"\x00" * (512 * 3))
    return boot + fat + bytes(root) + clusters


def _make_synthetic_st_disk_with_fragmented_file() -> bytes:
    boot = _make_boot_sector(
        bytes_per_sector=512,
        sectors_per_cluster=1,
        reserved_sector_count=1,
        fat_count=1,
        root_entry_count=16,
        total_sectors=10,
        sectors_per_fat=1,
        sectors_per_track=10,
        side_count=1,
    )
    fat = _encode_fat12({2: 4, 3: 0x000, 4: 0xFFF}, 512)
    root = bytearray(512)
    root[0:32] = _pack_dir_entry("FRAG", "PRG", 0x20, 2, 700)
    root[32] = 0
    cluster2 = b"A" * 512
    cluster3 = b"\x00" * 512
    cluster4 = b"B" * 512
    clusters = cluster2 + cluster3 + cluster4 + (b"\x00" * (512 * 4))
    return boot + fat + bytes(root) + clusters


def _make_synthetic_oversized_st_disk_with_invalid_extra_cluster() -> bytes:
    boot = _make_boot_sector(
        bytes_per_sector=512,
        sectors_per_cluster=1,
        reserved_sector_count=1,
        fat_count=1,
        root_entry_count=16,
        total_sectors=8,
        sectors_per_fat=1,
        sectors_per_track=8,
        side_count=1,
    )
    fat = _encode_fat12({2: 7, 7: 0xFFF}, 512)
    root = bytearray(512)
    root[0:32] = _pack_dir_entry("BAD", "PRG", 0x20, 2, 700)
    root[32] = 0
    logical_clusters = (b"A" * 512) + (b"\x00" * (512 * 3))
    trailing_extra = (b"B" * 512) + (b"\x00" * 512)
    return boot + fat + bytes(root) + logical_clusters + trailing_extra


class AtariStDiskTests(PlatformDiskTestCaseMixin, unittest.TestCase):

    def test_analyze_st_root_and_subdir_entries(self) -> None:
        actual = self.inspect_disk_buffer("atari-st-disk", _make_synthetic_st_disk_with_subdir())
        self.assertEqual(actual["bytes_per_sector"], 512)
        self.assertEqual(actual["sectors_per_cluster"], 1)
        self.assertEqual(actual["fat_count"], 1)
        self.assertEqual(
            actual["entries"],
            [
                {
                    "path": "TESTDISK",
                    "kind": 3,
                    "file_size": 0,
                    "first_cluster": 0,
                    "attributes": 8,
                    "is_executable_candidate": 0,
                    "extents": [],
                },
                {
                    "path": "HELLO.PRG",
                    "kind": 1,
                    "file_size": 6,
                    "first_cluster": 2,
                    "attributes": 32,
                    "is_executable_candidate": 1,
                    "extents": [{"image_offset": 1536, "byte_size": 6, "cluster_index": 2}],
                },
                {
                    "path": "AUTO",
                    "kind": 2,
                    "file_size": 0,
                    "first_cluster": 3,
                    "attributes": 16,
                    "is_executable_candidate": 0,
                    "extents": [{"image_offset": 2048, "byte_size": 512, "cluster_index": 3}],
                },
                {
                    "path": "AUTO/BOOT.PRG",
                    "kind": 1,
                    "file_size": 4,
                    "first_cluster": 4,
                    "attributes": 32,
                    "is_executable_candidate": 1,
                    "extents": [{"image_offset": 2560, "byte_size": 4, "cluster_index": 4}],
                },
            ],
        )

    def test_analyze_st_fragmented_file_extents(self) -> None:
        actual = self.inspect_disk_buffer("atari-st-disk", _make_synthetic_st_disk_with_fragmented_file())
        self.assertEqual(actual["entry_count"], 1)
        self.assertEqual(
            actual["entries"][0],
            {
                "path": "FRAG.PRG",
                "kind": 1,
                "file_size": 700,
                "first_cluster": 2,
                "attributes": 32,
                "is_executable_candidate": 1,
                "extents": [
                    {"image_offset": 1536, "byte_size": 512, "cluster_index": 2},
                    {"image_offset": 2560, "byte_size": 188, "cluster_index": 4},
                ],
            },
        )

    def test_analyze_st_multicluster_subdir_extents(self) -> None:
        actual = self.inspect_disk_buffer("atari-st-disk", _make_synthetic_st_disk_with_multicluster_subdir())
        self.assertEqual(
            actual["entries"],
            [
                {
                    "path": "AUTO",
                    "kind": 2,
                    "file_size": 0,
                    "first_cluster": 3,
                    "attributes": 16,
                    "is_executable_candidate": 0,
                    "extents": [
                        {"image_offset": 2048, "byte_size": 512, "cluster_index": 3},
                        {"image_offset": 2560, "byte_size": 512, "cluster_index": 4},
                    ],
                },
                {
                    "path": "AUTO/DUMMY.TXT",
                    "kind": 1,
                    "file_size": 0,
                    "first_cluster": 0,
                    "attributes": 32,
                    "is_executable_candidate": 0,
                    "extents": [],
                },
                {
                    "path": "AUTO/BOOT.PRG",
                    "kind": 1,
                    "file_size": 4,
                    "first_cluster": 5,
                    "attributes": 32,
                    "is_executable_candidate": 1,
                    "extents": [{"image_offset": 3072, "byte_size": 4, "cluster_index": 5}],
                },
            ],
        )

    def test_rejects_fat_chain_into_trailing_bytes_outside_logical_disk(self) -> None:
        with self.assertRaises(AssertionError) as raised:
            self.inspect_disk_buffer("atari-st-disk", _make_synthetic_oversized_st_disk_with_invalid_extra_cluster())
        self.assertIn("Invalid FAT12 cluster chain", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
