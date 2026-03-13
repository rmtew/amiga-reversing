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

from m68k_executor import (BasicBlock, _extract_mnemonic, _load_kb,
                            _find_kb_entry, _extract_branch_target)
from jump_tables import _build_ea_field_spec, _xf


_OS_KB_CACHE = None


def _build_dst_reg_field(inst_kb: dict) -> tuple | None:
    """Extract the destination REGISTER field from KB encoding (bits 11-9 for MOVEA).

    For instructions with two REGISTER fields (like MOVEA), the destination
    is the one at higher bit positions (bits 11-9), distinct from the source
    EA REGISTER at bits 2-0.

    Returns (bit_hi, bit_lo, width) or None.
    """
    encodings = inst_kb.get("encodings", [])
    if not encodings:
        return None
    fields = encodings[0].get("fields", [])
    # Find REGISTER fields; the destination is the one with higher bit_lo
    reg_fields = [f for f in fields if f["name"] == "REGISTER"]
    if len(reg_fields) < 2:
        return None  # single REGISTER field — not a src+dst instruction
    # Sort by bit position descending; highest = destination
    reg_fields.sort(key=lambda f: f["bit_lo"], reverse=True)
    dst = reg_fields[0]
    return (dst["bit_hi"], dst["bit_lo"], dst["bit_hi"] - dst["bit_lo"] + 1)


def load_os_kb() -> dict:
    """Load the Amiga OS reference KB. Cached after first call."""
    global _OS_KB_CACHE
    if _OS_KB_CACHE is not None:
        return _OS_KB_CACHE
    path = Path(__file__).resolve().parent.parent / "knowledge" / "amiga_os_reference.json"
    with open(path, encoding="utf-8") as f:
        _OS_KB_CACHE = json.load(f)
    return _OS_KB_CACHE


def get_platform_config() -> dict:
    """Build platform config dict from OS KB for the executor.

    Returns dict with:
        scratch_regs: list of (mode, num) tuples to invalidate after calls
        exec_base_addr: int (absolute address of ExecBase pointer)
    """
    os_kb = load_os_kb()
    meta = os_kb["_meta"]
    cc = meta["calling_convention"]

    # Parse register names like "D0" -> ("dn", 0), "A1" -> ("an", 1)
    scratch = []
    for reg_name in cc["scratch_regs"]:
        reg_name = reg_name.upper()
        if reg_name[0] == "D":
            scratch.append(("dn", int(reg_name[1])))
        elif reg_name[0] == "A":
            scratch.append(("an", int(reg_name[1])))
        else:
            raise ValueError(f"Unknown register in calling_convention.scratch_regs: {reg_name}")

    return {
        "scratch_regs": scratch,
        "exec_base_addr": meta["exec_base_addr"]["address"],
        "base_reg": cc["base_reg"],
        "return_reg": cc["return_reg"],
    }


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
                           ) -> list[dict]:
    """Identify OS library calls in analyzed code.

    Scans for the Amiga library call pattern:
        MOVEA.L ($0004).W,A6    ; load ExecBase
        JSR     -offset(A6)     ; call library function via LVO

    EA field positions read from KB instruction encodings (not hardcoded).
    ExecBase address and library base register from OS KB.

    Returns list of dicts:
        {"addr": int, "block": int, "library": str, "function": str,
         "lvo": int, "no_return": bool}
    """
    if os_kb is None:
        os_kb = load_os_kb()

    m68k_kb, _, m68k_meta = _load_kb()
    ea_enc = m68k_meta["ea_mode_encoding"]
    opword_bytes = m68k_meta["opword_bytes"]
    cc_defs = m68k_meta.get("cc_test_definitions", {})
    cc_aliases = m68k_meta.get("cc_aliases", {})

    os_meta = os_kb["_meta"]
    exec_base_addr = os_meta["exec_base_addr"]["address"]
    exec_lib_name = os_meta["exec_base_addr"].get("library", "exec.library")
    base_reg_name = os_meta["calling_convention"]["base_reg"]
    if not base_reg_name.upper().startswith("A"):
        raise ValueError(
            f"calling_convention.base_reg must be An, got {base_reg_name}")
    base_reg_num = int(base_reg_name[1])

    lvo_lookup = _build_lvo_lookup(os_kb)

    # EA mode encodings from KB
    absw_enc = ea_enc.get("absw")
    disp_enc = ea_enc.get("disp")
    if absw_enc is None:
        raise KeyError("ea_mode_encoding.absw missing from M68K KB")
    if disp_enc is None:
        raise KeyError("ea_mode_encoding.disp missing from M68K KB")

    # Pre-resolve KB entries and encoding field specs for MOVEA and JSR
    movea_kb = _find_kb_entry(m68k_kb, "movea", cc_defs, cc_aliases)
    jsr_kb = _find_kb_entry(m68k_kb, "jsr", cc_defs, cc_aliases)
    if movea_kb is None:
        raise KeyError("MOVEA not found in M68K KB")
    if jsr_kb is None:
        raise KeyError("JSR not found in M68K KB")

    movea_ea_spec = _build_ea_field_spec(movea_kb)
    movea_dst_spec = _build_dst_reg_field(movea_kb)
    jsr_ea_spec = _build_ea_field_spec(jsr_kb)
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

        # Track whether base_reg was loaded from ExecBase within this block
        a6_is_exec = False

        for inst in block.instructions:
            mn = _extract_mnemonic(inst.text)
            ikb = _find_kb_entry(m68k_kb, mn, cc_defs, cc_aliases)
            if ikb is None:
                continue

            flow = ikb.get("pc_effects", {}).get("flow", {})

            # Detect ExecBase load: MOVEA.L ($0004).W,A6
            # Must be specifically MOVEA (source_sign_extend distinguishes
            # MOVEA from MOVE in the KB).
            if (ikb.get("operation_type") == "move"
                    and ikb.get("source_sign_extend")
                    and len(inst.raw) >= opword_bytes + 2):
                opcode = struct.unpack_from(">H", inst.raw, 0)[0]
                src_mode = _xf(opcode, movea_mode_f)
                src_reg = _xf(opcode, movea_reg_f)

                if src_mode == absw_enc[0] and src_reg == absw_enc[1]:
                    addr_val = struct.unpack_from(
                        ">h", inst.raw, opword_bytes)[0]
                    addr_val &= 0xFFFFFFFF

                    dst_reg = _xf(opcode, movea_dst_spec)
                    if addr_val == exec_base_addr and dst_reg == base_reg_num:
                        a6_is_exec = True

            # Detect library call: JSR d(An) where An == base_reg
            if flow.get("type") == "call":
                target = _extract_branch_target(inst, inst.offset)
                if target is not None:
                    continue  # resolved — not a library call

                if len(inst.raw) < opword_bytes + 2:
                    continue
                opcode = struct.unpack_from(">H", inst.raw, 0)[0]
                ea_mode = _xf(opcode, jsr_mode_f)
                ea_reg = _xf(opcode, jsr_reg_f)

                if ea_mode != disp_enc[0] or ea_reg != base_reg_num:
                    continue  # not d(A6)

                disp = struct.unpack_from(
                    ">h", inst.raw, opword_bytes)[0]

                call_info = {
                    "addr": inst.offset,
                    "block": block_addr,
                    "lvo": disp,
                }

                if a6_is_exec:
                    key = (exec_lib_name, disp)
                    if key in lvo_lookup["by_lib_lvo"]:
                        match = lvo_lookup["by_lib_lvo"][key]
                        call_info["library"] = match["library"]
                        call_info["function"] = match["function"]
                        if match.get("no_return"):
                            call_info["no_return"] = True
                    else:
                        call_info["library"] = exec_lib_name
                        call_info["function"] = f"LVO_{-disp}"
                else:
                    candidates = lvo_lookup["by_lvo"].get(disp, [])
                    if len(candidates) == 1:
                        lib_name, func_name, func = candidates[0]
                        call_info["library"] = lib_name
                        call_info["function"] = func_name
                        if func.get("no_return"):
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

        # A6 state doesn't propagate across blocks (conservative)

    return results
