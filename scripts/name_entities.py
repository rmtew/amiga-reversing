"""Name subroutine entities from available signals.

Signals used (in priority order):
1. OS call patterns — subroutines calling specific library functions
2. String references — LEA d(PC),An pointing to readable strings
3. Call graph position — entry point, leaf functions

String detection uses KB ea_mode_encoding.pcdisp and opword_bytes.
OS call naming uses amiga_os_reference.json function names.
No hardcoded mnemonic names.

Usage:
    from name_entities import name_subroutines
    name_subroutines(entities, blocks, code, os_calls, result)
"""

import struct
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m68k_executor import (BasicBlock, _extract_mnemonic, _load_kb,
                            _find_kb_entry)
from os_calls import load_os_kb


def find_string_refs(blocks: dict[int, BasicBlock],
                     code: bytes) -> dict[int, list[tuple[int, str]]]:
    """Find string references in each subroutine's blocks.

    Scans for LEA d(PC),An where the target address contains a readable
    ASCII string. PC-displacement EA mode detected from KB.

    Returns {block_addr: [(string_addr, string_text), ...]}.
    """
    kb_by_name, _, meta = _load_kb()
    opword_bytes = meta["opword_bytes"]
    ea_enc = meta["ea_mode_encoding"]
    cc_defs = meta.get("cc_test_definitions", {})
    cc_aliases = meta.get("cc_aliases", {})

    pcdisp = ea_enc.get("pcdisp")
    if pcdisp is None:
        raise KeyError("ea_mode_encoding.pcdisp missing from M68K KB")

    # Get LEA's encoding to extract EA field positions
    lea_kb = _find_kb_entry(kb_by_name, "lea", cc_defs, cc_aliases)
    if lea_kb is None:
        raise KeyError("LEA not found in M68K KB")

    # LEA source EA: MODE at bits 5-3, REGISTER at bits 2-0
    encodings = lea_kb.get("encodings", [])
    if not encodings:
        raise KeyError("LEA has no encodings in KB")
    fields = encodings[0].get("fields", [])
    mode_field = reg_field = None
    for f in fields:
        if f["name"] == "MODE":
            mode_field = f
        elif f["name"] == "REGISTER" and f["bit_hi"] <= 5:
            reg_field = f
    if mode_field is None or reg_field is None:
        raise KeyError("LEA encoding lacks MODE/REGISTER fields")

    mode_spec = (mode_field["bit_hi"], mode_field["bit_lo"],
                 mode_field["bit_hi"] - mode_field["bit_lo"] + 1)
    reg_spec = (reg_field["bit_hi"], reg_field["bit_lo"],
                reg_field["bit_hi"] - reg_field["bit_lo"] + 1)

    def _xf(opcode, spec):
        return (opcode >> spec[1]) & ((1 << spec[2]) - 1)

    refs_by_block = {}

    for block_addr in sorted(blocks):
        block = blocks[block_addr]
        refs = []
        for inst in block.instructions:
            mn = _extract_mnemonic(inst.text)
            ikb = _find_kb_entry(kb_by_name, mn, cc_defs, cc_aliases)
            if ikb is None:
                continue
            # Check this is LEA by KB operation text (same detection as executor)
            if ikb.get("operation") != "< ea > \u2192 An":
                continue
            if len(inst.raw) < opword_bytes + 2:
                continue

            opcode = struct.unpack_from(">H", inst.raw, 0)[0]
            src_mode = _xf(opcode, mode_spec)
            src_reg = _xf(opcode, reg_spec)

            if src_mode != pcdisp[0] or src_reg != pcdisp[1]:
                continue

            disp = struct.unpack_from(">h", inst.raw, opword_bytes)[0]
            str_addr = inst.offset + opword_bytes + disp
            if str_addr < 0 or str_addr >= len(code):
                continue

            # Read null-terminated ASCII
            chars = []
            for i in range(128):
                if str_addr + i >= len(code):
                    break
                b = code[str_addr + i]
                if b == 0:
                    break
                if 32 <= b < 127:
                    chars.append(chr(b))
                else:
                    chars = []
                    break

            if len(chars) >= 3:
                refs.append((str_addr, "".join(chars)))

        if refs:
            refs_by_block[block_addr] = refs

    return refs_by_block


def _string_to_name(s: str, os_lib_names: set[str] | None = None) -> str:
    """Convert a string reference to a subroutine name suggestion.

    If the string matches a known OS library/device/resource name
    (from the OS KB), prefix with 'open_'. Otherwise sanitize as
    a generic identifier.
    """
    s = s.strip()

    # Check against known OS library names from KB
    if os_lib_names and s in os_lib_names:
        # Strip the suffix (everything after the last dot)
        base = s.rsplit(".", 1)[0]
        return "open_" + re.sub(r'[^a-z0-9]+', '_', base.lower()).strip('_')

    # Convert to identifier
    name = s.lower()
    name = re.sub(r'[^a-z0-9]+', '_', name)
    name = name.strip('_')
    if len(name) > 40:
        name = name[:40].rstrip('_')
    return name


def _os_calls_to_name(os_calls: list[str]) -> str | None:
    """Suggest a name from a subroutine's OS call list."""
    if not os_calls:
        return None

    # Extract just function names (strip library prefix)
    funcs = set()
    for call in os_calls:
        parts = call.split("/")
        if len(parts) == 2:
            funcs.add(parts[1])

    # Common patterns
    if "OpenLibrary" in funcs and "AllocMem" in funcs:
        return "init_app"
    if "CloseLibrary" in funcs and "FreeMem" in funcs:
        return "cleanup_app"
    if funcs == {"AllocMem"}:
        return "alloc_memory"
    if funcs == {"FreeMem"}:
        return "free_memory"
    if funcs == {"AllocMem", "FreeMem"}:
        return "manage_memory"
    if funcs == {"SetSignal"}:
        return "check_signals"
    if funcs == {"AvailMem"}:
        return "check_memory"
    if "OpenDevice" in funcs:
        return "open_device"

    # Generic: use the most distinctive function name
    # Prefer non-trivial functions
    trivial = {"AllocMem", "FreeMem", "SetSignal"}
    distinctive = funcs - trivial
    if distinctive:
        func = sorted(distinctive)[0]
        return "call_" + re.sub(r'[^a-z0-9]+', '_', func.lower()).strip('_')

    return None


def name_subroutines(entities: list[dict],
                     blocks: dict[int, BasicBlock],
                     code: bytes,
                     lib_calls: list[dict]) -> int:
    """Assign names to unnamed code entities.

    Modifies entities in place. Returns count of entities named.

    Naming priority:
    1. OS call patterns
    2. String references (most distinctive string)
    3. Entry point / call graph position
    """
    # Known OS library/device/resource names from KB
    os_kb = load_os_kb()
    os_lib_names = set(os_kb["libraries"].keys())

    # Build block→subroutine mapping
    entity_by_addr = {}
    for ent in entities:
        if ent.get("type") != "code":
            continue
        addr = int(ent["addr"], 16)
        entity_by_addr[addr] = ent

    # Collect string refs per subroutine
    string_refs = find_string_refs(blocks, code)

    # Map block addresses to their containing subroutine
    sorted_subs = sorted(entity_by_addr.keys())

    def _find_sub(block_addr):
        """Find containing subroutine for a block address."""
        lo, hi = 0, len(sorted_subs) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            s = sorted_subs[mid]
            ent = entity_by_addr[s]
            end = int(ent["end"], 16)
            if block_addr < s:
                hi = mid - 1
            elif block_addr >= end:
                lo = mid + 1
            else:
                return s
        return None

    # Aggregate string refs by subroutine
    sub_strings: dict[int, list[str]] = {}
    for block_addr, refs in string_refs.items():
        sub_addr = _find_sub(block_addr)
        if sub_addr is not None:
            if sub_addr not in sub_strings:
                sub_strings[sub_addr] = []
            for _, text in refs:
                sub_strings[sub_addr].append(text)

    # Aggregate OS calls by subroutine (from lib_calls)
    sub_os_calls: dict[int, list[str]] = {}
    for call in lib_calls:
        sub_addr = _find_sub(call["addr"])
        if sub_addr is not None:
            if sub_addr not in sub_os_calls:
                sub_os_calls[sub_addr] = []
            lib = call["library"]
            func = call["function"]
            sub_os_calls[sub_addr].append(f"{lib}/{func}")

    named = 0
    used_names = set()

    for addr in sorted_subs:
        ent = entity_by_addr[addr]
        if ent.get("name"):
            used_names.add(ent["name"])
            continue

        name = None

        # Priority 1: OS call pattern
        os_calls = sub_os_calls.get(addr)
        if os_calls:
            name = _os_calls_to_name(os_calls)

        # Priority 2: string reference
        if name is None and addr in sub_strings:
            strings = sub_strings[addr]
            # Filter: string must be descriptive (>= 6 chars, contains
            # a space or looks like a filename/identifier)
            good = [s for s in strings
                    if len(s) >= 6 and (
                        " " in s or "." in s or "_" in s
                        or s[0].isupper())]
            if good:
                best = max(good, key=len)
                name = _string_to_name(best, os_lib_names)

        # Priority 3: entry point
        if name is None and addr == 0:
            name = "entry_point"

        if name and name not in used_names:
            ent["name"] = name
            ent["status"] = "named"
            used_names.add(name)
            named += 1
        elif name:
            # Deduplicate with address suffix
            deduped = f"{name}_{addr:04x}"
            ent["name"] = deduped
            ent["status"] = "named"
            used_names.add(deduped)
            named += 1

    return named
