"""Shared KB-driven table and pointer source recovery helpers."""

import struct

from .kb_util import decode_destination, decode_instruction_operands, xf
from . import address_reconstruction as _ar
from . import value_transforms as _vt


def _read_code_long(code: bytes, addr: int, code_size: int, kb) -> int | None:
    """Read a concrete longword from code bytes or reject it."""
    long_size = kb.size_bytes["l"]
    if addr < 0 or addr + long_size > code_size or (addr & kb.align_mask):
        return None
    return struct.unpack_from(">I", code, addr)[0]


def _find_full_extension_long_pointer_dispatch(jump_operand, instructions,
                                               code: bytes, code_size: int, kb):
    """Resolve inferable full-extension long-pointer dispatch source info."""
    if jump_operand is None:
        return None
    if jump_operand.mode not in ("index", "pcindex"):
        return None
    if not jump_operand.full_extension or not jump_operand.memory_indirect:
        return None
    if jump_operand.base_suppressed or jump_operand.index_suppressed:
        return None

    if jump_operand.mode == "index":
        table_base = _ar.resolve_block_pc_base(instructions, kb, jump_operand.reg)
        pointer_addr = (table_base + (jump_operand.base_displacement or 0)
                        if table_base is not None else None)
        if jump_operand.postindexed:
            pointer = (_read_code_long(code, pointer_addr, code_size, kb)
                       if pointer_addr is not None else None)
            if pointer is None:
                return None
            return {
                "table_addr": ((pointer + (jump_operand.outer_displacement or 0))
                               & kb.addr_mask),
                "pattern": "memory_indirect_postindexed_long_pointer",
                "addend": 0,
            }
        if pointer_addr is None:
            return None
        return {
            "table_addr": pointer_addr,
            "pattern": "memory_indirect_long_pointer",
            "addend": jump_operand.outer_displacement or 0,
        }

    if jump_operand.postindexed:
        pointer = _read_code_long(code, jump_operand.value, code_size, kb)
        if pointer is None:
            return None
        return {
            "table_addr": ((pointer + (jump_operand.outer_displacement or 0))
                           & kb.addr_mask),
            "pattern": "pc_memory_indirect_postindexed_long_pointer",
            "addend": 0,
        }
    return {
        "table_addr": jump_operand.value,
        "pattern": "pc_memory_indirect_long_pointer",
        "addend": jump_operand.outer_displacement or 0,
    }


def find_pointer_table_load(instructions, kb,
                            target_reg: int, stop_before: int,
                            code: bytes, code_size: int) -> dict | None:
    """Find a long pointer table load into An from indexed code-section data."""
    from . import static_values as _sv

    long_size = kb.size_bytes["l"]
    current_mode = "an"
    current_reg = target_reg
    addend_offset = 0
    transforms = []

    for inst in reversed(instructions):
        if inst.offset >= stop_before:
            continue
        mi = kb.instruction_kb(inst)
        decoded = decode_instruction_operands(
            inst.raw, mi, kb.meta, inst.operand_size, inst.offset)
        if (mi.get("operation_type") in ("add", "sub")
                and decoded.get("imm_val") is not None):
            ea_op = decoded.get("ea_op")
            if (ea_op is not None
                    and ea_op.mode == current_mode
                    and ea_op.reg == current_reg):
                imm = decoded["imm_val"]
                addend_offset += imm if mi.get("operation_type") == "add" else -imm
                continue
        ea_op = decoded.get("ea_op")
        if (mi.get("operation_type") in ("add", "sub")
                and ea_op is not None
                and ea_op.mode in ("dn", "an")):
            dst = decode_destination(inst.raw, mi, kb.meta, inst.operand_size, inst.offset)
            if dst == (current_mode, current_reg):
                src_val = _sv._resolve_block_constant_reg(
                    instructions, kb, ea_op.mode, ea_op.reg, inst.offset)
                if src_val is not None:
                    addend_offset += src_val if mi.get("operation_type") == "add" else -src_val
                    continue
        if (current_mode == "dn"
                and mi.get("operation_type") in ("shift", "rotate")
                and decoded.get("reg_num") == current_reg
                and decoded.get("imm_val") is not None):
            transforms.append(("shift", inst.opcode_text, inst.operand_size, decoded["imm_val"]))
            continue
        if (current_mode == "dn"
                and mi.get("operation_type") in ("shift", "rotate")
                and decoded.get("imm_val") is None
                and len(inst.operand_nodes) == 2):
            src_node, dst_node = inst.operand_nodes
            if (src_node.kind == "register"
                    and dst_node.kind == "register"
                    and dst_node.register == f"d{current_reg}"
                    and src_node.register is not None
                    and src_node.register.startswith("d")):
                count_reg = int(src_node.register[1:])
                count_val = _sv._resolve_block_constant_reg(
                    instructions, kb, "dn", count_reg, inst.offset)
                if count_val is not None and count_val >= 0:
                    transforms.append(("shift", inst.opcode_text, inst.operand_size, count_val))
                    continue
            return None
        if (current_mode == "dn"
                and mi.get("operation_type") in ("and", "or", "xor")
                and decoded.get("imm_val") is not None
                and ea_op is not None
                and ea_op.mode == "dn"
                and ea_op.reg == current_reg):
            transforms.append(("logical", mi.get("operation_type"), inst.operand_size,
                               decoded["imm_val"]))
            continue
        if (current_mode == "dn"
                and mi.get("operation_type") == "bit_test"
                and ea_op is not None
                and ea_op.mode == "dn"
                and ea_op.reg == current_reg
                and decoded.get("imm_val") is not None):
            transforms.append(("bitop", inst.opcode_text, decoded["imm_val"]))
            continue
        if (current_mode == "dn"
                and mi.get("operation_type") == "bit_test"
                and decoded.get("imm_val") is None
                and len(inst.operand_nodes) == 2):
            src_node, dst_node = inst.operand_nodes
            if (src_node.kind == "register"
                    and dst_node.kind == "register"
                    and dst_node.register == f"d{current_reg}"
                    and src_node.register is not None
                    and src_node.register.startswith("d")):
                count_reg = int(src_node.register[1:])
                count_val = _sv._resolve_block_constant_reg(
                    instructions, kb, "dn", count_reg, inst.offset)
                if count_val is not None:
                    transforms.append(("bitop", inst.opcode_text, count_val))
                    continue
            return None
        if (current_mode == "dn"
                and mi.get("operation_type") == "test"
                and ea_op is not None
                and ea_op.mode == "dn"
                and ea_op.reg == current_reg):
            transforms.append(("test", inst.opcode_text, inst.operand_size))
            continue
        if (current_mode == "dn"
                and mi.get("operation_type") in ("and", "or", "xor")
                and decoded.get("imm_val") is None
                and ea_op is not None
                and ea_op.mode in ("dn", "an")):
            dst = decode_destination(inst.raw, mi, kb.meta, inst.operand_size, inst.offset)
            if dst == (current_mode, current_reg):
                src_val = _sv._resolve_block_constant_reg(
                    instructions, kb, ea_op.mode, ea_op.reg, inst.offset)
                if src_val is not None:
                    transforms.append(("logical", mi.get("operation_type"),
                                       inst.operand_size, src_val))
                    continue
            return None
        if (current_mode == "dn"
                and mi.get("operation_type") in ("not", "neg")
                and ea_op is not None
                and ea_op.mode == "dn"
                and ea_op.reg == current_reg):
            transforms.append(("unary", mi.get("operation_type"), inst.operand_size))
            continue
        if (current_mode == "dn"
                and mi.get("operation_type") == "swap"
                and len(inst.operand_nodes) == 1
                and inst.operand_nodes[0].kind == "register"
                and inst.operand_nodes[0].register == f"d{current_reg}"):
            transforms.append(("swap",))
            continue
        if mi.get("operation_type") == "swap":
            partner = _vt._swap_partner(inst, current_mode, current_reg)
            if partner is not None:
                current_mode, current_reg = partner
                continue
        if (current_mode == "dn"
                and mi.get("operation_type") == "sign_extend"
                and len(inst.operand_nodes) == 1
                and inst.operand_nodes[0].kind == "register"
                and inst.operand_nodes[0].register == f"d{current_reg}"):
            transforms.append(("sign_extend", inst.operand_size))
            continue
        if (current_mode == "dn"
                and mi.get("operation_type") in ("multiply", "divide")
                and len(inst.operand_nodes) == 2):
            src_node, dst_node = inst.operand_nodes
            if (src_node.kind in ("register", "immediate")
                    and dst_node.kind == "register"
                    and dst_node.register == f"d{current_reg}"):
                if src_node.kind == "register":
                    src_mode = "an" if src_node.register.startswith("a") else "dn"
                    src_val = _sv._resolve_block_constant_reg(
                        instructions, kb, src_mode, int(src_node.register[1:]), inst.offset)
                else:
                    src_val = src_node.value
                if src_val is None:
                    return None
                transforms.append((mi.get("operation_type"), inst.opcode_text,
                                   inst.operand_size, src_val))
                continue
        if current_mode == "an":
            delta = _ar._immediate_an_adjustment(mi, decoded, current_reg)
            if delta is not None:
                addend_offset += delta
                continue
        dst = decode_destination(inst.raw, mi, kb.meta, inst.operand_size, inst.offset)
        if dst != (current_mode, current_reg):
            continue
        if ea_op is None:
            return None
        if ea_op.mode in ("dn", "an"):
            if inst.operand_size != "l":
                return None
            current_mode = ea_op.mode
            current_reg = ea_op.reg
            continue

        if ea_op.mode == "pcindex":
            if ea_op.base_suppressed or ea_op.index_suppressed:
                return None
            if ea_op.full_extension:
                if not ea_op.memory_indirect:
                    return None
                if ea_op.postindexed:
                    pointer = _read_code_long(code, ea_op.value, code_size, kb)
                    if pointer is None:
                        return None
                    return {
                        "table_addr": (pointer + (ea_op.outer_displacement or 0)) & kb.addr_mask,
                        "stride": long_size,
                        "addend": addend_offset,
                        "transforms": tuple(transforms),
                    }
                return {
                    "table_addr": ea_op.value,
                    "stride": long_size,
                    "addend": (ea_op.outer_displacement or 0) + addend_offset,
                    "transforms": tuple(transforms),
                }
            if ea_op.memory_indirect:
                return None
            return {
                "table_addr": ea_op.value,
                "stride": long_size,
                "addend": addend_offset,
                "transforms": tuple(transforms),
            }

        if ea_op.mode == "index":
            if ea_op.base_suppressed or ea_op.index_suppressed:
                return None
            lea_addr = _ar.resolve_block_pc_base(
                [inst2 for inst2 in instructions if inst2.offset < inst.offset],
                kb, ea_op.reg)
            if lea_addr is None:
                return None
            if ea_op.full_extension:
                pointer_addr = lea_addr + (ea_op.base_displacement or 0)
                if not ea_op.memory_indirect:
                    return None
                if ea_op.postindexed:
                    pointer = _read_code_long(code, pointer_addr, code_size, kb)
                    if pointer is None:
                        return None
                    return {
                        "table_addr": (pointer + (ea_op.outer_displacement or 0)) & kb.addr_mask,
                        "stride": long_size,
                        "addend": addend_offset,
                        "transforms": tuple(transforms),
                    }
                return {
                    "table_addr": pointer_addr,
                    "stride": long_size,
                    "addend": (ea_op.outer_displacement or 0) + addend_offset,
                    "transforms": tuple(transforms),
                }
            if ea_op.memory_indirect:
                return None
            return {
                "table_addr": lea_addr + ea_op.value,
                "stride": long_size,
                "addend": addend_offset,
                "transforms": tuple(transforms),
            }

        return None

    return None


def find_table_source(instructions, kb, index_mode: str,
                      index_reg: int, stop_before: int) -> dict | None:
    """Find where an index register was loaded from code-section memory."""
    for inst in reversed(instructions):
        if inst.offset >= stop_before:
            continue
        mi = kb.instruction_kb(inst)
        dst = decode_destination(inst.raw, mi, kb.meta, "w", inst.offset)
        if not dst or dst != (index_mode, index_reg):
            continue

        decoded = decode_instruction_operands(
            inst.raw, mi, kb.meta, "w", inst.offset)
        ea_op = decoded.get("ea_op")
        if ea_op is None:
            return None

        word_size = kb.size_bytes["w"]

        if ea_op.mode == "pcdisp":
            return {"table_addr": ea_op.value,
                    "field_offset": 0, "stride": word_size}

        if ea_op.mode in kb.reg_indirect_modes | {"postinc"}:
            src_reg = ea_op.reg
            postinc_count = 0
            field_index = -1

            if ea_op.mode == "postinc":
                for scan_inst in instructions:
                    if scan_inst.offset >= stop_before:
                        break
                    if scan_inst.operand_size != "w":
                        continue
                    scan_mi = kb.instruction_kb(scan_inst)
                    scan_decoded = decode_instruction_operands(
                        scan_inst.raw, scan_mi, kb.meta, scan_inst.operand_size,
                        scan_inst.offset)
                    scan_ea = scan_decoded.get("ea_op")
                    if (scan_ea and scan_ea.mode == "postinc"
                            and scan_ea.reg == src_reg):
                        if scan_inst.offset == inst.offset:
                            field_index = postinc_count
                        postinc_count += 1

            lea_addr = _ar.resolve_block_pc_base(
                [inst2 for inst2 in instructions if inst2.offset < inst.offset],
                kb, src_reg)
            if lea_addr is None:
                return None
            disp = ea_op.value if ea_op.mode == "disp" else 0
            stride = (postinc_count * word_size
                      if postinc_count > 1 else word_size)
            field_off = (field_index * word_size
                         if field_index >= 0 else disp)
            return {"table_addr": lea_addr,
                    "field_offset": field_off,
                    "stride": stride}

        return None


def _is_adda_reg_src(inst, kb, target_reg: int) -> tuple | None:
    """Check for KB-driven ADDA with register source to target_reg."""
    mi = kb.instruction_kb(inst)
    if mi.get("operation_type") != "add" or not mi.get("source_sign_extend"):
        return None
    ea_spec = kb.ea_field_spec(mi)
    if ea_spec is None or len(inst.raw) < 2:
        return None
    opcode = struct.unpack_from(">H", inst.raw, 0)[0]
    dst = kb.dst_reg_field(mi)
    if dst is None or xf(opcode, dst) != target_reg:
        return None
    src_mode_val = xf(opcode, ea_spec[0])
    src_reg_val = xf(opcode, ea_spec[1])
    dn_enc = kb.ea_enc["dn"]
    an_enc = kb.ea_enc["an"]
    if src_mode_val == dn_enc[0]:
        return ("dn", src_reg_val)
    if src_mode_val == an_enc[0]:
        return ("an", src_reg_val)
    return None


def _is_adda_ind(inst, kb, target_reg: int) -> bool:
    """Check for KB-driven ADDA with (An) source to the same target_reg."""
    mi = kb.instruction_kb(inst)
    if mi.get("operation_type") != "add" or not mi.get("source_sign_extend"):
        return False
    ea_spec = kb.ea_field_spec(mi)
    if ea_spec is None or len(inst.raw) < 2:
        return False
    opcode = struct.unpack_from(">H", inst.raw, 0)[0]
    if xf(opcode, ea_spec[0]) != kb.ea_enc["ind"][0]:
        return False
    if xf(opcode, ea_spec[1]) != target_reg:
        return False
    dst = kb.dst_reg_field(mi)
    if dst is None or xf(opcode, dst) != target_reg:
        return False
    return True
