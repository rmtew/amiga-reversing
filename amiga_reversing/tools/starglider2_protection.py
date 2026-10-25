"""Reversible, hash-bound view of Starglider 2's protected code/data bytes.

The original startup subtracts an incrementing LONG key; conditional picture/
load paths subsequently ROL.W the first half twice and ROR.W the second thrice.
This is an analysis view, not a replacement executable or protection bypass.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

IMAGE_SHA256 = '662976920689c38fd47271ed7e656a92caf20aa20ce0b8801db2bdc77ba864d9'
IMAGE_BASE = 0x1000
START = 0x12F80
DECLARED_END = 0x13D1E
SIZE = (DECLARED_END - START) // 4 * 4
CONTEXT_END = 0x13D5C
ENTRY = 0x13BFC
KEY = 0x32597635


def _rol16(value: int, count: int) -> int:
    return ((value << count) | (value >> (16 - count))) & 0xFFFF


def subtract_stage(encoded: bytes) -> bytes:
    if len(encoded) != SIZE:
        raise ValueError(f'Expected exactly {SIZE} protected bytes')
    return b''.join(((int.from_bytes(encoded[i:i+4], 'big') - KEY - i//4)
                     & 0xFFFFFFFF).to_bytes(4, 'big') for i in range(0, SIZE, 4))


def decode(encoded: bytes) -> bytes:
    subtracted = subtract_stage(encoded)
    result = bytearray()
    for i in range(0, SIZE, 4):
        result.extend(_rol16(int.from_bytes(subtracted[i:i+2], 'big'), 2).to_bytes(2, 'big'))
        result.extend(_rol16(int.from_bytes(subtracted[i+2:i+4], 'big'), 13).to_bytes(2, 'big'))
    return bytes(result)


def encode(decoded: bytes) -> bytes:
    """Invert both stages, including LONG carry and modulo-32 arithmetic."""
    if len(decoded) != SIZE:
        raise ValueError(f'Expected exactly {SIZE} decoded bytes')
    result = bytearray()
    for i in range(0, SIZE, 4):
        first = _rol16(int.from_bytes(decoded[i:i+2], 'big'), 14)
        second = _rol16(int.from_bytes(decoded[i+2:i+4], 'big'), 3)
        result.extend((((first << 16) | second) + KEY + i//4 & 0xFFFFFFFF).to_bytes(4, 'big'))
    return bytes(result)


def extract(image: bytes) -> tuple[bytes, dict[str, object]]:
    if len(image) != 412736 or hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
        raise ValueError('Expected the reviewed original Starglider 2 main-copy image')
    encoded = image[START-IMAGE_BASE:START-IMAGE_BASE+SIZE]
    decoded = decode(encoded)
    assert encode(decoded) == encoded
    return decoded, dict(schema_version=1, parent_sha256=IMAGE_SHA256,
        source_offset=START-IMAGE_BASE, load_address=START, entrypoint=ENTRY,
        size=SIZE, long_count=SIZE//4, declared_end=DECLARED_END,
        untransformed_tail_size=2, key=KEY,
        encoded_sha256=hashlib.sha256(encoded).hexdigest(),
        decoded_sha256=hashlib.sha256(decoded).hexdigest(), inverse_exact=True,
        subtraction_loop=0x1F04, rotation_loops=[0x1F38, 0xE444],
        limits=['Static decoded view; conditional execution requires separate evidence',
                'Original payload remains encoded and is not replaced by this view',
                'Two bytes before the declared end are outside the LONG loops'])


def extract_view(image: bytes) -> tuple[bytes, dict[str, object]]:
    """Keep adjacent original trampolines as context, without transforming them."""
    decoded, receipt = extract(image)
    context = image[START-IMAGE_BASE+SIZE:CONTEXT_END-IMAGE_BASE]
    view = decoded + context
    receipt.update(context_end=CONTEXT_END, unchanged_context_size=len(context),
                   analysis_view_size=len(view),
                   analysis_view_sha256=hashlib.sha256(view).hexdigest(),
                   unchanged_context_sha256=hashlib.sha256(context).hexdigest())
    return view, receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    view, receipt = extract_view(args.image.read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'binary.bin').write_bytes(view)
    (args.output/'transformation.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    main()
