"""Name subroutine entities from available signals.

Signals used (in priority order):
1. OS call patterns — subroutines calling specific library functions
2. String references — LEA d(PC),An pointing to readable strings
3. Call graph position — entry point, leaf functions

String detection uses KB ea_mode_encoding.pcdisp and opword_bytes.
OS call naming uses the runtime OS KB function names.
No hardcoded mnemonic names.

Usage:
    from name_entities import name_subroutines
    name_subroutines(entities, blocks, code, os_calls, result)
"""

import struct
import sys
import re

from .m68k_executor import BasicBlock, _extract_mnemonic
from .os_calls import load_os_kb
from .kb_util import KB, xf, find_containing_sub
from .runtime_kb import load_naming_runtime_kb


def find_string_refs(blocks: dict[int, BasicBlock],
                     code: bytes) -> dict[int, list[tuple[int, str]]]:
    """Find string references in each subroutine's blocks.

    Scans for LEA d(PC),An where the target address contains a readable
    ASCII string. PC-displacement EA mode detected from KB.

    Returns {block_addr: [(string_addr, string_text), ...]}.
    """
    kb = KB()
    pcdisp = kb.ea_enc["pcdisp"]

    lea_kb = kb.find("lea")
    if lea_kb is None:
        raise KeyError("LEA not found in M68K KB")
    ea_spec = kb.ea_field_spec(lea_kb)
    if ea_spec is None:
        raise KeyError("LEA encoding lacks MODE/REGISTER fields")
    mode_spec, reg_spec = ea_spec

    refs_by_block = {}

    for block_addr in sorted(blocks):
        block = blocks[block_addr]
        refs = []
        for inst in block.instructions:
            ikb = kb.instruction_kb(inst)
            if ikb.get("operation_class") != "load_effective_address":
                continue
            if len(inst.raw) < kb.opword_bytes + 2:
                continue

            opcode = struct.unpack_from(">H", inst.raw, 0)[0]
            src_mode = xf(opcode, mode_spec)
            src_reg = xf(opcode, reg_spec)

            if src_mode != pcdisp[0] or src_reg != pcdisp[1]:
                continue

            disp = struct.unpack_from(">h", inst.raw, kb.opword_bytes)[0]
            str_addr = inst.offset + kb.opword_bytes + disp
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


_NAMING_RULES = None

def _load_naming_rules() -> dict:
    """Load naming rules from KB. Cached after first call."""
    global _NAMING_RULES
    if _NAMING_RULES is not None:
        return _NAMING_RULES
    _NAMING_RULES = load_naming_runtime_kb()
    return _NAMING_RULES


def _os_calls_to_name(os_calls: list[str]) -> str | None:
    """Suggest a name from a subroutine's OS call list.

    Naming rules loaded from the runtime naming KB.
    """
    if not os_calls:
        return None

    rules = _load_naming_rules()

    # Extract just function names (strip library prefix)
    funcs = set()
    for call in os_calls:
        parts = call.split("/")
        if len(parts) == 2:
            funcs.add(parts[1])

    # Match against patterns from KB
    for pattern in rules["patterns"]:
        required = set(pattern["functions"])
        if pattern.get("partial"):
            # At least one required function must be present
            if required & funcs:
                return pattern["name"]
        else:
            # Exact match or superset
            if required <= funcs and (len(required) > 1 or funcs == required):
                return pattern["name"]

    # Generic: use the most distinctive function name
    trivial = set(rules["trivial_functions"])
    prefix = rules["generic_prefix"]
    distinctive = funcs - trivial
    if distinctive:
        func = sorted(distinctive)[0]
        return prefix + re.sub(r'[^a-z0-9]+', '_', func.lower()).strip('_')

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

    # Build sorted sub list for binary search (with int keys)
    sorted_sub_list = sorted(
        [{"addr": k, "end": int(entity_by_addr[k]["end"], 16)}
         for k in entity_by_addr],
        key=lambda s: s["addr"])

    # Aggregate string refs by subroutine
    sub_strings: dict[int, list[str]] = {}
    for block_addr, refs in string_refs.items():
        sub_addr = find_containing_sub(block_addr, sorted_sub_list)
        if sub_addr is not None:
            if sub_addr not in sub_strings:
                sub_strings[sub_addr] = []
            for _, text in refs:
                sub_strings[sub_addr].append(text)

    # Aggregate OS calls by subroutine (from lib_calls)
    sub_os_calls: dict[int, list[str]] = {}
    for call in lib_calls:
        sub_addr = find_containing_sub(call["addr"], sorted_sub_list)
        if sub_addr is not None:
            if sub_addr not in sub_os_calls:
                sub_os_calls[sub_addr] = []
            lib = call["library"]
            func = call["function"]
            sub_os_calls[sub_addr].append(f"{lib}/{func}")

    # Detect dispatch subroutines: subs containing per-caller dispatch
    # instructions (identified by the "dispatch" field in lib_calls).
    dispatch_libs: dict[int, set] = {}
    for call in lib_calls:
        disp_addr = call.get("dispatch")
        if disp_addr is None:
            continue
        sub_addr = find_containing_sub(disp_addr, sorted_sub_list)
        if sub_addr is not None:
            if sub_addr not in dispatch_libs:
                dispatch_libs[sub_addr] = set()
            lib = call.get("library")
            if lib and lib != "unknown":
                dispatch_libs[sub_addr].add(lib)

    named = 0
    used_names = set()

    for addr in sorted(entity_by_addr.keys()):
        ent = entity_by_addr[addr]
        if ent.get("name"):
            used_names.add(ent["name"])
            continue

        name = None

        # Priority 1: OS call pattern
        os_calls = sub_os_calls.get(addr)
        if os_calls:
            name = _os_calls_to_name(os_calls)

        # Priority 1.5: dispatch subroutine
        if name is None and addr in dispatch_libs:
            libs = dispatch_libs[addr]
            if len(libs) == 1:
                base = next(iter(libs)).rsplit(".", 1)[0]
                name = re.sub(r'[^a-z0-9]+', '_', base.lower()) + "_dispatch"
            elif libs:
                name = "lib_dispatch"

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
