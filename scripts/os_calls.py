"""Amiga OS library call identification.

Identifies OS library calls in analyzed M68K code by matching the
ExecBase load pattern and LVO dispatch pattern against the OS KB.

All identification is data-driven from:
- amiga_os_reference.json: exec_base_addr, lvo_index, calling_convention
- m68k_instructions.json: ea_mode_encoding for addressing mode detection

Usage:
    from os_calls import load_os_kb, identify_library_calls
    os_kb = load_os_kb()
    calls = identify_library_calls(blocks, code, os_kb)
"""

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m68k_executor import BasicBlock, _extract_mnemonic, _extract_branch_target
from kb_util import KB, xf, parse_reg_name, read_string_at


_OS_KB_CACHE = None



def load_os_kb() -> dict:
    """Load the Amiga OS reference KB. Cached after first call."""
    global _OS_KB_CACHE
    if _OS_KB_CACHE is not None:
        return _OS_KB_CACHE
    path = Path(__file__).resolve().parent.parent / "knowledge" / "amiga_os_reference.json"
    with open(path, encoding="utf-8") as f:
        _OS_KB_CACHE = json.load(f)
    return _OS_KB_CACHE


# Sentinel addresses for abstract memory regions.
# These must not overlap with real hunk addresses (code is 0..64K range).
# SP sentinel: top of a virtual stack region.
# Memory allocation sentinels: auto-incrementing base addresses.
_SENTINEL_SP = 0x7F000000
_SENTINEL_ALLOC_BASE = 0x80000000
_SENTINEL_ALLOC_STEP = 0x00100000  # 1MB per allocation


def get_platform_config() -> dict:
    """Build platform config dict from OS KB for the executor.

    Returns dict with:
        scratch_regs: list of (mode, num) tuples to invalidate after calls
        exec_base_addr: int (absolute address of ExecBase pointer)
        initial_sp: int (sentinel SP for abstract stack tracking)
    """
    os_kb = load_os_kb()
    meta = os_kb["_meta"]
    cc = meta["calling_convention"]

    scratch = [parse_reg_name(r) for r in cc["scratch_regs"]]

    base_reg_name = cc["base_reg"].upper()
    if not base_reg_name.startswith("A"):
        raise ValueError(f"calling_convention.base_reg must be An, got {base_reg_name}")
    base_reg_num = int(base_reg_name[1])

    exec_lib = meta["exec_base_addr"].get("library")
    if exec_lib is None:
        raise KeyError("exec_base_addr.library missing from OS KB")

    return {
        "scratch_regs": scratch,
        "exec_base_addr": meta["exec_base_addr"]["address"],
        "exec_base_library": exec_lib,
        "exec_base_tag": {"library_base": exec_lib},
        "base_reg": cc["base_reg"],
        "return_reg": cc["return_reg"],
        "initial_sp": _SENTINEL_SP,
        "_base_reg_num": base_reg_num,
        "_next_alloc_sentinel": _SENTINEL_ALLOC_BASE,
        "_os_call_resolver": lambda offset, lvo, lib, cpu, code, platform=None:
            resolve_call_effects(offset, lvo, lib, cpu, code,
                                 platform=platform),
    }


def resolve_call_effects(inst_offset: int, lvo: int, a6_lib: str | None,
                         cpu_state, code: bytes,
                         os_kb: dict | None = None,
                         platform: dict | None = None) -> dict | None:
    """Determine the effects of a library call on register state.

    Handles three KB fields, in priority order:
    - `returns_base` (OpenLibrary etc.): tags result register as library base
    - `returns_memory` (AllocMem etc.): assigns sentinel concrete value to
      result register, enabling base-relative memory tracking
    - `output` (all typed functions): tags result register with OS type

    Returns dict with one of:
        {"base_reg": "D0", "tag": {"library_base": "dos.library"}}
        {"result_reg": "D0", "concrete": 0x80000000}
        {"output_reg": "D0", "output_type": {"os_type": "void *", ...}}
    or None if no effect can be determined.
    """
    if os_kb is None:
        os_kb = load_os_kb()

    if a6_lib is None:
        return None

    lib_data = os_kb["libraries"].get(a6_lib)
    if lib_data is None:
        return None

    lvo_index = lib_data.get("lvo_index", {})
    func_name = lvo_index.get(str(lvo))
    if func_name is None:
        return None

    func = lib_data["functions"].get(func_name, {})

    # Check returns_base first (OpenLibrary, OpenResource)
    rb = func.get("returns_base")
    if rb:
        mode, num = parse_reg_name(rb["name_reg"])
        reg_val = cpu_state.get_reg(mode, num)
        if reg_val.is_known:
            lib_name = read_string_at(code, reg_val.concrete)
            if lib_name:
                output = func.get("output", {})
                tag = {"library_base": lib_name}
                if output.get("type"):
                    tag["os_type"] = output["type"]
                return {
                    "base_reg": rb["base_reg"],
                    "tag": tag,
                }

    # Check returns_memory (AllocMem, AllocVec, etc.)
    rm = func.get("returns_memory")
    if rm and platform:
        sentinel = platform.get("_next_alloc_sentinel")
        if sentinel is not None:
            # Advance sentinel for next allocation
            platform["_next_alloc_sentinel"] = \
                sentinel + _SENTINEL_ALLOC_STEP
            return {
                "result_reg": rm["result_reg"],
                "concrete": sentinel,
            }

    # Generic output type tag from KB
    output = func.get("output")
    if output and output.get("reg") and output.get("type"):
        return {
            "output_reg": output["reg"],
            "output_type": {
                "os_type": output["type"],
                "os_result": output.get("name"),
                "call": func_name,
                "library": a6_lib,
            },
        }

    return None


def _build_lvo_lookup(os_kb: dict) -> dict:
    """Build combined LVO lookup: {(library_name, lvo_offset_int): function_dict}.

    Also builds reverse: {lvo_offset_int: [(library_name, func_name, func_dict)]}
    for when we don't know which library base is in A6.
    """
    by_lib_lvo = {}
    by_lvo = {}
    for lib_name, lib_data in os_kb["libraries"].items():
        for lvo_str, func_name in lib_data.get("lvo_index", {}).items():
            lvo = int(lvo_str)
            func = lib_data["functions"].get(func_name, {})
            by_lib_lvo[(lib_name, lvo)] = {
                "library": lib_name,
                "function": func_name,
                "lvo": lvo,
                **{k: v for k, v in func.items() if k in (
                    "inputs", "output", "no_return", "since")},
            }
            if lvo not in by_lvo:
                by_lvo[lvo] = []
            by_lvo[lvo].append((lib_name, func_name, func))
    return {"by_lib_lvo": by_lib_lvo, "by_lvo": by_lvo}


def identify_library_calls(blocks: dict[int, BasicBlock],
                           code: bytes,
                           os_kb: dict | None = None,
                           exit_states: dict | None = None,
                           ) -> list[dict]:
    """Identify OS library calls in analyzed code.

    Scans for the Amiga library call pattern:
        MOVEA.L ($0004).W,A6    ; load ExecBase
        JSR     -offset(A6)     ; call library function via LVO

    If exit_states is provided (from propagation with platform config),
    uses library_base tags on A6 to resolve calls through non-exec
    library bases (e.g. after OpenLibrary stores a dos.library base).

    EA field positions read from KB instruction encodings (not hardcoded).
    ExecBase address and library base register from OS KB.

    Returns list of dicts:
        {"addr": int, "block": int, "library": str, "function": str,
         "lvo": int, "no_return": bool}
    """
    if os_kb is None:
        os_kb = load_os_kb()

    kb = KB()
    os_meta = os_kb["_meta"]
    exec_base_addr = os_meta["exec_base_addr"]["address"]
    exec_lib_name = os_meta["exec_base_addr"]["library"]
    base_mode, base_reg_num = parse_reg_name(
        os_meta["calling_convention"]["base_reg"])
    if base_mode != "an":
        raise ValueError(
            f"calling_convention.base_reg must be An, got {base_mode}")

    lvo_lookup = _build_lvo_lookup(os_kb)

    absw_enc = kb.ea_enc["absw"]
    disp_enc = kb.ea_enc["disp"]
    addr_mask = (1 << (kb.meta["size_byte_count"]["l"] * 8)) - 1

    movea_kb = kb.find("movea")
    jsr_kb = kb.find("jsr")
    if movea_kb is None:
        raise KeyError("MOVEA not found in M68K KB")
    if jsr_kb is None:
        raise KeyError("JSR not found in M68K KB")

    movea_ea_spec = kb.ea_field_spec(movea_kb)
    movea_dst_spec = kb.dst_reg_field(movea_kb)
    jsr_ea_spec = kb.ea_field_spec(jsr_kb)
    if movea_ea_spec is None:
        raise KeyError("MOVEA encoding lacks MODE/REGISTER EA fields")
    if movea_dst_spec is None:
        raise KeyError("MOVEA encoding lacks destination REGISTER field")
    if jsr_ea_spec is None:
        raise KeyError("JSR encoding lacks MODE/REGISTER EA fields")

    movea_mode_f, movea_reg_f = movea_ea_spec
    jsr_mode_f, jsr_reg_f = jsr_ea_spec

    results = []

    for block_addr in sorted(blocks):
        block = blocks[block_addr]
        if not block.instructions:
            continue

        # Determine library identity for A6 in this block.
        # Priority: propagated tag (cross-block) > intra-block ExecBase detection.
        a6_lib = None

        # Check propagated state for A6's library_base tag
        if exit_states and block_addr in exit_states:
            cpu, _mem = exit_states[block_addr]
            a6_val = cpu.a[base_reg_num]
            if a6_val.tag and "library_base" in a6_val.tag:
                a6_lib = a6_val.tag["library_base"]

        for inst in block.instructions:
            mn = _extract_mnemonic(inst.text)
            ikb = kb.find(mn)
            if ikb is None:
                continue

            flow = ikb.get("pc_effects", {}).get("flow", {})

            # Detect ExecBase load: MOVEA.L ($0004).W,A6
            # Must be specifically MOVEA (source_sign_extend distinguishes
            # MOVEA from MOVE in the KB).
            if (ikb.get("operation_type") == "move"
                    and ikb.get("source_sign_extend")
                    and len(inst.raw) >= kb.opword_bytes + 2):
                opcode = struct.unpack_from(">H", inst.raw, 0)[0]
                src_mode = xf(opcode, movea_mode_f)
                src_reg = xf(opcode, movea_reg_f)

                if src_mode == absw_enc[0] and src_reg == absw_enc[1]:
                    addr_val = struct.unpack_from(
                        ">h", inst.raw, kb.opword_bytes)[0]
                    addr_val &= addr_mask

                    dst_reg = xf(opcode, movea_dst_spec)
                    if addr_val == exec_base_addr and dst_reg == base_reg_num:
                        a6_lib = exec_lib_name

            # Detect library call: JSR d(An) where An == base_reg
            if flow.get("type") == "call":
                target = _extract_branch_target(inst, inst.offset)
                if target is not None:
                    continue  # resolved — not a library call

                if len(inst.raw) < kb.opword_bytes + 2:
                    continue
                opcode = struct.unpack_from(">H", inst.raw, 0)[0]
                ea_mode = xf(opcode, jsr_mode_f)
                ea_reg = xf(opcode, jsr_reg_f)

                if ea_mode != disp_enc[0] or ea_reg != base_reg_num:
                    continue  # not d(A6)

                disp = struct.unpack_from(
                    ">h", inst.raw, kb.opword_bytes)[0]

                call_info = {
                    "addr": inst.offset,
                    "block": block_addr,
                    "lvo": disp,
                }

                if a6_lib:
                    # Known library — look up in that library's LVO index
                    key = (a6_lib, disp)
                    if key in lvo_lookup["by_lib_lvo"]:
                        match = lvo_lookup["by_lib_lvo"][key]
                        call_info["library"] = match["library"]
                        call_info["function"] = match["function"]
                        if match.get("no_return"):
                            call_info["no_return"] = True
                    else:
                        call_info["library"] = a6_lib
                        call_info["function"] = f"LVO_{-disp}"
                else:
                    # Unknown library — try ambiguous resolution
                    candidates = lvo_lookup["by_lvo"].get(disp, [])
                    if len(candidates) == 1:
                        clib, cfunc, cdata = candidates[0]
                        call_info["library"] = clib
                        call_info["function"] = cfunc
                        if cdata.get("no_return"):
                            call_info["no_return"] = True
                    elif candidates:
                        call_info["library"] = "unknown"
                        call_info["function"] = f"LVO_{-disp}"
                        call_info["candidates"] = [
                            f"{ln}/{fn}" for ln, fn, _ in candidates
                        ]
                    else:
                        call_info["library"] = "unknown"
                        call_info["function"] = f"LVO_{-disp}"

                results.append(call_info)

    return results
