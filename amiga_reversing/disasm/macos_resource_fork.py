"""Classic Mac OS resource fork parsing."""

from __future__ import annotations

import hashlib
from typing import Any


def be16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "big")


def be24(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 3], "big")


def be32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "big")


def signed16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "big", signed=True)


def mac_roman(data: bytes) -> str:
    return data.decode("mac_roman", errors="replace")


def parse_name(data: bytes, name_list_offset: int, name_offset: int) -> str | None:
    if name_offset < 0:
        return None
    offset = name_list_offset + name_offset
    if offset >= len(data):
        return None
    size = data[offset]
    return mac_roman(data[offset + 1 : offset + 1 + size])


def parse_code_metadata(resource_id: int, payload: bytes) -> dict[str, object]:
    if resource_id == 0 and len(payload) >= 16:
        return {
            "kind": "jump_table_segment",
            "above_a5_size": be32(payload, 0),
            "below_a5_size": be32(payload, 4),
            "jump_table_length": be32(payload, 8),
            "jump_table_offset_from_a5": be32(payload, 12),
        }
    if len(payload) >= 4:
        return {
            "kind": "code_segment",
            "first_jump_table_entry_offset": be16(payload, 0),
            "jump_table_entry_count": be16(payload, 2),
        }
    return {"kind": "code_segment"}


def parse_resource_fork(data: bytes, source: str) -> dict[str, Any]:
    entries = _resource_entries(data)
    return {
        "schema_version": 1,
        "source_path": source,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "header": entries["header"],
        "types": entries["types"],
        "resources": sorted(entries["resources"], key=lambda item: (item["type"], item["id"])),
    }


def resource_payload(data: bytes, resource_type: str, resource_id: int) -> bytes:
    entries = _resource_entries(data, include_payloads=True)
    for resource in entries["resources"]:
        if resource["type"] == resource_type and resource["id"] == resource_id:
            payload = resource.get("payload")
            if not isinstance(payload, bytes):
                raise ValueError("internal resource payload was not captured")
            return payload
    raise KeyError(f"{resource_type} {resource_id}")


def _resource_entries(data: bytes, *, include_payloads: bool = False) -> dict[str, Any]:
    if len(data) < 16:
        raise ValueError("resource fork too short")
    data_offset = be32(data, 0)
    map_offset = be32(data, 4)
    data_length = be32(data, 8)
    map_length = be32(data, 12)
    if data_offset + data_length > len(data):
        raise ValueError("resource data area extends beyond file")
    if map_offset + map_length > len(data):
        raise ValueError("resource map extends beyond file")

    type_list_offset = map_offset + be16(data, map_offset + 24)
    name_list_offset = map_offset + be16(data, map_offset + 26)
    type_count = be16(data, type_list_offset) + 1

    types: list[dict[str, Any]] = []
    resources: list[dict[str, Any]] = []
    type_entry = type_list_offset + 2
    for _ in range(type_count):
        resource_type = mac_roman(data[type_entry : type_entry + 4])
        resource_count = be16(data, type_entry + 4) + 1
        ref_list_offset = type_list_offset + be16(data, type_entry + 6)
        types.append({"type": resource_type, "count": resource_count})
        ref_entry = ref_list_offset
        for _ in range(resource_count):
            resource_id = signed16(data, ref_entry)
            name_offset = signed16(data, ref_entry + 2)
            attributes = data[ref_entry + 4]
            resource_data_offset = be24(data, ref_entry + 5)
            payload_offset = data_offset + resource_data_offset
            payload_size = be32(data, payload_offset)
            payload = data[payload_offset + 4 : payload_offset + 4 + payload_size]
            item: dict[str, Any] = {
                "type": resource_type,
                "id": resource_id,
                "name": parse_name(data, name_list_offset, name_offset),
                "attributes": attributes,
                "data_offset": resource_data_offset,
                "size": payload_size,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            if include_payloads:
                item["payload"] = payload
            if resource_type == "CODE":
                item["code"] = parse_code_metadata(resource_id, payload)
            resources.append(item)
            ref_entry += 12
        type_entry += 8

    return {
        "header": {
            "resource_data_offset": data_offset,
            "resource_map_offset": map_offset,
            "resource_data_length": data_length,
            "resource_map_length": map_length,
        },
        "types": types,
        "resources": resources,
    }
