from __future__ import annotations
"""Build disassembly-time substitution maps."""

import re

from m68k.kb_util import KB, decode_destination, parse_reg_name
from m68k.m68k_executor import _extract_branch_target, _extract_mnemonic, _extract_size
from m68k.kb_util import find_containing_sub, decode_instruction_operands
from m68k.os_calls import build_app_memory_types


def build_lvo_substitutions(*, blocks: dict, lib_calls: list[dict],
                            hunk_entities: list[dict], kb: KB
                            ) -> tuple[dict[str, dict[int, str]], dict[int, tuple[str, str]]]:
    lvo_equs: dict[str, dict[int, str]] = {}
    lvo_substitutions: dict[int, tuple[str, str]] = {}
    sorted_code_ents = sorted(
        [{"addr": int(e["addr"], 16), "end": int(e["end"], 16)}
         for e in hunk_entities if e["type"] == "code"],
        key=lambda s: s["addr"])

    for call in lib_calls:
        lib = call.get("library")
        func = call.get("function")
        lvo = call.get("lvo")
        if not lib or not func or lvo is None or lib == "unknown":
            continue
        if func.startswith("LVO_"):
            continue
        sym = f"_LVO{func}"
        lvo_equs.setdefault(lib, {})[lvo] = sym
        if "dispatch" in call:
            caller_blk = blocks.get(call["addr"])
            if not caller_blk:
                continue
            disp_sub = find_containing_sub(call["dispatch"], sorted_code_ents)
            if disp_sub is None:
                continue
            for i, inst in enumerate(caller_blk.instructions):
                target = _extract_branch_target(inst, inst.offset)
                if target != disp_sub:
                    continue
                for j in range(i - 1, -1, -1):
                    prev = caller_blk.instructions[j]
                    prev_mn = _extract_mnemonic(prev.text)
                    prev_kb = kb.find(prev_mn)
                    if prev_kb is None:
                        continue
                    prev_sz = _extract_size(prev.text)
                    prev_dec = decode_instruction_operands(
                        prev.raw, prev_kb, kb.meta, prev_sz, prev.offset)
                    if prev_dec["imm_val"] is None:
                        continue
                    pv = prev_dec["imm_val"]
                    pv_signed = pv - 0x100000000 if pv >= 0x80000000 else pv
                    if pv_signed == lvo:
                        imm_m = re.search(r'#(\$?-?[0-9a-fA-F]+)', prev.text)
                        if imm_m:
                            lvo_substitutions[prev.offset] = (
                                f"#{imm_m.group(1)}", f"#{sym}")
                        break
                break
        else:
            lvo_substitutions[call["addr"]] = (f"{lvo}(", f"{sym}(")
    return lvo_equs, lvo_substitutions


def build_arg_substitutions(*, blocks: dict, lib_calls: list[dict], os_kb: dict,
                            kb: KB) -> tuple[dict[str, int], dict[int, tuple[str, str]]]:
    arg_equs: dict[str, int] = {}
    arg_substitutions: dict[int, tuple[str, str]] = {}
    const_domains = os_kb["_meta"]["constant_domains"]
    all_consts = os_kb.get("constants", {})
    func_const_map: dict[str, dict[int, str]] = {}
    for func_name, const_names in const_domains.items():
        vmap = {}
        for cn in const_names:
            cv = all_consts.get(cn, {}).get("value")
            if cv is not None:
                vmap[cv] = cn
        if vmap:
            func_const_map[func_name] = vmap
    for call in lib_calls:
        func_name = call.get("function")
        if not func_name or func_name.startswith("LVO_"):
            continue
        vmap = func_const_map.get(func_name)
        if not vmap:
            continue
        lib = call["library"]
        func = os_kb["libraries"].get(lib, {}).get("functions", {}).get(func_name, {})
        inputs = func.get("inputs", [])
        if not inputs:
            continue
        blk_addr = call["block"]
        blk = blocks.get(blk_addr)
        if not blk:
            continue
        call_idx = None
        call_addr = call["addr"]
        if "dispatch" in call:
            continue
        for ci, inst in enumerate(blk.instructions):
            if inst.offset == call_addr:
                call_idx = ci
                break
        if call_idx is None:
            continue
        for inp in inputs:
            reg = inp["reg"].lower()
            reg_mode, reg_n = parse_reg_name(reg)
            for j in range(call_idx - 1, -1, -1):
                prev = blk.instructions[j]
                prev_mn = _extract_mnemonic(prev.text)
                prev_kb = kb.find(prev_mn)
                if prev_kb is None:
                    continue
                prev_sz = _extract_size(prev.text)
                prev_dec = decode_instruction_operands(
                    prev.raw, prev_kb, kb.meta, prev_sz, prev.offset)
                if prev_dec["imm_val"] is None:
                    continue
                dst = decode_destination(prev.raw, prev_kb, kb.meta,
                                         prev_sz, prev.offset)
                if dst is None:
                    continue
                dst_mode, dst_num = dst
                if dst_mode != reg_mode or dst_num != reg_n:
                    continue
                imm_val = prev_dec["imm_val"]
                const_name = vmap.get(imm_val)
                if const_name is None and imm_val >= 0x80000000:
                    const_name = vmap.get(imm_val - 0x100000000)
                if const_name:
                    equ_val = imm_val - 0x100000000 if imm_val >= 0x80000000 else imm_val
                    arg_equs[const_name] = equ_val
                    imm_m = re.search(r'#(\$?-?[0-9a-fA-F]+)', prev.text)
                    if imm_m:
                        arg_substitutions[prev.offset] = (
                            f"#{imm_m.group(1)}", f"#{const_name}")
                break
    return arg_equs, arg_substitutions


def build_app_offset_symbols(*, blocks: dict, lib_calls: list[dict], platform: dict
                             ) -> dict[int, str]:
    app_offsets: dict[int, str] = {}
    base_info = platform.get("initial_base_reg")
    init_mem = platform.get("_initial_mem")
    if base_info and init_mem:
        base_concrete = base_info[1]
        alloc_base = 0x80000000
        for (addr, _nbytes), tag in init_mem._tags.items():
            if not tag or "library_base" not in tag:
                continue
            if addr >= alloc_base:
                offset = addr - base_concrete
                if offset < 0 or offset > 0xFFFF:
                    continue
            offset = addr - base_concrete
            lib_name = tag["library_base"]
            base_name = lib_name.rsplit(".", 1)[0]
            sym = re.sub(r'[^a-z0-9]+', '_', base_name.lower())
            app_offsets[offset] = f"app_{sym}_base"
    if base_info and lib_calls:
        typed_slots = build_app_memory_types(blocks, lib_calls, base_reg=base_info[0])
        for offset, info in typed_slots.items():
            if offset not in app_offsets:
                func = info["function"]
                name = info.get("name", "result")
                sym = re.sub(r'[^a-z0-9]+', '_', f"app_{func}_{name}".lower())
                app_offsets[offset] = sym
    return app_offsets
