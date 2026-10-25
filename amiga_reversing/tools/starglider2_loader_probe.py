"""Bounded normal-media Starglider 2 extraction check, using the shared session.

No direct-payload adapter, guest memory/register writes, or routine calls. The
sole input is the port-one blue button (the intro's POTINP secondary-button
line). This qualifies loader entry and bytes, not gameplay or output equality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .copperline_session import HeadlessCopperlineSession
from .copperline_control import CopperlineProcess
from .copperline_runtime import wait_for_pc
from .starglider2_extract import extract
from .starglider2_protection import START, SIZE, subtract_stage


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disk", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--copperline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument('--check-protection-subtraction', action='store_true',
                        help='Verify the first startup transform at PC $1F0C')
    args = parser.parse_args()
    payloads, extraction = extract(args.disk.read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    session = HeadlessCopperlineSession(rom_path=args.rom,
        target_payload_path=args.disk, binary_path=args.copperline,
        floppy0=args.disk, state_directory=args.output)
    receipt = dict(schema_version=1, profile=session.plan(), extraction=extraction,
                   input_events=[], stages=[], status="incomplete",
                   limits=["CPU entry and loaded bytes only; no DMA or output comparison",
                           "No gameplay completion qualification"])

    def save():
        (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")

    save()
    try:
        with CopperlineProcess(session.binary_path, rom=session.rom_path,
                               floppy=session.floppy0) as process:
            client = process.client
            for name, entry, load, payload in [
                ("intro_entry", 0x24000, 0x23FF8, payloads["intro_read"]),
                ("game_entry", 0x1000, 0x1000, payloads["game_copy"]),
            ]:
                stage = dict(name=name, entry=entry, load_address=load,
                             wait=wait_for_pc(client, entry, 60))
                receipt["stages"].append(stage)
                save()
                if stage["wait"]["status"] != "hit":
                    raise RuntimeError(f"{name}: {stage['wait']['termination']}")
                observed = client.read_memory(load, len(payload))
                stage.update(size=len(payload), byte_exact=observed == payload,
                             observed_sha256=hashlib.sha256(observed).hexdigest(),
                             registers=client.registers())
                save()
                if observed != payload:
                    stage["first_difference"] = next(i for i, (a, b) in enumerate(zip(observed, payload)) if a != b)
                    raise RuntimeError(f"{name}: extracted bytes do not match memory")
                print(f"{name}: PC {entry:06X}, all {len(payload)} bytes match", flush=True)
                if name == "intro_entry":
                    receipt["input_events"].append(dict(after=name, port=1, blue=True))
                    client.joystick(port=1, blue=True)
            client.joystick(port=1)
            receipt["input_events"].append(dict(after="game_entry", port=1, blue=False))
            if args.check_protection_subtraction:
                expected = subtract_stage(payloads['game_copy'][START-0x1000:START-0x1000+SIZE])
                stage = dict(name='protection_subtraction', entry=0x1F0C,
                             load_address=START, wait=wait_for_pc(client, 0x1F0C, 60))
                receipt['stages'].append(stage)
                save()
                if stage['wait']['status'] != 'hit':
                    raise RuntimeError('Protection subtraction not observed within bounds')
                observed = client.read_memory(START, SIZE)
                stage.update(size=SIZE, byte_exact=observed == expected,
                             observed_sha256=hashlib.sha256(observed).hexdigest(),
                             registers=client.registers())
                save()
                if observed != expected:
                    raise RuntimeError('Protection subtraction bytes differ')
                print(f'protection_subtraction: all {SIZE} bytes match', flush=True)
                receipt['limits'].append('Rotation/decoded protection entry not qualified by SUB-stage match')
            receipt["status"] = "normal_media_loader_entries_and_bytes_exact"
    except Exception as exc:
        receipt.update(status="failed_or_not_observed", error=str(exc))
        raise
    finally:
        save()


if __name__ == "__main__":
    main()
