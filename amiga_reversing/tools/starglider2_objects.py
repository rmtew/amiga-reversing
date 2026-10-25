"""Audit the original Starglider 2 secondary object dispatch and name catalogue.

A finite hash-bound source recipe, not a runtime object-domain proof. Encoded
jump targets and name pointers are evidence; canonical interpretation lives in
the target Manual Action Log. No game strings or payload bytes are exported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

from amiga_reversing.tools.starglider2_models import PAYLOAD_SHA256


def inventory(payload: bytes) -> dict:
    if len(payload) != 412736 or hashlib.sha256(payload).hexdigest() != PAYLOAD_SHA256:
        raise ValueError("Expected the reviewed 412736-byte Starglider 2 game copy")
    load, dispatch, names, count = 0x1000, 0x821C, 0xF334, 148
    offsets = [struct.unpack_from(">h", payload, dispatch - load + index * 2)[0]
               for index in range(count)]
    targets = [dispatch + offset for offset in offsets]
    if dispatch + count * 2 != 0x8344:
        raise ValueError("Dispatch extent does not end at the known following code")
    if any(target % 2 or not load <= target < load + len(payload)
           or dispatch <= target < dispatch + count * 2 for target in targets):
        raise ValueError("Invalid original encoded dispatch target")
    pointers = [struct.unpack_from(">I", payload, names - load + index * 4)[0]
                for index in range(count)]
    if min(pointers) != names + count * 4:
        raise ValueError("Name pointers do not end at the first text")
    ends = []
    for pointer in pointers:
        if not load <= pointer < load + len(payload):
            raise ValueError("Name pointer outside original image")
        end = payload.index(0, pointer - load) + load + 1
        if any(not 32 <= byte < 127 for byte in payload[pointer - load:end - load - 1]):
            raise ValueError("Non-printable original object name")
        ends.append(end)
    start, end = min(pointers), max(ends)
    if (start, end) != (0xF584, 0xFD07):
        raise ValueError("Unexpected original text-pool extent")
    if any(byte and not 32 <= byte < 127 for byte in payload[start - load:end - load]):
        raise ValueError("Text pool contains non-text storage")
    return dict(schema_version=1, binary_sha256=PAYLOAD_SHA256,
                load_address=load, dispatch_site=0x8218,
                dispatch_table=dict(start=dispatch, end=dispatch + count * 2,
                                    entries=count, entry_width=2,
                                    target_entries=[dict(target=target,
                                                         indices=[i for i, value in enumerate(targets)
                                                                  if value == target])
                                                    for target in sorted(set(targets))]),
                names=dict(table_start=names, table_end=names + count * 4,
                           entries=count, unique_pointers=len(set(pointers)),
                           text_start=start, text_end=end, text_bytes=end - start,
                           pointer_alias_counts=sorted(Counter(pointers).values(), reverse=True)),
                external_restart=dict(entry=0xC698, jump_site=0xC6DE,
                                      stack_pointer_source=0, target_pointer_source=4),
                limits=["Dispatch contract requires original object type in 0..147",
                        "Encoded targets are not proof that every type occurs in gameplay",
                        "Name aliases/placeholders and spare strings are preserved, not declared dead",
                        "Low-vector restart target/platform state remains unresolved",
                        "No standalone ABI or runtime/output equivalence claim"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(inventory(args.payload.read_bytes()), indent=2) + "\n")


if __name__ == "__main__":
    main()
