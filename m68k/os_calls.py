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

from .m68k_executor import BasicBlock, _extract_mnemonic, _extract_branch_target
from .kb_util import (KB, xf, parse_reg_name, read_string_at,
                      decode_destination)
from .m68k_executor import _extract_size


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

    lvo_index = lib_data["lvo_index"]
    func_name = lvo_index.get(str(lvo))
    if func_name is None:
        return None

    func = lib_data["functions"][func_name]

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


# ── Return value store tracing ───────────────────────────────────────

def trace_return_stores(blocks: dict[int, BasicBlock],
                        lib_calls: list[dict],
                        base_reg: int) -> dict[int, dict]:
    """Trace return value stores to app memory after library calls.

    For each lib_call with an output field, scans the fallthrough block
    for stores of the return register to d(base_reg).  Returns a map
    of app memory offsets to the function/field that produced the value.

    Returns: {offset: {"function": "Output", "name": "file", ...}}
    """
    kb = KB()
    result = {}
    base_reg_name = f"a{base_reg}"

    for call in lib_calls:
        output = call.get("output")
        if not output or not output.get("reg"):
            continue

        ret_reg = output["reg"].lower()
        call_addr = call["addr"]

        # Find the block containing the call
        block = blocks.get(call.get("block"))
        if not block:
            continue

        # Scan for store of ret_reg to d(base_reg) in instructions
        # after the call.  The call may end the block, so also check
        # the fallthrough block.
        import re
        ret_key = ("dn" if ret_reg[0] == "d" else "an", int(ret_reg[1]))
        store_info = {
            "function": call["function"],
            "name": output.get("name", "result"),
            "type": output.get("type"),
            "library": call.get("library"),
        }

        def _scan_for_store(instructions):
            """Scan instructions for ret_reg -> d(base_reg). Returns offset or None."""
            for inst in instructions:
                text = inst.text.lower()
                mn = _extract_mnemonic(text)
                if mn in ("move", "movea"):
                    m = re.match(
                        rf'{mn}\.\w\s+{ret_reg}\s*,'
                        rf'\s*(-?\d+)\({base_reg_name}\)',
                        text)
                    if m:
                        return int(m.group(1))
                # Stop if ret_reg is overwritten by a non-store instruction
                ikb = kb.find(mn) if mn else None
                if ikb:
                    dst = decode_destination(
                        inst.raw, ikb, kb.meta,
                        _extract_size(text), inst.offset)
                    if dst == ret_key:
                        return None
            return None

        # Instructions after the call in the same block
        past_call = False
        after_call = []
        for inst in block.instructions:
            if past_call:
                after_call.append(inst)
            if inst.offset == call_addr:
                past_call = True

        offset = _scan_for_store(after_call)
        if offset is None:
            # Check fallthrough block
            for xref in block.xrefs:
                if xref.type == "fallthrough":
                    ft_block = blocks.get(xref.dst)
                    if ft_block:
                        offset = _scan_for_store(ft_block.instructions)
                    break

        if offset is not None:
            result[offset] = store_info

    return result


# ── Unified app memory type map ───────────────────────────────────────

def build_app_memory_types(blocks: dict[int, BasicBlock],
                           lib_calls: list[dict],
                           base_reg: int) -> dict[int, dict]:
    """Build a type map for app memory slots from library call data flow.

    Combines forward propagation (return values -> register copies ->
    app memory stores) with backward propagation (call inputs <- app
    memory loads).  Handles cross-subroutine flow: sub A stores Output()
    result to d(A6), sub B loads it for Write(file=D1).

    Returns: {app_offset: {"name": str, "function": str, "type": str, ...}}
    """
    import re
    kb = KB()
    result = {}
    base_reg_name = f"a{base_reg}"
    disp_pattern = re.compile(rf'(-?\d+)\({base_reg_name}\)')

    def _trace_reg_forward(instructions, src_reg, info):
        """Trace src_reg through copies and stores to d(base_reg).

        Follows move/movea chains: if src_reg is copied to another
        register, continues tracing the copy.  Stops when src_reg
        (or its copy) is stored to d(base_reg) or overwritten.
        """
        tracked = {src_reg}  # set of registers carrying the value
        for inst in instructions:
            text = inst.text.lower()
            mn = _extract_mnemonic(text)
            if not mn:
                continue

            copied_to = None  # register added by copy in this instruction

            # Check for store to d(base_reg) from any tracked register
            if mn in ("move", "movea"):
                for treg in list(tracked):
                    m = re.match(
                        rf'{mn}\.\w\s+{treg}\s*,\s*'
                        rf'(-?\d+)\({base_reg_name}\)',
                        text)
                    if m:
                        offset = int(m.group(1))
                        if offset not in result:
                            result[offset] = dict(info)
                        return

                # Check for register-to-register copy of tracked reg
                for treg in list(tracked):
                    m = re.match(
                        rf'{mn}\.\w\s+{treg}\s*,\s*([da]\d)\s*$',
                        text)
                    if m:
                        copied_to = m.group(1)
                        tracked.add(copied_to)
                        break

            # Check if any tracked register is overwritten
            # (skip the register we just added via copy)
            ikb = kb.find(mn)
            if ikb:
                dst = decode_destination(
                    inst.raw, ikb, kb.meta,
                    _extract_size(text), inst.offset)
                if dst:
                    mode_str, reg_num = dst
                    dst_name = f"{'d' if mode_str == 'dn' else 'a'}{reg_num}"
                    if dst_name in tracked and dst_name != copied_to:
                        tracked.discard(dst_name)
                        if not tracked:
                            return

    # Forward: trace return values to app memory stores
    for call in lib_calls:
        output = call.get("output")
        if not output or not output.get("reg"):
            continue
        ret_reg = output["reg"].lower()
        call_addr = call["addr"]
        info = {
            "function": call["function"],
            "name": output.get("name", "result"),
            "type": output.get("type"),
            "library": call.get("library"),
            "direction": "forward",
        }

        block = blocks.get(call.get("block"))
        if not block:
            continue

        # Collect instructions after the call
        past_call = False
        after_call = []
        for inst in block.instructions:
            if past_call:
                after_call.append(inst)
            if inst.offset == call_addr:
                past_call = True

        # Trace in same block
        _trace_reg_forward(after_call, ret_reg, info)

        # Trace in fallthrough block
        for xref in block.xrefs:
            if xref.type == "fallthrough":
                ft_block = blocks.get(xref.dst)
                if ft_block:
                    _trace_reg_forward(ft_block.instructions, ret_reg, info)
                    # Also follow fallthrough's fallthrough (conditional blocks)
                    for xref2 in ft_block.xrefs:
                        if xref2.type in ("fallthrough", "branch"):
                            ft2 = blocks.get(xref2.dst)
                            if ft2:
                                _trace_reg_forward(
                                    ft2.instructions, ret_reg, info)
                break

    # Backward: trace call inputs to app memory loads
    for call in lib_calls:
        inputs = call.get("inputs")
        if not inputs:
            continue

        block = blocks.get(call.get("block"))
        if not block or not block.instructions:
            continue

        call_idx = None
        for i, inst in enumerate(block.instructions):
            if inst.offset == call["addr"]:
                call_idx = i
                break
        if call_idx is None:
            continue

        for inp in inputs:
            reg = inp["reg"].lower()
            # Walk backward to find where this register was loaded
            for i in range(call_idx - 1, -1, -1):
                inst = block.instructions[i]
                text = inst.text.lower()
                mn = _extract_mnemonic(text)
                ikb = kb.find(mn) if mn else None
                if not ikb:
                    continue

                # Check if this instruction writes to the arg register
                dst = decode_destination(
                    inst.raw, ikb, kb.meta,
                    _extract_size(text), inst.offset)
                if not dst:
                    continue
                mode_str = "dn" if reg[0] == "d" else "an"
                reg_num = int(reg[1])
                if dst != (mode_str, reg_num):
                    continue

                # Found the setter. Check if source is d(base_reg)
                m = disp_pattern.search(text)
                if m:
                    offset = int(m.group(1))
                    if offset not in result:
                        result[offset] = {
                            "name": inp["name"],
                            "function": call["function"],
                            "type": inp.get("type"),
                            "library": call.get("library"),
                            "direction": "backward",
                        }
                break  # stop after finding the setter

    return result


# ── Call argument annotation ─────────────────────────────────────────

def annotate_call_arguments(blocks: dict[int, BasicBlock],
                            lib_calls: list[dict]) -> dict[int, dict]:
    """Annotate instructions that set up arguments for library calls.

    For each lib_call with inputs, walks backward from the call within
    the containing block to find instructions that write to argument
    registers.  Returns a map of instruction offsets to argument info.

    Returns: {inst_offset: {"arg_name": "file", "function": "Write", ...}}
    """
    kb = KB()
    result = {}

    for call in lib_calls:
        inputs = call.get("inputs")
        if not inputs:
            continue

        block = blocks.get(call.get("block"))
        if not block or not block.instructions:
            continue

        # Find the call instruction index
        call_idx = None
        for i, inst in enumerate(block.instructions):
            if inst.offset == call["addr"]:
                call_idx = i
                break
        if call_idx is None:
            continue

        # Build set of argument registers to find
        pending = {}  # reg_key -> input dict
        for inp in inputs:
            reg = inp["reg"].lower()
            mode_str = "dn" if reg[0] == "d" else "an"
            reg_num = int(reg[1])
            pending[(mode_str, reg_num)] = inp

        # Walk backward from call
        for i in range(call_idx - 1, -1, -1):
            if not pending:
                break
            inst = block.instructions[i]
            text = inst.text.lower()
            mn = _extract_mnemonic(text)
            ikb = kb.find(mn) if mn else None
            if not ikb:
                continue

            dst = decode_destination(inst.raw, ikb, kb.meta,
                                     _extract_size(text), inst.offset)
            if dst and dst in pending:
                inp = pending.pop(dst)
                result[inst.offset] = {
                    "arg_name": inp["name"],
                    "arg_reg": inp["reg"],
                    "function": call["function"],
                    "library": call.get("library"),
                }

    return result


# ── Backward type propagation ─────────────────────────────────────────

def _build_struct_field_map(struct_def: dict) -> dict[int, str]:
    """Build offset -> field_name map from KB struct definition."""
    return {
        f["offset"]: f["name"]
        for f in struct_def["fields"]
        if f["type"] != "LABEL"
    }


def propagate_input_types(blocks: dict, lib_calls: list[dict],
                          os_kb: dict) -> dict[int, dict[str, dict]]:
    """Walk backward from OS call sites to find struct-typed register ranges.

    For each resolved OS call with struct-typed inputs, traces backward
    through the containing block to find where the input register was
    set.  All instructions between the setter and the call that use
    d(An) on the typed register get struct field annotations.

    Register write detection uses KB-driven destination decoding from
    opcode bits via decode_destination().

    Returns: {inst_offset: {reg: {"struct": "IS", "fields": {14: "IS_DATA", ...}}}}
    """
    kb = KB()
    structs = os_kb["structs"]
    result = {}

    for call in lib_calls:
        # Collect struct-typed input registers
        typed_inputs = {}  # reg_name_lower -> i_struct name
        for inp in call.get("inputs", []):
            i_struct = inp.get("i_struct")
            if i_struct and i_struct in structs:
                typed_inputs[inp["reg"].lower()] = i_struct

        if not typed_inputs:
            continue

        block = blocks.get(call["block"])
        if not block or not block.instructions:
            continue

        # Find the call instruction index
        call_idx = None
        for i, inst in enumerate(block.instructions):
            if inst.offset == call["addr"]:
                call_idx = i
                break
        if call_idx is None:
            continue

        # For each typed register, walk backward to find where it was
        # set, then annotate all instructions from setter to call.
        for reg, struct_name in typed_inputs.items():
            reg_mode, reg_num = parse_reg_name(reg)
            field_map = _build_struct_field_map(structs[struct_name])

            # Walk backward: find last instruction that writes to reg.
            setter_idx = 0
            for j in range(call_idx - 1, -1, -1):
                jinst = block.instructions[j]
                mn = _extract_mnemonic(jinst.text)
                inst_kb = kb.find(mn)
                if inst_kb is None:
                    continue
                sz = _extract_size(jinst.text)
                dst = decode_destination(
                    jinst.raw, inst_kb, kb.meta, sz, jinst.offset)
                if dst is not None and dst[0] == reg_mode and dst[1] == reg_num:
                    setter_idx = j
                    break

            # Annotate all instructions in [setter_idx, call_idx]
            for j in range(setter_idx, call_idx + 1):
                off = block.instructions[j].offset
                result.setdefault(off, {})[reg] = {
                    "struct": struct_name,
                    "fields": field_map,
                }

    return result


def _build_lvo_lookup(os_kb: dict) -> dict:
    """Build combined LVO lookup: {(library_name, lvo_offset_int): function_dict}.

    Also builds reverse: {lvo_offset_int: [(library_name, func_name, func_dict)]}
    for when we don't know which library base is in A6.
    """
    by_lib_lvo = {}
    by_lvo = {}
    for lib_name, lib_data in os_kb["libraries"].items():
        for lvo_str, func_name in lib_data["lvo_index"].items():
            lvo = int(lvo_str)
            func = lib_data["functions"][func_name]
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


def _resolve_lvo(lvo: int, library: str, lvo_lookup: dict) -> dict:
    """Resolve an LVO offset to a function in a known library."""
    key = (library, lvo)
    match = lvo_lookup["by_lib_lvo"].get(key)
    if match:
        info = {"library": match["library"], "function": match["function"]}
        if match.get("no_return"):
            info["no_return"] = True
        if match.get("inputs"):
            info["inputs"] = match["inputs"]
        if match.get("output"):
            info["output"] = match["output"]
        return info
    return {"library": library, "function": f"LVO_{-lvo}"}


def _find_sub_entry(block_addr: int, blocks: dict,
                    call_targets: set[int]) -> int | None:
    """Walk predecessors to find the containing subroutine entry."""
    visited = set()
    work = [block_addr]
    while work:
        addr = work.pop()
        if addr in visited:
            continue
        visited.add(addr)
        if addr in call_targets:
            return addr
        blk = blocks.get(addr)
        if blk:
            work.extend(blk.predecessors)
    return None


def identify_library_calls(blocks: dict[int, BasicBlock],
                           code: bytes,
                           os_kb: dict,
                           exit_states: dict[int, tuple],
                           call_targets: set[int],
                           platform: dict,
                           ) -> list[dict]:
    """Identify OS library calls in analyzed code.

    Detects two patterns through the library base register (OS KB):
    1. Displacement EA: JSR d(A6) -- LVO is the displacement
    2. Indexed EA: JSR 0(A6,Dn.w) -- LVO is in the index register,
       resolved per-caller from exit states

    Library identity comes from:
    - Propagated library_base tags on A6 (from exit states)
    - Intra-block ExecBase load detection (MOVEA.L ($N).W,A6)

    EA field positions from M68K KB encodings.  ExecBase address and
    library base register from OS KB.

    Returns list of dicts:
        {"addr": int, "block": int, "library": str, "function": str,
         "lvo": int, "no_return": bool,
         "inputs": [...], "output": {...}}
    """
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

    # App base register concrete value (from init discovery)
    base_info = platform.get("initial_base_reg")
    app_base = base_info[1] if base_info else None

    absw_enc = kb.ea_enc["absw"]
    disp_enc = kb.ea_enc["disp"]
    index_enc = kb.ea_enc["index"]
    addr_mask = (1 << (kb.meta["size_byte_count"]["l"] * 8)) - 1
    brief_ext = {f["name"]: (f["bit_hi"], f["bit_lo"],
                             f["bit_hi"] - f["bit_lo"] + 1)
                 for f in kb.meta["ea_brief_ext_word"]}

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

    # Build caller map: subroutine_entry -> [caller_block_addrs]
    caller_map: dict[int, list[int]] = {}
    for addr, blk in blocks.items():
        for x in blk.xrefs:
            if x.type == "call" and x.dst in call_targets:
                caller_map.setdefault(x.dst, []).append(addr)

    results = []
    # Deferred: indexed EA calls needing per-caller resolution.
    # List of (block_addr, inst_offset, library, index_reg_mode,
    #          index_reg_num, base_displacement)
    deferred = []

    for block_addr in sorted(blocks):
        block = blocks[block_addr]
        if not block.instructions:
            continue

        # Library identity for A6 in this block.
        a6_lib = None

        # Check propagated state for A6's library_base tag
        if block_addr in exit_states:
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

            # Detect library base load into the base register.
            # 1. MOVEA.L ($N).W,A6 — ExecBase from absolute address
            # 2. MOVEA.L d(An),A6 — library base from tagged memory
            if (ikb.get("operation_type") == "move"
                    and ikb.get("source_sign_extend")
                    and len(inst.raw) >= kb.opword_bytes + 2):
                opcode = struct.unpack_from(">H", inst.raw, 0)[0]
                src_mode = xf(opcode, movea_mode_f)
                src_reg = xf(opcode, movea_reg_f)
                dst_reg = xf(opcode, movea_dst_spec)

                if dst_reg == base_reg_num:
                    if (src_mode == absw_enc[0]
                            and src_reg == absw_enc[1]):
                        addr_val = struct.unpack_from(
                            ">h", inst.raw, kb.opword_bytes)[0]
                        addr_val &= addr_mask
                        if addr_val == exec_base_addr:
                            a6_lib = exec_lib_name
                    elif (src_mode == disp_enc[0]
                            and block_addr in exit_states
                            and app_base is not None):
                        disp_val = struct.unpack_from(
                            ">h", inst.raw, kb.opword_bytes)[0]
                        _, blk_mem = exit_states[block_addr]
                        mem_addr = (app_base + disp_val) & addr_mask
                        tag_val = blk_mem.read(mem_addr, "l")
                        if (tag_val.tag
                                and "library_base" in tag_val.tag):
                            a6_lib = tag_val.tag["library_base"]

            # Detect library call: JSR through base_reg
            if flow.get("type") != "call":
                continue
            target = _extract_branch_target(inst, inst.offset)
            if target is not None:
                continue  # resolved — not a library call
            if len(inst.raw) < kb.opword_bytes + 2:
                continue

            opcode = struct.unpack_from(">H", inst.raw, 0)[0]
            ea_mode = xf(opcode, jsr_mode_f)
            ea_reg = xf(opcode, jsr_reg_f)

            # Pattern 1: JSR d(A6) — displacement EA, LVO is disp
            if ea_mode == disp_enc[0] and ea_reg == base_reg_num:
                disp = struct.unpack_from(
                    ">h", inst.raw, kb.opword_bytes)[0]
                call_info = {"addr": inst.offset, "block": block_addr,
                             "lvo": disp}
                if a6_lib:
                    call_info.update(_resolve_lvo(disp, a6_lib,
                                                 lvo_lookup))
                else:
                    call_info["library"] = "unknown"
                    call_info["function"] = f"LVO_{-disp}"
                results.append(call_info)
                continue

            # Pattern 2: JSR 0(A6,Dn.w) — indexed EA, LVO in index reg
            if ea_mode == index_enc[0] and ea_reg == base_reg_num:
                ext = struct.unpack_from(
                    ">H", inst.raw, kb.opword_bytes)[0]
                idx_da = xf(ext, brief_ext["D/A"])
                idx_reg = xf(ext, brief_ext["REGISTER"])
                idx_wl = xf(ext, brief_ext["W/L"])
                disp_raw = xf(ext, brief_ext["DISPLACEMENT"])
                disp_w = brief_ext["DISPLACEMENT"][2]
                if disp_raw & (1 << (disp_w - 1)):
                    disp_raw -= (1 << disp_w)

                idx_mode = "an" if idx_da == 1 else "dn"

                # Try resolving from this block's exit state
                if block_addr in exit_states:
                    cpu, _ = exit_states[block_addr]
                    idx_val = cpu.get_reg(idx_mode, idx_reg)
                    if idx_val.is_known:
                        v = idx_val.concrete
                        idx_size = "l" if idx_wl == 1 else "w"
                        nbits = kb.meta["size_byte_count"][idx_size] * 8
                        mask = (1 << nbits) - 1
                        v = v & mask
                        if v >= (1 << (nbits - 1)):
                            v -= (1 << nbits)
                        lvo = disp_raw + v
                        call_info = {"addr": inst.offset,
                                     "block": block_addr, "lvo": lvo}
                        if a6_lib:
                            call_info.update(_resolve_lvo(
                                lvo, a6_lib, lvo_lookup))
                        else:
                            call_info["library"] = "unknown"
                            call_info["function"] = f"LVO_{-lvo}"
                        results.append(call_info)
                        continue

                # Defer for per-caller resolution
                deferred.append((block_addr, inst.offset, a6_lib,
                                 idx_mode, idx_reg, idx_wl, disp_raw))

    # Per-caller resolution for deferred indexed-EA calls.
    # The callee block's index register is unknown (joined from
    # multiple callers), but each caller's exit state has the
    # concrete value.
    for (blk_addr, inst_addr, lib, idx_mode, idx_reg,
         idx_wl, base_disp) in deferred:
        sub_entry = _find_sub_entry(blk_addr, blocks, call_targets)
        if sub_entry is None:
            continue
        callers = caller_map.get(sub_entry, [])
        for caller_addr in callers:
            if caller_addr not in exit_states:
                continue
            caller_cpu, _ = exit_states[caller_addr]
            idx_val = caller_cpu.get_reg(idx_mode, idx_reg)
            if not idx_val.is_known:
                continue
            v = idx_val.concrete
            idx_size = "l" if idx_wl == 1 else "w"
            nbits = kb.meta["size_byte_count"][idx_size] * 8
            mask = (1 << nbits) - 1
            v = v & mask
            if v >= (1 << (nbits - 1)):
                v -= (1 << nbits)
            lvo = base_disp + v

            # Resolve library from caller's A6 if callee didn't have it
            call_lib = lib
            if call_lib is None:
                a6_val = caller_cpu.a[base_reg_num]
                if a6_val.tag and "library_base" in a6_val.tag:
                    call_lib = a6_val.tag["library_base"]
            if call_lib is None:
                continue

            call_info = {"addr": caller_addr, "block": caller_addr,
                         "lvo": lvo, "dispatch": inst_addr}
            call_info.update(_resolve_lvo(lvo, call_lib, lvo_lookup))
            results.append(call_info)

    return results
