#!/usr/bin/env py.exe
"""Analyze Amiga disk images (ADF files).

Handles both AmigaDOS (OFS/FFS) and non-DOS (custom format) disks.
Produces a JSON summary of disk contents, block usage, and detected
signatures. Can optionally extract files from AmigaDOS disks.

Uses knowledge from knowledge/amiga_disk_formats.json for format details.
"""

import argparse
import datetime
import json
import math
import os
import struct
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# Constants
# ============================================================

BSIZE = 512
AMIGA_EPOCH = datetime.datetime(1978, 1, 1)

# Block types
T_HEADER = 2
T_DATA = 8
T_LIST = 16

# Secondary types
ST_ROOT = 1
ST_USERDIR = 2
ST_FILE = -3  # stored as 0xFFFFFFFD

# DOS type names
DOS_TYPES = {
    0x00: ("OFS", "DOS\\0 - Old File System"),
    0x01: ("FFS", "DOS\\1 - Fast File System"),
    0x02: ("OFS-Intl", "DOS\\2 - OFS International"),
    0x03: ("FFS-Intl", "DOS\\3 - FFS International"),
    0x04: ("OFS-DC", "DOS\\4 - OFS DirCache+Intl"),
    0x05: ("FFS-DC", "DOS\\5 - FFS DirCache+Intl"),
    0x06: ("OFS-LNFS", "DOS\\6 - LNFS OFS"),
    0x07: ("FFS-LNFS", "DOS\\7 - LNFS FFS"),
}

# Known magic signatures (bytes, name)
SIGNATURES = [
    (b"\x00\x00\x03\xf3", "HUNK_HEADER"),
    (b"PP20", "PP20"),
    (b"PX20", "PX20"),
    (b"RNC\x01", "RNC1"),
    (b"RNC\x02", "RNC2"),
    (b"IMP!", "Imploder"),
    (b"FORM", "IFF_FORM"),
]

# M68K instruction patterns (big-endian words)
M68K_PATTERNS = {
    0x4E75: "RTS",
    0x4E73: "RTE",
    0x4E71: "NOP",
    0x4E72: "STOP",
    0x4EF9: "JMP_abs",
    0x4EB9: "JSR_abs",
}

# ============================================================
# Low-level helpers
# ============================================================

def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]

def s32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">i", data, offset)[0]

def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from(">H", data, offset)[0]

def read_block(data: bytes, block_num: int) -> bytes:
    start = block_num * BSIZE
    if start + BSIZE > len(data):
        return b"\x00" * BSIZE
    return data[start:start + BSIZE]

def read_bcpl_string(data: bytes, offset: int, max_len: int = 30) -> str:
    length = data[offset]
    if length > max_len:
        length = max_len
    return data[offset + 1:offset + 1 + length].decode("latin-1", errors="replace")


def compute_boot_checksum(boot_data: bytes) -> int:
    """Compute bootblock checksum with carry wraparound."""
    s = 0
    for i in range(256):  # 1024 bytes = 256 longwords
        if i == 1:  # skip checksum field at offset 4
            continue
        val = u32(boot_data, i * 4)
        s += val
        if s > 0xFFFFFFFF:
            s = (s + 1) & 0xFFFFFFFF  # carry wraps
    return (~s) & 0xFFFFFFFF


def compute_block_checksum(block: bytes) -> int:
    """Compute standard AmigaDOS block checksum."""
    s = 0
    for i in range(128):  # 512 bytes = 128 longwords
        if i == 5:  # skip checksum at offset 0x14
            continue
        s = (s + u32(block, i * 4)) & 0xFFFFFFFF
    return (-s) & 0xFFFFFFFF


def verify_block_checksum(block: bytes) -> bool:
    """Verify block checksum sums to 0."""
    s = 0
    for i in range(128):
        s = (s + u32(block, i * 4)) & 0xFFFFFFFF
    return s == 0


def amigados_hash(name: str, table_size: int = 72, international: bool = False) -> int:
    """AmigaDOS filename hash function."""
    h = len(name)
    for c in name:
        o = ord(c)
        # toupper
        if 0x61 <= o <= 0x7A:
            o -= 0x20
        elif international and 0xE0 <= o <= 0xFE and o != 0xF7:
            o -= 0x20
        h = ((h * 13) + o) & 0x7FF
    return h % table_size


def amiga_date_to_iso(days: int, mins: int, ticks: int) -> str:
    """Convert Amiga date to ISO 8601 string."""
    try:
        dt = AMIGA_EPOCH + datetime.timedelta(days=days, minutes=mins, seconds=ticks // 50)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (OverflowError, ValueError):
        return f"invalid({days},{mins},{ticks})"


def protection_to_str(prot: int) -> str:
    """Convert protection bits to string like '----rwed'."""
    # Bits 0-3 (RWED) are inverted: 0 means SET
    # Bits 4-7 (HSPA) are normal: 1 means SET
    chars = ""
    chars += "h" if prot & 0x80 else "-"
    chars += "s" if prot & 0x40 else "-"
    chars += "p" if prot & 0x20 else "-"
    chars += "a" if prot & 0x10 else "-"
    chars += "r" if not (prot & 0x08) else "-"
    chars += "w" if not (prot & 0x04) else "-"
    chars += "e" if not (prot & 0x02) else "-"
    chars += "d" if not (prot & 0x01) else "-"
    return chars


def shannon_entropy(data: bytes) -> float:
    """Calculate Shannon entropy in bits per byte."""
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    n = len(data)
    entropy = 0.0
    for f in freq:
        if f > 0:
            p = f / n
            entropy -= p * math.log2(p)
    return entropy


# ============================================================
# Boot block parsing
# ============================================================

def parse_boot_block(data: bytes) -> dict:
    """Parse the 1024-byte bootblock (blocks 0-1)."""
    boot = data[:1024]
    magic = boot[:3]
    flags = boot[3]
    checksum = u32(boot, 4)
    rootblock_ptr = u32(boot, 8)
    bootcode = boot[0x0C:]

    is_dos = magic == b"DOS"
    expected_cksum = compute_boot_checksum(boot)

    fs_short = ""
    fs_desc = ""
    if is_dos:
        info = DOS_TYPES.get(flags, ("unknown", f"DOS\\{flags}"))
        fs_short, fs_desc = info

    # Scan bootcode for signatures
    sigs = []
    for pattern, name in SIGNATURES:
        idx = bootcode.find(pattern)
        if idx >= 0:
            sigs.append({"type": name, "offset_in_bootcode": idx})

    return {
        "magic": magic.hex(),
        "magic_ascii": magic.decode("latin-1", errors="replace"),
        "is_dos": is_dos,
        "flags_byte": flags,
        "fs_type": fs_short,
        "fs_description": fs_desc,
        "checksum": f"0x{checksum:08X}",
        "checksum_valid": checksum == expected_cksum,
        "rootblock_ptr": rootblock_ptr,
        "bootcode_size": len(bootcode),
        "bootcode_has_code": any(b != 0 for b in bootcode),
        "bootcode_entropy": round(shannon_entropy(bootcode), 2),
        "signatures": sigs,
    }


# ============================================================
# AmigaDOS filesystem parsing
# ============================================================

def parse_root_block(data: bytes, block_num: int) -> dict:
    """Parse the root block."""
    block = read_block(data, block_num)

    type_field = u32(block, 0)
    ht_size = u32(block, 0x0C)
    if ht_size > 128 or ht_size == 0:
        ht_size = 72  # default, may still be corrupt
    hash_table = [u32(block, 0x18 + i * 4) for i in range(min(ht_size, 72))]
    sec_type = s32(block, BSIZE - 4)

    bm_flag = s32(block, BSIZE - 200)
    bm_pages = [u32(block, BSIZE - 196 + i * 4) for i in range(25)]

    volume_name = read_bcpl_string(block, BSIZE - 80, 30)

    r_days, r_mins, r_ticks = u32(block, BSIZE - 92), u32(block, BSIZE - 88), u32(block, BSIZE - 84)
    v_days, v_mins, v_ticks = u32(block, BSIZE - 40), u32(block, BSIZE - 36), u32(block, BSIZE - 32)
    c_days, c_mins, c_ticks = u32(block, BSIZE - 28), u32(block, BSIZE - 24), u32(block, BSIZE - 20)

    return {
        "block_num": block_num,
        "type": type_field,
        "type_valid": type_field == T_HEADER,
        "sec_type": sec_type,
        "sec_type_valid": sec_type == ST_ROOT,
        "ht_size": ht_size,
        "hash_table": hash_table,
        "checksum_valid": verify_block_checksum(block),
        "bm_flag": bm_flag,
        "bm_flag_valid": bm_flag == -1,
        "bm_pages": [p for p in bm_pages if p != 0],
        "volume_name": volume_name,
        "root_date": amiga_date_to_iso(r_days, r_mins, r_ticks),
        "volume_date": amiga_date_to_iso(v_days, v_mins, v_ticks),
        "creation_date": amiga_date_to_iso(c_days, c_mins, c_ticks),
    }


def parse_file_header(data: bytes, block_num: int) -> Optional[dict]:
    """Parse a file or directory header block."""
    block = read_block(data, block_num)

    type_field = u32(block, 0)
    if type_field != T_HEADER:
        return None

    sec_type = s32(block, BSIZE - 4)
    is_dir = sec_type == ST_USERDIR
    high_seq = u32(block, 0x08)
    first_data = u32(block, 0x10)

    # Read data block pointers (or hash table for directories)
    raw_ptrs = [u32(block, 0x18 + i * 4) for i in range(72)]

    name = read_bcpl_string(block, BSIZE - 80, 30)
    byte_size = u32(block, BSIZE - 188)
    protection = u32(block, BSIZE - 192)
    comment = read_bcpl_string(block, BSIZE - 184, 79)
    d_days, d_mins, d_ticks = u32(block, BSIZE - 92), u32(block, BSIZE - 88), u32(block, BSIZE - 84)
    hash_chain = u32(block, BSIZE - 16)
    parent = u32(block, BSIZE - 12)
    extension = u32(block, BSIZE - 8)

    # Collect data blocks in file order
    data_blocks = []
    if not is_dir and high_seq > 0:
        # Pointers fill from the END of the 72-entry array upward:
        # Index 71 = first data block, index 70 = second, etc.
        # So valid entries are at indices (72 - high_seq) through 71
        start_idx = max(0, 72 - high_seq)
        valid = [p for p in raw_ptrs[start_idx:72] if p != 0]
        valid.reverse()  # reverse to get file order (first block first)
        data_blocks = valid

    # Follow extension blocks
    ext_blocks = []
    ext = extension
    visited = {block_num}
    while ext and ext not in visited:
        visited.add(ext)
        ext_block = read_block(data, ext)
        ext_type = u32(ext_block, 0)
        if ext_type != T_LIST:
            break
        ext_blocks.append(ext)
        ext_high_seq = u32(ext_block, 0x08)
        ext_ptrs = [u32(ext_block, 0x18 + i * 4) for i in range(72)]
        ext_start = max(0, 72 - ext_high_seq)
        valid = [p for p in ext_ptrs[ext_start:72] if p != 0]
        valid.reverse()
        data_blocks.extend(valid)
        ext = u32(ext_block, BSIZE - 8)

    return {
        "block_num": block_num,
        "name": name,
        "is_directory": is_dir,
        "sec_type": sec_type,
        "size": byte_size,
        "protection": protection_to_str(protection),
        "comment": comment if comment else None,
        "date": amiga_date_to_iso(d_days, d_mins, d_ticks),
        "hash_chain": hash_chain,
        "parent": parent,
        "extension_blocks": ext_blocks,
        "data_blocks": data_blocks,
        "data_block_count": len(data_blocks),
        "checksum_valid": verify_block_checksum(block),
        # For directories: store hash table for recursive walk
        "_hash_table": raw_ptrs if is_dir else None,
    }


def walk_directory(data: bytes, hash_table: list, parent_path: str,
                   total_sectors: int) -> list:
    """Recursively walk an AmigaDOS directory tree."""
    entries = []
    visited = set()

    for slot_ptr in hash_table:
        block_num = slot_ptr
        while block_num and block_num not in visited and block_num < total_sectors:
            visited.add(block_num)
            entry = parse_file_header(data, block_num)
            if not entry:
                break

            full_path = f"{parent_path}/{entry['name']}" if parent_path else entry["name"]
            entry["full_path"] = full_path

            entries.append(entry)

            # Recurse into subdirectories
            if entry["is_directory"] and entry["_hash_table"]:
                sub_entries = walk_directory(
                    data, entry["_hash_table"], full_path, total_sectors
                )
                entries.extend(sub_entries)

            block_num = entry["hash_chain"]

    return entries


def parse_bitmap(data: bytes, bm_pages: list, total_sectors: int) -> dict:
    """Parse bitmap blocks to get free/allocated block map."""
    block_map = [None] * total_sectors  # None = unknown
    # Blocks 0-1 always allocated (bootblock)
    block_map[0] = False
    block_map[1] = False

    checksum_ok = True
    for bm_block_num in bm_pages:
        if bm_block_num == 0 or bm_block_num >= total_sectors:
            continue
        bm_block = read_block(data, bm_block_num)
        if not verify_block_checksum(bm_block):
            checksum_ok = False

        # Bitmap data starts at offset 4 (after checksum longword)
        # Each bit represents a block: 1=free, 0=allocated
        for byte_idx in range(4, BSIZE):
            byte_val = bm_block[byte_idx]
            for bit in range(8):
                block_idx = 2 + (byte_idx - 4) * 8 + bit
                if block_idx < total_sectors:
                    block_map[block_idx] = bool(byte_val & (1 << bit))

    free_count = sum(1 for x in block_map if x is True)
    alloc_count = sum(1 for x in block_map if x is False)

    return {
        "checksum_valid": checksum_ok,
        "free_blocks": free_count,
        "allocated_blocks": alloc_count,
        "total_blocks": total_sectors,
        "percent_used": round(alloc_count / total_sectors * 100, 1),
        "_block_map": block_map,  # internal, not serialized
    }


# ============================================================
# Block usage map
# ============================================================

def build_block_usage(total_sectors: int, root_block_num: int,
                      bm_pages: list, files: list,
                      bitmap_map: list) -> dict:
    """Build a map of what each block is used for."""
    usage = ["unknown"] * total_sectors
    owner = [""] * total_sectors

    # Boot
    usage[0] = "boot"
    usage[1] = "boot"

    # Root
    usage[root_block_num] = "root"

    # Bitmap blocks
    for bm in bm_pages:
        if 0 < bm < total_sectors:
            usage[bm] = "bitmap"

    # Files and directories
    for f in files:
        bn = f["block_num"]
        if 0 <= bn < total_sectors:
            usage[bn] = "dir_header" if f["is_directory"] else "file_header"
            owner[bn] = f.get("full_path", f["name"])

        for db in f.get("data_blocks", []):
            if 0 <= db < total_sectors:
                usage[db] = "data"
                owner[db] = f.get("full_path", f["name"])

        for eb in f.get("extension_blocks", []):
            if 0 <= eb < total_sectors:
                usage[eb] = "extension"
                owner[eb] = f.get("full_path", f["name"])

    # Cross-ref with bitmap
    orphan_blocks = []
    free_with_data_blocks = []
    for i in range(total_sectors):
        if bitmap_map and i < len(bitmap_map):
            if bitmap_map[i] is True and usage[i] == "unknown":
                usage[i] = "free"
            elif bitmap_map[i] is False and usage[i] == "unknown":
                usage[i] = "allocated_orphan"
                orphan_blocks.append(i)

    # Summary by usage type
    summary = {}
    for u in usage:
        summary[u] = summary.get(u, 0) + 1

    return {
        "summary": summary,
        "orphan_blocks": orphan_blocks,
        "_usage": usage,
        "_owner": owner,
    }


# ============================================================
# Signature detection
# ============================================================

_lvo_cache = None

def _load_lvo_names() -> dict:
    """Load exec.library LVO→name map from OS reference."""
    global _lvo_cache
    if _lvo_cache is not None:
        return _lvo_cache
    _lvo_cache = {}
    ref_path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "amiga_os_reference.json")
    if os.path.exists(ref_path):
        try:
            with open(ref_path, encoding="utf-8") as f:
                data = json.load(f)
            # Build per-library LVO maps
            for lib_key, lib in data.get("libraries", {}).items():
                for func in lib.get("functions", []):
                    lvo = func.get("lvo")
                    if lvo and lib_key == "exec.library":
                        _lvo_cache[lvo] = func["name"]
        except Exception:
            pass
    return _lvo_cache


def detect_signatures(data: bytes, total_sectors: int) -> list:
    """Scan entire disk for known byte patterns."""
    results = []
    seen = set()

    for block_num in range(total_sectors):
        block = read_block(data, block_num)
        for pattern, name in SIGNATURES:
            idx = 0
            while True:
                idx = block.find(pattern, idx)
                if idx < 0:
                    break
                key = (name, block_num, idx)
                if key not in seen:
                    seen.add(key)
                    detail = {}
                    if name == "IFF_FORM":
                        # Try to read FORM type
                        form_size = u32(block, idx + 4) if idx + 8 <= len(block) else 0
                        form_type = block[idx + 8:idx + 12].decode("ascii", errors="replace") if idx + 12 <= len(block) else "?"
                        detail = {"form_type": form_type, "form_size": form_size}
                    elif name == "HUNK_HEADER":
                        detail = {"description": "Amiga executable hunk"}

                    results.append({
                        "type": name,
                        "block": block_num,
                        "offset_in_block": idx,
                        "disk_offset": block_num * BSIZE + idx,
                        **detail,
                    })
                idx += 1

        # Check for OS library calls: JSR -xxx(A6) = $4EAE xxxx
        for off in range(0, len(block) - 3, 2):
            word = u16(block, off)
            if word == 0x4EAE:
                lvo = struct.unpack_from(">h", block, off + 2)[0]  # signed
                if lvo < 0 and lvo > -1000:
                    results.append({
                        "type": "OS_call",
                        "block": block_num,
                        "offset_in_block": off,
                        "disk_offset": block_num * BSIZE + off,
                        "lvo": lvo,
                    })

    return results


# ============================================================
# Non-DOS / track analysis
# ============================================================

def scan_ascii_strings(data: bytes, min_length: int = 4) -> list:
    """Find printable ASCII runs."""
    strings = []
    current = []
    start = 0
    for i, b in enumerate(data):
        if 0x20 <= b <= 0x7E:
            if not current:
                start = i
            current.append(chr(b))
        else:
            if len(current) >= min_length:
                strings.append({"offset": start, "text": "".join(current)})
            current = []
    if len(current) >= min_length:
        strings.append({"offset": start, "text": "".join(current)})
    return strings


def analyze_track(data: bytes, track_num: int, sectors_per_track: int) -> dict:
    """Analyze a single track for patterns."""
    first_block = track_num * sectors_per_track
    track_data = data[first_block * BSIZE:(first_block + sectors_per_track) * BSIZE]

    if len(track_data) == 0:
        return {"track": track_num, "empty": True}

    is_empty = all(b == 0 for b in track_data)
    entropy = round(shannon_entropy(track_data), 2)

    # M68K code detection
    m68k_hits = []
    for off in range(0, len(track_data) - 1, 2):
        word = u16(track_data, off)
        if word in M68K_PATTERNS:
            m68k_hits.append({"offset": off, "instruction": M68K_PATTERNS[word]})

    # ASCII strings
    ascii_strings = scan_ascii_strings(track_data, 6)

    # Signatures
    sigs = []
    for pattern, name in SIGNATURES:
        idx = track_data.find(pattern)
        if idx >= 0:
            sigs.append({"type": name, "offset": idx})

    return {
        "track": track_num,
        "cylinder": track_num // 2,
        "head": track_num % 2,
        "first_block": first_block,
        "empty": is_empty,
        "entropy": entropy,
        "m68k_pattern_count": len(m68k_hits),
        "has_code": len(m68k_hits) > 3,  # heuristic threshold
        "ascii_strings": ascii_strings[:20],  # cap output
        "signatures": sigs,
    }


# ============================================================
# File extraction
# ============================================================

def extract_file(data: bytes, entry: dict, output_dir: str, is_ffs: bool):
    """Extract a single file from the disk image."""
    if entry["is_directory"]:
        dir_path = os.path.join(output_dir, entry["full_path"])
        os.makedirs(dir_path, exist_ok=True)
        return

    file_path = os.path.join(output_dir, entry["full_path"])
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    file_size = entry["size"]
    collected = bytearray()

    for db_num in entry["data_blocks"]:
        block = read_block(data, db_num)
        if is_ffs:
            collected.extend(block)
        else:
            # OFS: skip 24-byte header
            data_size = u32(block, 0x0C)
            collected.extend(block[0x18:0x18 + data_size])

    # Truncate to actual file size
    collected = collected[:file_size]

    with open(file_path, "wb") as f:
        f.write(collected)


# ============================================================
# Main analysis
# ============================================================

def analyze_adf(adf_path: str, extract_dir: str = None,
                include_tracks: bool = False, verbose: bool = False) -> dict:
    """Main analysis function."""
    with open(adf_path, "rb") as f:
        data = f.read()

    file_size = len(data)

    # Determine variant
    if file_size == 901120:
        variant = "DD"
        sectors_per_track = 11
        total_sectors = 1760
        root_block_num = 880
    elif file_size == 1802240:
        variant = "HD"
        sectors_per_track = 22
        total_sectors = 3520
        root_block_num = 1760
    else:
        # Try to handle non-standard sizes
        if file_size % BSIZE != 0:
            print(f"Warning: file size {file_size} not a multiple of {BSIZE}", file=sys.stderr)
        total_sectors = file_size // BSIZE
        sectors_per_track = 11  # assume DD layout
        root_block_num = total_sectors // 2
        variant = f"custom({file_size})"

    if verbose:
        print(f"Disk: {adf_path} ({variant}, {total_sectors} sectors)", file=sys.stderr)

    # ---- Boot block ----
    boot = parse_boot_block(data)
    is_dos = boot["is_dos"]
    is_ffs = boot["flags_byte"] & 0x01 == 1 if is_dos else False
    is_intl = boot["flags_byte"] & 0x02 == 2 if is_dos else False

    if verbose:
        dtype = boot["fs_description"] if is_dos else "Non-DOS"
        print(f"  Type: {dtype}, checksum {'OK' if boot['checksum_valid'] else 'FAIL'}", file=sys.stderr)

    result = {
        "disk_info": {
            "path": os.path.basename(adf_path),
            "size": file_size,
            "variant": variant,
            "total_sectors": total_sectors,
            "sectors_per_track": sectors_per_track,
            "is_dos": is_dos,
        },
        "boot_block": boot,
    }

    # ---- AmigaDOS filesystem ----
    if is_dos:
        root = parse_root_block(data, root_block_num)
        # Verify root block is actually valid
        if not root["type_valid"] or not root["sec_type_valid"]:
            if verbose:
                print(f"  Root block invalid (type={root['type']}, sec_type={root['sec_type']}), treating as non-DOS", file=sys.stderr)
            is_dos = False
            result["disk_info"]["is_dos"] = False
            result["disk_info"]["dos_note"] = "Boot says DOS but root block is invalid"
            result["root_block_attempt"] = root

    if is_dos:
        if verbose:
            print(f"  Volume: {root['volume_name']}", file=sys.stderr)

        files = walk_directory(data, root["hash_table"], "", total_sectors)

        # Separate dirs and files for cleaner output
        dirs = [f for f in files if f["is_directory"]]
        file_entries = [f for f in files if not f["is_directory"]]

        if verbose:
            print(f"  {len(dirs)} directories, {len(file_entries)} files", file=sys.stderr)

        # Bitmap
        bitmap = parse_bitmap(data, root["bm_pages"], total_sectors)
        if verbose:
            print(f"  Bitmap: {bitmap['free_blocks']} free, {bitmap['allocated_blocks']} allocated ({bitmap['percent_used']}% used)", file=sys.stderr)

        # Block usage
        block_usage = build_block_usage(
            total_sectors, root_block_num,
            root["bm_pages"], files,
            bitmap["_block_map"],
        )
        if verbose and block_usage["orphan_blocks"]:
            print(f"  Orphan blocks: {len(block_usage['orphan_blocks'])}", file=sys.stderr)

        # Clean internal fields before output
        for f in files:
            f.pop("_hash_table", None)
        bitmap.pop("_block_map", None)

        result["root_block"] = root
        result["filesystem"] = {
            "type": boot["fs_type"],
            "volume_name": root["volume_name"],
            "directories": len(dirs),
            "files": len(file_entries),
            "total_file_size": sum(f["size"] for f in file_entries),
        }
        result["files"] = file_entries
        result["directories"] = dirs
        result["bitmap"] = {k: v for k, v in bitmap.items() if not k.startswith("_")}
        result["block_usage"] = {k: v for k, v in block_usage.items() if not k.startswith("_")}

        # Check for non-zero free blocks (hidden data)
        free_with_data = []
        bmap = parse_bitmap(data, root["bm_pages"], total_sectors)["_block_map"]
        for i in range(total_sectors):
            if bmap[i] is True:  # free block
                block = read_block(data, i)
                if any(b != 0 for b in block):
                    # Check if it has interesting content
                    entropy = shannon_entropy(block)
                    strings = scan_ascii_strings(block, 6)
                    free_with_data.append({
                        "block": i,
                        "entropy": round(entropy, 2),
                        "strings": [s["text"] for s in strings[:5]],
                    })
        if free_with_data:
            result["free_blocks_with_data"] = free_with_data
            if verbose:
                print(f"  Free blocks with data: {len(free_with_data)}", file=sys.stderr)

        # Extract files if requested
        if extract_dir:
            os.makedirs(extract_dir, exist_ok=True)
            for entry in files:
                try:
                    extract_file(data, entry, extract_dir, is_ffs)
                except Exception as e:
                    print(f"  Error extracting {entry.get('full_path', '?')}: {e}", file=sys.stderr)
            if verbose:
                print(f"  Extracted to {extract_dir}", file=sys.stderr)

    # ---- Non-DOS ----
    else:
        result["non_dos"] = {
            "description": "Custom format disk (non-AmigaDOS)",
            "bootcode_present": boot["bootcode_has_code"],
        }
        include_tracks = True  # always scan tracks for non-DOS

    # ---- Track analysis (non-DOS always, DOS optionally) ----
    if include_tracks:
        if verbose:
            print("  Scanning tracks...", file=sys.stderr)
        tracks = []
        total_tracks = total_sectors // sectors_per_track
        for t in range(total_tracks):
            ta = analyze_track(data, t, sectors_per_track)
            # Only include non-empty tracks to keep output manageable
            if not ta["empty"] or ta["signatures"]:
                tracks.append(ta)
        result["track_analysis"] = {
            "total_tracks": total_tracks,
            "non_empty_tracks": len(tracks),
            "tracks": tracks,
        }

    # ---- Global signature scan ----
    if verbose:
        print("  Scanning for signatures...", file=sys.stderr)
    sigs = detect_signatures(data, total_sectors)

    # Summarize OS calls by LVO
    os_calls = [s for s in sigs if s["type"] == "OS_call"]
    other_sigs = [s for s in sigs if s["type"] != "OS_call"]

    # Deduplicate OS calls by LVO
    lvo_counts = {}
    for s in os_calls:
        lvo = s["lvo"]
        lvo_counts[lvo] = lvo_counts.get(lvo, 0) + 1

    result["signatures"] = other_sigs
    if lvo_counts:
        # Try to resolve LVO names from OS reference
        lvo_names = _load_lvo_names()
        resolved = {}
        for lvo, count in sorted(lvo_counts.items()):
            name = lvo_names.get(lvo, f"LVO_{-lvo}")
            resolved[str(lvo)] = {"count": count, "exec": name}
        result["os_calls_by_lvo"] = resolved

    return result


# ============================================================
# Output formatting
# ============================================================

def print_summary(result: dict):
    """Print human-readable summary."""
    info = result["disk_info"]
    boot = result["boot_block"]

    print(f"=== {info['path']} ===")
    print(f"  Size: {info['size']} bytes ({info['variant']})")
    print(f"  Sectors: {info['total_sectors']}")
    print(f"  Boot: {'DOS' if info['is_dos'] else 'Non-DOS'} "
          f"(checksum {'OK' if boot['checksum_valid'] else 'FAIL'})")

    if boot.get("fs_description"):
        print(f"  Filesystem: {boot['fs_description']}")
    if boot["bootcode_has_code"]:
        print(f"  Boot code: yes (entropy: {boot['bootcode_entropy']})")

    if "filesystem" in result:
        fs = result["filesystem"]
        print(f"\n  Volume: {fs['volume_name']}")
        print(f"  Files: {fs['files']}, Directories: {fs['directories']}")
        print(f"  Total file data: {fs['total_file_size']:,} bytes")

        bm = result.get("bitmap", {})
        if bm:
            print(f"  Blocks: {bm.get('allocated_blocks', '?')} allocated, "
                  f"{bm.get('free_blocks', '?')} free ({bm.get('percent_used', '?')}% used)")

        bu = result.get("block_usage", {})
        if bu.get("orphan_blocks"):
            print(f"  Orphan blocks: {len(bu['orphan_blocks'])}")

        fwd = result.get("free_blocks_with_data", [])
        if fwd:
            print(f"  Free blocks with data: {len(fwd)}")

    if "files" in result:
        print(f"\n  Files:")
        for f in sorted(result["files"], key=lambda x: x["full_path"]):
            print(f"    {f['full_path']:40s} {f['size']:>8,} bytes  {f['protection']}  {f['date']}")

    if "non_dos" in result:
        print(f"\n  Non-DOS disk")

    if "track_analysis" in result:
        ta = result["track_analysis"]
        print(f"\n  Tracks: {ta['total_tracks']} total, {ta['non_empty_tracks']} non-empty")
        code_tracks = [t for t in ta["tracks"] if t.get("has_code")]
        if code_tracks:
            print(f"  Tracks with M68K code: {len(code_tracks)}")

    sigs = result.get("signatures", [])
    if sigs:
        print(f"\n  Signatures:")
        for s in sigs[:30]:
            detail = ""
            if s["type"] == "IFF_FORM":
                detail = f" (FORM {s.get('form_type', '?')}, {s.get('form_size', '?')} bytes)"
            elif s["type"] == "HUNK_HEADER":
                detail = " (Amiga executable)"
            print(f"    Block {s['block']:4d} +{s['offset_in_block']:3d}: {s['type']}{detail}")

    os_calls = result.get("os_calls_by_lvo", {})
    if os_calls:
        print(f"\n  OS library calls (JSR -xxx(A6)):")
        for lvo, info in list(os_calls.items())[:20]:
            if isinstance(info, dict):
                name = info.get("exec", "?")
                count = info.get("count", "?")
                print(f"    LVO {lvo:>5s}: {name:30s} ({count} call(s))")
            else:
                print(f"    LVO {lvo}: {info} call(s)")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Analyze Amiga ADF disk images"
    )
    parser.add_argument("adf_file", help="Path to ADF file")
    parser.add_argument("-o", "--output", choices=["json", "summary"],
                        default="summary", help="Output format (default: summary)")
    parser.add_argument("--outfile", help="Write JSON output to file")
    parser.add_argument("--extract", metavar="DIR",
                        help="Extract files to directory (DOS disks only)")
    parser.add_argument("--tracks", action="store_true",
                        help="Include per-track analysis (always on for non-DOS)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print progress to stderr")
    args = parser.parse_args()

    if not os.path.exists(args.adf_file):
        print(f"Error: {args.adf_file} not found", file=sys.stderr)
        sys.exit(1)

    result = analyze_adf(
        args.adf_file,
        extract_dir=args.extract,
        include_tracks=args.tracks,
        verbose=args.verbose,
    )

    if args.output == "json" or args.outfile:
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        if args.outfile:
            with open(args.outfile, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"Wrote {args.outfile}", file=sys.stderr)
        else:
            print(json_str)
    else:
        print_summary(result)


if __name__ == "__main__":
    main()
