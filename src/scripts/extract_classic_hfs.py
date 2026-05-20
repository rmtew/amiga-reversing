#!/usr/bin/env python3
"""Read-only extractor for classic Macintosh HFS volumes.

This intentionally supports the subset needed by the MPW-GM NDIF image:
the MDB, catalog B-tree, and the first three catalog extents stored on file
records. Extents overflow support can be added when an image needs it.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


CATALOG_ROOT_PARENT_ID = 1
ROOT_DIR_ID = 2
NODE_KIND_LEAF = -1


def be16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "big")


def be32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "big")


def mac_roman(data: bytes) -> str:
    return data.decode("mac_roman", errors="replace")


def pascal_string(data: bytes, offset: int, max_len: int) -> str:
    size = min(data[offset], max_len)
    return mac_roman(data[offset + 1 : offset + 1 + size])


def fourcc(data: bytes) -> str:
    return data.decode("mac_roman", errors="replace")


def extents(data: bytes, offset: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for index in range(3):
        start = be16(data, offset + index * 4)
        count = be16(data, offset + index * 4 + 2)
        if count:
            out.append((start, count))
    return out


def safe_component(name: str) -> str:
    value = name.replace(":", "/").split("/")[-1]
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip()
    return value or "_"


@dataclass
class DirectoryRecord:
    parent_id: int
    name: str
    cnid: int
    valence: int


@dataclass
class FileRecord:
    parent_id: int
    name: str
    cnid: int
    file_type: str
    creator: str
    data_size: int
    resource_size: int
    data_extents: list[tuple[int, int]]
    resource_extents: list[tuple[int, int]]


class HFSImage:
    def __init__(self, data: bytes) -> None:
        self.data = data
        mdb = 1024
        if data[mdb : mdb + 2] != b"BD":
            raise ValueError("classic HFS MDB signature not found at byte 1024")
        self.volume_name = pascal_string(data, mdb + 36, 27)
        self.allocation_block_count = be16(data, mdb + 18)
        self.allocation_block_size = be32(data, mdb + 20)
        self.allocation_start = be16(data, mdb + 28) * 512
        self.catalog_size = be32(data, mdb + 146)
        self.catalog_extents = extents(data, mdb + 150)

    def fork_bytes(self, fork_extents: list[tuple[int, int]], fork_size: int) -> bytes:
        chunks: list[bytes] = []
        remaining = fork_size
        for start, count in fork_extents:
            if remaining <= 0:
                break
            offset = self.allocation_start + start * self.allocation_block_size
            size = min(count * self.allocation_block_size, remaining)
            chunks.append(self.data[offset : offset + size])
            remaining -= size
        if remaining:
            raise ValueError("fork is not fully covered by catalog extents; extents overflow support is needed")
        return b"".join(chunks)

    def catalog_bytes(self) -> bytes:
        catalog = self.fork_bytes(self.catalog_extents, self.catalog_size)
        if len(catalog) != self.catalog_size:
            raise ValueError("catalog fork is not fully covered by MDB extents")
        return catalog


class CatalogTree:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.node_size = self._read_node_size()

    def _node(self, node_id: int, node_size: int | None = None) -> bytes:
        size = node_size or self.node_size
        offset = node_id * size
        return self.data[offset : offset + size]

    @staticmethod
    def _record_offsets(node: bytes, node_size: int) -> list[int]:
        count = be16(node, 10)
        return [be16(node, node_size - 2 * (index + 1)) for index in range(count)]

    def _read_node_size(self) -> int:
        node_size = 512
        node = self.data[:node_size]
        first_record = self._record_offsets(node, node_size)[0]
        return be16(node, first_record + 18)

    def records(self) -> tuple[list[DirectoryRecord], list[FileRecord]]:
        dirs: list[DirectoryRecord] = []
        files: list[FileRecord] = []
        for node_id in range(len(self.data) // self.node_size):
            node = self._node(node_id)
            kind = int.from_bytes(node[8:9], "big", signed=True)
            if kind != NODE_KIND_LEAF:
                continue
            for offset in self._record_offsets(node, self.node_size):
                parent_id, name, data_offset = self._parse_key(node, offset)
                record_type = be16(node, data_offset)
                if record_type == 0x0100:
                    dirs.append(
                        DirectoryRecord(
                            parent_id=parent_id,
                            name=name,
                            cnid=be32(node, data_offset + 6),
                            valence=be16(node, data_offset + 4),
                        )
                    )
                elif record_type == 0x0200:
                    files.append(
                        FileRecord(
                            parent_id=parent_id,
                            name=name,
                            cnid=be32(node, data_offset + 20),
                            file_type=fourcc(node[data_offset + 4 : data_offset + 8]),
                            creator=fourcc(node[data_offset + 8 : data_offset + 12]),
                            data_size=be32(node, data_offset + 26),
                            resource_size=be32(node, data_offset + 36),
                            data_extents=extents(node, data_offset + 74),
                            resource_extents=extents(node, data_offset + 86),
                        )
                    )
        return dirs, files

    @staticmethod
    def _parse_key(node: bytes, offset: int) -> tuple[int, str, int]:
        key_len = node[offset]
        parent_id = be32(node, offset + 2)
        name_len = node[offset + 6]
        name = mac_roman(node[offset + 7 : offset + 7 + name_len])
        data_offset = offset + key_len + 1
        if data_offset & 1:
            data_offset += 1
        return parent_id, name, data_offset


def build_path(parent_id: int, name: str, dirs_by_id: dict[int, DirectoryRecord]) -> str:
    parts = [name]
    seen: set[int] = set()
    current_id = parent_id
    while current_id not in (CATALOG_ROOT_PARENT_ID, ROOT_DIR_ID) and current_id not in seen:
        seen.add(current_id)
        directory = dirs_by_id.get(current_id)
        if directory is None:
            break
        parts.append(directory.name)
        current_id = directory.parent_id
    return "/".join(reversed([part for part in parts if part]))


def write_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--extract", type=Path)
    parser.add_argument("--path-prefix", default="")
    parser.add_argument("--resource-forks", action="store_true")
    args = parser.parse_args()

    image = HFSImage(args.image.read_bytes())
    catalog = CatalogTree(image.catalog_bytes())
    dirs, files = catalog.records()
    dirs_by_id = {directory.cnid: directory for directory in dirs}

    inventory: dict[str, object] = {
        "volume_name": image.volume_name,
        "allocation_block_size": image.allocation_block_size,
        "allocation_block_count": image.allocation_block_count,
        "directories": len(dirs),
        "files": len(files),
        "items": [],
    }

    items: list[dict[str, object]] = []
    for file_record in sorted(files, key=lambda item: build_path(item.parent_id, item.name, dirs_by_id).lower()):
        path = build_path(file_record.parent_id, file_record.name, dirs_by_id)
        item = {
            "path": path,
            "cnid": file_record.cnid,
            "type": file_record.file_type,
            "creator": file_record.creator,
            "data_size": file_record.data_size,
            "resource_size": file_record.resource_size,
        }
        items.append(item)
        selected = not args.path_prefix or path == args.path_prefix or path.startswith(args.path_prefix.rstrip("/") + "/")
        if args.extract and selected and file_record.data_size:
            out_path = args.extract / "data" / Path(*[safe_component(part) for part in path.split("/")])
            write_file(out_path, image.fork_bytes(file_record.data_extents, file_record.data_size))
        if args.extract and selected and args.resource_forks and file_record.resource_size:
            out_path = args.extract / "resource" / Path(*[safe_component(part) for part in path.split("/")])
            write_file(out_path, image.fork_bytes(file_record.resource_extents, file_record.resource_size))

    inventory["items"] = items
    if args.inventory:
        args.inventory.parent.mkdir(parents=True, exist_ok=True)
        args.inventory.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(inventory, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
