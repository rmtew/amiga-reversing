"""Read-only Classic Mac OS HFS catalog/fork access."""

from __future__ import annotations

from dataclasses import dataclass

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
    return mac_roman(data)


def extents(data: bytes, offset: int) -> tuple[tuple[int, int], ...]:
    out: list[tuple[int, int]] = []
    for index in range(3):
        start = be16(data, offset + index * 4)
        count = be16(data, offset + index * 4 + 2)
        if count:
            out.append((start, count))
    return tuple(out)


@dataclass(frozen=True, slots=True)
class HFSDirectoryRecord:
    parent_id: int
    name: str
    cnid: int
    valence: int


@dataclass(frozen=True, slots=True)
class HFSFileRecord:
    parent_id: int
    name: str
    path: str
    cnid: int
    file_type: str
    creator: str
    data_size: int
    resource_size: int
    data_extents: tuple[tuple[int, int], ...]
    resource_extents: tuple[tuple[int, int], ...]

    def inventory_item(self) -> dict[str, object]:
        return {
            "path": self.path,
            "cnid": self.cnid,
            "type": self.file_type,
            "creator": self.creator,
            "data_size": self.data_size,
            "resource_size": self.resource_size,
        }


class HFSVolume:
    def __init__(self, data: bytes) -> None:
        mdb = 1024
        if data[mdb : mdb + 2] != b"BD":
            raise ValueError("classic HFS MDB signature not found at byte 1024")
        self.data = data
        self.volume_name = pascal_string(data, mdb + 36, 27)
        self.allocation_block_count = be16(data, mdb + 18)
        self.allocation_block_size = be32(data, mdb + 20)
        self.allocation_start = be16(data, mdb + 28) * 512
        self.catalog_size = be32(data, mdb + 146)
        self.catalog_extents = extents(data, mdb + 150)
        self.directories, self.files = self._catalog_records()

    def fork_bytes(self, fork_extents: tuple[tuple[int, int], ...], fork_size: int) -> bytes:
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

    def data_fork(self, file_record: HFSFileRecord) -> bytes:
        return self.fork_bytes(file_record.data_extents, file_record.data_size)

    def resource_fork(self, file_record: HFSFileRecord) -> bytes:
        return self.fork_bytes(file_record.resource_extents, file_record.resource_size)

    def find_file(self, path: str) -> HFSFileRecord:
        for file_record in self.files:
            if file_record.path == path:
                return file_record
        raise KeyError(path)

    def _catalog_records(self) -> tuple[tuple[HFSDirectoryRecord, ...], tuple[HFSFileRecord, ...]]:
        tree = _CatalogTree(self.fork_bytes(self.catalog_extents, self.catalog_size))
        directories, file_rows = tree.records()
        dirs_by_id = {directory.cnid: directory for directory in directories}
        files = tuple(
            HFSFileRecord(
                parent_id=file_row.parent_id,
                name=file_row.name,
                path=_build_path(file_row.parent_id, file_row.name, dirs_by_id),
                cnid=file_row.cnid,
                file_type=file_row.file_type,
                creator=file_row.creator,
                data_size=file_row.data_size,
                resource_size=file_row.resource_size,
                data_extents=file_row.data_extents,
                resource_extents=file_row.resource_extents,
            )
            for file_row in file_rows
        )
        return tuple(directories), files


@dataclass(frozen=True, slots=True)
class _CatalogFileRow:
    parent_id: int
    name: str
    cnid: int
    file_type: str
    creator: str
    data_size: int
    resource_size: int
    data_extents: tuple[tuple[int, int], ...]
    resource_extents: tuple[tuple[int, int], ...]


class _CatalogTree:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.node_size = self._read_node_size()

    def records(self) -> tuple[list[HFSDirectoryRecord], list[_CatalogFileRow]]:
        dirs: list[HFSDirectoryRecord] = []
        files: list[_CatalogFileRow] = []
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
                        HFSDirectoryRecord(
                            parent_id=parent_id,
                            name=name,
                            cnid=be32(node, data_offset + 6),
                            valence=be16(node, data_offset + 4),
                        )
                    )
                elif record_type == 0x0200:
                    files.append(
                        _CatalogFileRow(
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

    def _node(self, node_id: int, node_size: int | None = None) -> bytes:
        size = node_size or self.node_size
        offset = node_id * size
        return self.data[offset : offset + size]

    def _read_node_size(self) -> int:
        node_size = 512
        node = self.data[:node_size]
        first_record = self._record_offsets(node, node_size)[0]
        return be16(node, first_record + 18)

    @staticmethod
    def _record_offsets(node: bytes, node_size: int) -> list[int]:
        count = be16(node, 10)
        return [be16(node, node_size - 2 * (index + 1)) for index in range(count)]

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


def _build_path(parent_id: int, name: str, dirs_by_id: dict[int, HFSDirectoryRecord]) -> str:
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
