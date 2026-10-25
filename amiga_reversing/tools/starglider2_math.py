"""Audit stored Starglider 2 rotation/heading coefficients without regenerating them."""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path
from .starglider2_protection import IMAGE_SHA256


def audit(image: bytes) -> dict[str, object]:
    if len(image) != 412736 or hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
        raise ValueError('Expected the reviewed Starglider 2 main-copy image')
    words = struct.unpack_from('>5120h', image, 0x13F60-0x1000)
    differences = Counter(words[4096+i]-words[i] for i in range(1024))
    if (min(words), max(words)) != (-16383, 16383) or differences != {0: 958, -1: 66}:
        raise ValueError('Original sine/cosine coefficient identity changed')
    if [words[i] for i in [0, 1024, 2048, 3072, 4096]] != [0, 16383, 0, -16383, 0]:
        raise ValueError('Original cardinal coefficients changed')
    return dict(schema_version=1, binary_sha256=IMAGE_SHA256,
        trigonometry=dict(start=0x13F60, end=0x16760, stored_words=5120,
            sine_view=[0x13F60, 0x15F60], cosine_view=[0x14760, 0x16760],
            overlapping_bytes=6144, index_mask=4095, index_width=2,
            min_value=min(words), max_value=max(words),
            tail_minus_first_quarter_counts={str(k):v for k,v in differences.items()},
            sha256=hashlib.sha256(image[0x12F60:0x15760]).hexdigest(),
            pointer_initializer=0x1F0E, matrix_builder=0x284C),
        arctangent=dict(start=0x13D5C, end=0x13F5C, words=256,
            index_mask=255, index_width=2, consumers=[0xB036, 0xB08E],
            following_four_bytes_unclaimed=[0x13F5C, 0x13F60],
            sha256=hashlib.sha256(image[0x12D5C:0x12F5C]).hexdigest()),
        limits=['Stored coefficients preserved; no floating-point resampling or rounding correction',
                'The two overlapping windows are not byte-identical periodic aliases',
                'Masked lookup bounds do not prove all arithmetic inputs or all callers safe',
                'No new runtime or all-path numerical equivalence qualification'])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.image.read_bytes()), indent=2))

if __name__ == '__main__':
    main()
