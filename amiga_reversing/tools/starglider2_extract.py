"""Extract the reviewed UA/WOW Starglider 2 boot reads without running them.

This is a hash-bound disk recipe, not an address scanner or unpacker. The
bootblock's second read is followed by a 0x19310-LONG forward copy and JMP $1000.
The first read is a separately returning intro. Runtime qualification of the
game entry is deliberately separate from this static extraction receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

DISK_SHA256 = "77c633a9270f85361a30ba19175f5940155631ceb6c84b47b1efbb0bf2150ee3"
SPANS = (
    ("bootblock", 0, 1024, None, 12),
    ("intro_read", 0x2C00, 0xDA00, 0x23FF8, 0x24000),
    ("game_read", 0x16000, 0x64E00, 0x1A000, None),
    ("game_copy", 0x16000, 0x19310 * 4, 0x1000, 0x1000),
)


def extract(disk: bytes) -> tuple[dict[str, bytes], dict[str, object]]:
    if len(disk) != 901120 or hashlib.sha256(disk).hexdigest() != DISK_SHA256:
        raise ValueError("Expected the reviewed 901120-byte UA/WOW Starglider 2 disk")
    payloads, spans = {}, []
    for name, offset, size, load, entry in SPANS:
        data = disk[offset:offset + size]
        if len(data) != size:
            raise ValueError(f"Truncated {name}")
        payloads[name] = data
        spans.append(dict(name=name, disk_offset=offset, size=size,
                          load_address=load, entrypoint=entry,
                          sha256=hashlib.sha256(data).hexdigest()))
    return payloads, dict(schema_version=1, disk_sha256=DISK_SHA256,
                          disk_size=len(disk), spans=spans,
                          bootblock_read_setup_sites=[0x4C, 0xA0],
                          copy_loop_source_offset=0x102,
                          copy_iterations=0x19310, copy_width=4,
                          copy_source=0x1A000, copy_destination=0x1000,
                          read_suffix_not_copied=0x1C0,
                          status="static_extraction",
                          limits=["No runtime entry or intro return qualification",
                                  "Not a DOS HUNK or reconstructed disk",
                                  "No claim that every copied byte is code"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("disk", type=Path)
    parser.add_argument("--output", type=Path, required=True,
                        help="Fresh private directory; contains copyrighted payloads")
    args = parser.parse_args()
    payloads, receipt = extract(args.disk.read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in payloads.items():
        (args.output / f"{name}.bin").write_bytes(data)
    (args.output / "extraction.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
