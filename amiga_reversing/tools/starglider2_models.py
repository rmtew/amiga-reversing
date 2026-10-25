"""Check the source-backed model catalogue in the reviewed Starglider 2 image.

This finite recipe follows consumers at $49E0/$4A2A, $56BC and $583C. It does
not infer variant-table lengths or identify models by their visual appearance.
The JSON contains addresses/counts, never model coordinates or game bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

PAYLOAD_SHA256 = "662976920689c38fd47271ed7e656a92caf20aa20ce0b8801db2bdc77ba864d9"
LOAD_ADDRESS = 0x1000
TABLE_ADDRESS = 0x18974
TABLE_COUNT = 104


def inventory(payload: bytes) -> dict:
    digest = hashlib.sha256(payload).hexdigest()
    if len(payload) != 412736 or digest != PAYLOAD_SHA256:
        raise ValueError("Expected the reviewed 412736-byte Starglider 2 game copy")

    def read(address: int, fmt: str) -> int:
        offset = address - LOAD_ADDRESS
        size = struct.calcsize(fmt)
        if offset < 0 or offset + size > len(payload):
            raise ValueError(f"Model reference outside recovered image: ${address:X}")
        return struct.unpack_from(fmt, payload, offset)[0]

    def word(address: int) -> int:
        return read(address, ">H")

    def long(address: int) -> int:
        return read(address, ">I")
    pointers = [long(TABLE_ADDRESS + index * 4) for index in range(TABLE_COUNT)]
    models, spans = [], []
    for header in sorted(set(pointers)):
        last_vertex, face_count, coordinate_count = (word(header + n) for n in (0, 2, 4))
        faces, vertices, coordinates, variants = (long(header + n) for n in (6, 10, 14, 18))
        auxiliary_count = word(header + 22)
        auxiliary = long(header + 24) if auxiliary_count else None
        if coordinates + coordinate_count * 2 != vertices:
            raise ValueError("Coordinate pool does not end at vertex-reference records")
        for vertex in range(last_vertex + 1):
            for axis in range(3):
                reference = word(vertices + vertex * 8 + axis * 2) & 0x7FFF
                if reference % 2 or reference >= coordinate_count * 2:
                    raise ValueError("Vertex coordinate reference outside its WORD pool")

        def face_end(start: int, count: int, mask: int) -> int:
            cursor = start
            for _ in range(count):
                count_vertices = (word(cursor) >> 8) & mask
                if count_vertices == 0:
                    raise ValueError("Empty original face command")
                for index in range(count_vertices):
                    offset = word(cursor + 2 + index * 2)
                    if offset % 8 or offset > last_vertex * 8:
                        raise ValueError("Face reference outside its vertex records")
                cursor += 2 + count_vertices * 2
            return cursor

        normal_end = face_end(faces, face_count, 7)
        if normal_end != (auxiliary if auxiliary_count else coordinates):
            raise ValueError("Face stream does not end at its next declared component")
        if auxiliary_count and face_end(auxiliary, auxiliary_count, 15) != coordinates:
            raise ValueError("Auxiliary faces do not end at the coordinate pool")
        parts = [("faces", faces, normal_end),
                 ("coordinates", coordinates, vertices),
                 ("vertices", vertices, vertices + (last_vertex + 1) * 8)]
        if auxiliary_count:
            parts.append(("auxiliary_faces", auxiliary, coordinates))
        for role, start, end in parts:
            if end <= start or start < LOAD_ADDRESS or end > LOAD_ADDRESS + len(payload):
                raise ValueError("Invalid model component extent")
            spans.append((start, end, role, header))
        models.append(dict(header=header, header_size=28 if auxiliary_count else 24,
                           table_indices=[i for i, value in enumerate(pointers) if value == header],
                           last_vertex_index=last_vertex, face_count=face_count,
                           coordinate_word_count=coordinate_count,
                           faces=faces, vertices=vertices, coordinates=coordinates,
                           variant_table=variants, auxiliary_face_count=auxiliary_count,
                           auxiliary_faces=auxiliary, components=[dict(role=r, start=s, end=e)
                                                                 for r, s, e in parts]))
    for previous, following in zip(models, models[1:]):
        if previous["header"] + previous["header_size"] != following["header"]:
            raise ValueError("Gap or overlap between packed model headers")
    if models[0]["header"] != TABLE_ADDRESS + TABLE_COUNT * 4:
        raise ValueError("Headers do not begin immediately after the pointer table")
    if models[-1]["header"] + models[-1]["header_size"] != 0x19570:
        raise ValueError("Unexpected end of the reviewed header catalogue")
    ordered = sorted(spans)
    for previous, following in zip(ordered, ordered[1:]):
        if previous[1] > following[0]:
            raise ValueError("Overlapping model component owners require separate review")
    totals = {role: sum(end - start for start, end, kind, _ in spans if kind == role)
              for role in ("faces", "auxiliary_faces", "coordinates", "vertices")}
    return dict(schema_version=1, binary_sha256=digest, load_address=LOAD_ADDRESS,
                table_address=TABLE_ADDRESS, table_count=TABLE_COUNT,
                unique_headers=len(models), component_bytes=totals, models=models,
                limits=["Static original-record validation, not runtime reachability",
                        "Variant pointer table lengths/selector domains remain unresolved",
                        "Face flags/material meanings and visual model identities not inferred",
                        "No arbitrary replacement-input safety or complete image classification"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(inventory(args.payload.read_bytes()), indent=2) + "\n")


if __name__ == "__main__":
    main()
