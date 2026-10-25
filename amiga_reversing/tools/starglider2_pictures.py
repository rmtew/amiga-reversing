"""Audit the two hash-bound picture resources consumed by original $3A50.

This is the Amiga four-plane path, not generic PackBits or a rendered-frame
comparison. Underfilled planes remain underfilled; no pixel bytes are invented.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from .starglider2_protection import IMAGE_SHA256


def plane_byte_offset(index: int) -> int:
    if not 0 <= index < 8000:
        raise ValueError('Outside the admitted 40-byte by 200-row plane')
    return (index % 200)*40 + index//200


def decode_plane(data: bytes, offset: int = 0) -> tuple[bytes, int, dict[str, int]]:
    if not 0 <= offset < len(data):
        raise ValueError('Missing plane stream')
    decoded = bytearray()
    repeats = literals = 0
    while offset < len(data):
        control = data[offset]
        offset += 1
        if control == 0:
            return bytes(decoded), offset, dict(repeats=repeats, literals=literals)
        if control < 128:
            if offset >= len(data):
                raise ValueError('Truncated repeat')
            decoded.extend(bytes([data[offset]])*control)
            repeats += 1
            offset += 1
        else:
            count = (-control) & 127
            if count == 0:
                raise ValueError('$80 would execute 65536 DBF iterations; outside admitted bounded streams')
            if offset+count > len(data):
                raise ValueError('Truncated literal')
            decoded.extend(data[offset:offset+count])
            literals += 1
            offset += count
        if len(decoded) > 8000:
            raise ValueError('Stream exceeds admitted plane footprint')
    raise ValueError('Missing plane terminator')


def audit(image: bytes) -> list[dict[str, object]]:
    if len(image) != 412736 or hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
        raise ValueError('Expected the reviewed Starglider 2 main-copy image')
    results = []
    for name, start, expected_end, expected_counts in [
        ('cockpit_picture', 0x5341C, 0x56552, [7999, 8000, 7999, 7999]),
        ('argonaut_splash_picture', 0x56554, 0x59F29, [7999]*4),
    ]:
        cursor = start-0x1000+32
        planes = []
        for _ in range(4):
            decoded, cursor, counts = decode_plane(image, cursor)
            planes.append(dict(written_bytes=len(decoded), **counts))
        if cursor+0x1000 != expected_end or [p['written_bytes'] for p in planes] != expected_counts:
            raise ValueError('Picture bounds or original underfill changed')
        packed = image[start-0x1000+32:cursor]
        results.append(dict(name=name, start=start, palette_bytes=32,
                            stream_start=start+32, end=expected_end,
                            packed_bytes=len(packed), packed_sha256=hashlib.sha256(packed).hexdigest(),
                            width=320, height=200, plane_stride=0x2000, row_stride=40,
                            planes=planes, unknown_destination_bytes=32000-sum(expected_counts)))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.image.read_bytes()), indent=2))

if __name__ == '__main__':
    main()
