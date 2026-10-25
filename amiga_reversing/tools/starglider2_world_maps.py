"""Audit original world-placement streams using the $17E52/$17E94 consumers.

The finite original catalogue has aliases and two formats. Coordinates remain
private; this tool reports extents/counts, not game record bytes or a runtime
reachability claim.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path
from .starglider2_protection import IMAGE_SHA256


def decode_map(payload: bytes, start: int, stride: int) -> dict[str, int]:
    if stride not in (10, 16):
        raise ValueError('Only the two original placement strides are admitted')
    cursor = start-0x1000
    count = 0
    while 0 <= cursor <= len(payload)-2:
        tag = struct.unpack_from('>H', payload, cursor)[0]
        if tag == 0:
            return dict(start=start, end=cursor+0x1002, count=count, stride=stride)
        if not 1 <= tag & 255 <= 147:
            raise ValueError('Placement type outside the conditional original dispatch domain')
        if cursor+stride > len(payload):
            raise ValueError('Truncated placement body')
        cursor += stride
        count += 1
        if count > 249:
            raise ValueError('Placement count plus original player exceeds the 250-record pool')
    raise ValueError('Missing placement terminator')


def audit(payload: bytes) -> dict[str, object]:
    if len(payload) != 412736 or hashlib.sha256(payload).hexdigest() != IMAGE_SHA256:
        raise ValueError('Expected the reviewed Starglider 2 main-copy image')
    base, count = 0x2F9FC, 32
    pointers = struct.unpack_from('>32I', payload, base-0x1000)
    if min(pointers) != base+count*4:
        raise ValueError('Pointer table no longer ends at the first placement tag')
    maps = {}
    for index, start in enumerate(pointers):
        if start % 2 or not base+count*4 <= start < len(payload)+0x1000:
            raise ValueError('Placement pointer outside admitted original data')
        stride = 10 if index < 16 else 16
        record = decode_map(payload, start, stride)
        if start in maps:
            if (maps[start]['end'], maps[start]['count']) != (record['end'], record['count']):
                raise ValueError('Ambiguous shared placement encoding')
            maps[start]['indices'].append(index)
        else:
            maps[start] = dict(**record, indices=[index])
    ordered = sorted(maps.values(), key=lambda item: item['start'])
    if any(a['end'] > b['start'] for a, b in zip(ordered, ordered[1:])):
        raise ValueError('Distinct placement owners overlap')
    if len(ordered) != 14 or sum(m['count'] for m in ordered) != 1139:
        raise ValueError('Original unique map/placement totals changed')
    return dict(schema_version=1, binary_sha256=IMAGE_SHA256,
        pointer_table=dict(start=base, end=base+count*4, entries=count),
        unique_maps=ordered, unique_placement_records=1139,
        map_bytes=sum(m['end']-m['start'] for m in ordered),
        max_original_map_records=max(m['count'] for m in ordered),
        constructor=0x17D90, next_record=0x17E52, extended_record=0x17E94,
        limits=['World index must remain in the original 0..31 catalogue domain',
                'Shared empty maps guarantee only a 2-byte tag, not a full record pointee',
                'Extended WORDs copied to object +$24/+$28 remain type-dependent/opaque',
                'Record counts are static templates, not all gameplay allocations or visits',
                'Sparse gaps and aliases retained; no unused-storage claim'])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.image.read_bytes()), indent=2))

if __name__ == '__main__':
    main()
