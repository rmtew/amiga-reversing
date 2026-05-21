"""Classic Mac OS MPW Asm executable/container import."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
from collections.abc import Iterable
from pathlib import Path

from amiga_reversing.disasm.c_backend import (
    extract_macos_hfs_code_resource_bytes_with_c_backend,
)
from amiga_reversing.disasm.macos_fork_roles import (
    classify_inventory_item,
    resource_type_counts,
)
from amiga_reversing.disasm.macos_hfs import HFSVolume
from amiga_reversing.disasm.macos_resource_fork import (
    parse_resource_fork,
    resource_payload,
)

MPW_ASM_PATH = "MPW-GM/MPW/Tools/Asm"
DEFAULT_NDIF2RAW_PATH = Path("ext/tools/ndif2raw/ndif2raw.exe")
UNSUPPORTED_SEGMENT_LOADER_AREAS = (
    "relocation/fixups",
    "complete Segment Loader behavior",
    "source mapping",
    "byte-for-byte round-trip",
)


def import_mpw_asm_container(
    image_path: Path,
    *,
    ndif2raw_path: Path = DEFAULT_NDIF2RAW_PATH,
    path: str = MPW_ASM_PATH,
) -> dict[str, object]:
    hfs_bytes = _read_hfs_bytes(image_path, ndif2raw_path=ndif2raw_path)
    volume = HFSVolume(hfs_bytes)
    file_record = volume.find_file(path)
    data_fork = volume.data_fork(file_record)
    resource_fork = volume.resource_fork(file_record)
    resource_summary = parse_resource_fork(resource_fork, f"{image_path.as_posix()}::{path}/rsrc")
    roles = classify_inventory_item(
        file_record.inventory_item(),
        resource_type_counts=resource_type_counts(resource_summary),
    )
    code_resources = [
        resource for resource in resource_summary["resources"] if isinstance(resource, dict) and resource.get("type") == "CODE"
    ]
    code0 = _single_code_resource(code_resources, 0)
    code1 = _single_code_resource(code_resources, 1)
    code1_payload = resource_payload(resource_fork, "CODE", 1)

    return {
        "platform": "macos",
        "container_kind": "hfs_file_with_resource_fork",
        "source_image": image_path.as_posix(),
        "volume": {
            "name": volume.volume_name,
            "allocation_block_size": volume.allocation_block_size,
            "allocation_block_count": volume.allocation_block_count,
        },
        "file": {
            "path": file_record.path,
            "cnid": file_record.cnid,
            "type": file_record.file_type,
            "creator": file_record.creator,
            "data_size": file_record.data_size,
            "resource_size": file_record.resource_size,
            "fork_roles": roles["fork_roles"],
        },
        "data_fork": {
            "role": "data_string_payload",
            "size": len(data_fork),
            "sha256": hashlib.sha256(data_fork).hexdigest(),
        },
        "resource_fork": {
            "role": "executable_resource_fork",
            "size": resource_summary["size"],
            "sha256": resource_summary["sha256"],
            "header": resource_summary["header"],
            "types": resource_summary["types"],
        },
        "code0": {
            "role": "jump_table_segment",
            "resource": _resource_inventory_row(code0),
            "metadata": code0.get("code"),
        },
        "code_resources": [_resource_inventory_row(resource) for resource in code_resources],
        "selected_code_segment": {
            "resource_type": "CODE",
            "id": 1,
            "name": code1.get("name"),
            "role": "code_segment",
            "payload_size": code1.get("size"),
            "code_header_size": 4,
            "code_bytes_size": max(0, len(code1_payload) - 4),
            "sha256": code1.get("sha256"),
            "listing_preview": _code_listing_preview(code1_payload[4:], max_words=8),
        },
        "unsupported": list(UNSUPPORTED_SEGMENT_LOADER_AREAS),
    }


def extract_mpw_asm_code_bytes(
    image_path: Path,
    *,
    resource_id: int = 1,
    ndif2raw_path: Path = DEFAULT_NDIF2RAW_PATH,
    path: str = MPW_ASM_PATH,
) -> bytes:
    hfs_bytes = read_macos_hfs_image_bytes(image_path, ndif2raw_path=ndif2raw_path)
    if resource_id != 0:
        return extract_macos_hfs_code_resource_bytes_with_c_backend(hfs_bytes, path, resource_id)
    volume = HFSVolume(hfs_bytes)
    file_record = volume.find_file(path)
    return resource_payload(volume.resource_fork(file_record), "CODE", resource_id)


def _read_hfs_bytes(image_path: Path, *, ndif2raw_path: Path) -> bytes:
    return read_macos_hfs_image_bytes(image_path, ndif2raw_path=ndif2raw_path)


def read_macos_hfs_image_bytes(image_path: Path, *, ndif2raw_path: Path = DEFAULT_NDIF2RAW_PATH) -> bytes:
    data = image_path.read_bytes()
    if data[1024:1026] == b"BD":
        return data
    if not ndif2raw_path.exists():
        raise FileNotFoundError(f"NDIF provider is required for non-raw image: {ndif2raw_path}")
    with tempfile.TemporaryDirectory(prefix="macos-asm-import-") as temp_dir:
        output = Path(temp_dir) / "image.raw"
        subprocess.run(
            [str(ndif2raw_path), "--format=macbinary", str(image_path), str(output)],
            check=True,
            capture_output=True,
        )
        return output.read_bytes()


def _single_code_resource(resources: Iterable[dict[str, object]], resource_id: int) -> dict[str, object]:
    for resource in resources:
        if resource.get("id") == resource_id:
            return resource
    raise KeyError(f"CODE {resource_id}")


def _resource_inventory_row(resource: dict[str, object]) -> dict[str, object]:
    return {
        "type": resource.get("type"),
        "id": resource.get("id"),
        "name": resource.get("name"),
        "size": resource.get("size"),
        "sha256": resource.get("sha256"),
        "code": resource.get("code"),
    }


def _code_listing_preview(code: bytes, *, max_words: int) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for offset in range(0, min(len(code), max_words * 2), 2):
        chunk = code[offset : offset + 2]
        out.append(
            {
                "offset": offset,
                "bytes": chunk.hex(" ").upper(),
                "directive": "dc.w" if len(chunk) == 2 else "dc.b",
                "value": f"${int.from_bytes(chunk, 'big'):04X}" if len(chunk) == 2 else f"${chunk[0]:02X}",
            }
        )
    return out
