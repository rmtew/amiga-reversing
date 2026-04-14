from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE_PATH = ROOT / "resources" / "platform_atari_st" / "Devpac v3.10 (1992)(HiSoft).st"
DISK_CLI = ROOT / "src" / "build" / "platform_disk_cli.exe"
OUTPUT_DIR = ROOT / "ext" / "atarist_includes" / "devpac_3_10" / "include"

WANTED_PATHS = (
    "INCDIR/BIOS.I",
    "INCDIR/GEMDOS.I",
    "INCDIR/XBIOS.I",
    "INCDIR/GEMMACRO.I",
    "INCDIR/AESLIB.S",
    "INCDIR/VDILIB.S",
)


def load_disk_entries() -> dict[str, dict]:
    output = subprocess.check_output(
        [str(DISK_CLI), "inspect-disk", "atari-st-disk", str(IMAGE_PATH)],
        cwd=ROOT,
        text=True,
    )
    payload = json.loads(output)
    return {entry["path"]: entry for entry in payload.get("entries", []) if isinstance(entry, dict)}


def extract_entry_bytes(image_bytes: bytes, entry: dict) -> bytes:
    remaining = int(entry["file_size"])
    extracted = bytearray()
    for extent in entry.get("extents", []):
        image_offset = int(extent["image_offset"])
        byte_size = min(int(extent["byte_size"]), remaining)
        extracted.extend(image_bytes[image_offset:image_offset + byte_size])
        remaining -= byte_size
        if remaining <= 0:
            break
    return bytes(extracted)


def main() -> None:
    entries = load_disk_entries()
    image_bytes = IMAGE_PATH.read_bytes()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for disk_path in WANTED_PATHS:
        entry = entries.get(disk_path)
        if entry is None:
            raise SystemExit(f"missing Devpac include on disk: {disk_path}")
        out_path = OUTPUT_DIR / Path(disk_path).name
        out_path.write_bytes(extract_entry_bytes(image_bytes, entry))


if __name__ == "__main__":
    main()
