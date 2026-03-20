from __future__ import annotations
"""Build semantic operands from decoded instruction operands."""

from knowledge import runtime_m68k_analysis
from knowledge import runtime_m68k_disasm
from knowledge import runtime_m68k_decode

from m68k.instruction_decode import (
    decode_inst_destination,
    select_encoding_fields,
    select_operand_types,
    select_operand_types_from_raw,
)
from m68k.instruction_primitives import extract_branch_target

from disasm.decode import decode_inst_for_emit
from disasm.types import HunkDisassemblySession, SemanticOperand


_FLOW_BRANCH = runtime_m68k_analysis.FlowType.BRANCH
_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL
_FLOW_JUMP = runtime_m68k_analysis.FlowType.JUMP


def _instruction_ref(inst) -> str:
    return f"instruction at ${inst.offset:06x}"


def _operand_types_for_inst(inst, meta: dict) -> tuple[str, ...]:
    opcode = int.from_bytes(inst.raw[:2], "big")
    form_operand_types = list(runtime_m68k_disasm.FORM_OPERAND_TYPES.get(meta["mnemonic"], ()))
    if form_operand_types == [("usp", "an"), ("an", "usp")]:
        return form_operand_types[0] if ((opcode >> 3) & 1) else form_operand_types[1]
    if form_operand_types == [("rn", "ea"), ("ea", "rn")]:
        if len(inst.raw) < 4:
            raise ValueError(f"MOVES extension word missing for {_instruction_ref(inst)}")
        ext = int.from_bytes(inst.raw[2:4], "big")
        return form_operand_types[0] if ((ext >> 11) & 1) != 0 else form_operand_types[1]
    return select_operand_types_from_raw(meta["mnemonic"], inst.raw)


def _selected_form_register(inst, meta: dict, register_index: int) -> tuple[str, int] | None:
    opcode = int.from_bytes(inst.raw[:2], "big")
    fields = select_encoding_fields(meta["mnemonic"], opcode)
    plain_register_fields = [
        field for field in fields
        if field[0] == "REGISTER"
    ]
    if plain_register_fields:
        register_fields = plain_register_fields
    else:
        register_fields = [
            field for field in fields
            if field[0].startswith("REGISTER ")
        ]
        register_fields.sort(key=lambda field: field[2])
    if len(register_fields) <= register_index:
        return None
    field = register_fields[register_index]
    width = field[3]
    mask = (1 << width) - 1
    reg = (opcode >> field[2]) & mask
    return ("dn", reg)


def _normalized_absolute_value(decoded_op) -> int | None:
    if decoded_op is None or getattr(decoded_op, "value", None) is None:
        return None
    if decoded_op.mode == "absw":
        return decoded_op.value & 0xFFFF
    if decoded_op.mode == "absl":
        return decoded_op.value
    return None


def _reloc_target(inst, hunk_session: HunkDisassemblySession, value: int) -> int | None:
    for ext_off in range(inst.offset + runtime_m68k_decode.OPWORD_BYTES,
                         inst.offset + inst.size):
        target = hunk_session.reloc_map.get(ext_off)
        if target == value:
            return target
    return None


def _register_name(mode: str, reg: int, token: str | None = None) -> str:
    if mode == "an" and reg == 7 and token is not None and token.lower() == "sp":
        return "sp"
    return f"{'a' if mode == 'an' else 'd'}{reg}"


def _register_text(mode: str, reg: int, token: str) -> str:
    if mode == "an" and reg == 7 and token.lower() == "sp":
        return "sp"
    return token.lower()


def _address_base_name(reg: int) -> str:
    return "sp" if reg == 7 else f"a{reg}"


def _same_register_name(expected: str, actual: str | None) -> bool:
    if actual is None:
        return False
    if expected == actual:
        return True
    return {expected, actual} == {"a7", "sp"}


def _apply_instruction_text_substitutions(text: str, inst_offset: int,
                                          hunk_session: HunkDisassemblySession,
                                          include_arg_subs: bool) -> str:
    sub = hunk_session.lvo_substitutions.get(inst_offset)
    if sub:
        text = text.replace(sub[0], sub[1])
    if include_arg_subs:
        sub = hunk_session.arg_substitutions.get(inst_offset)
        if sub:
            text = text.replace(sub[0], sub[1])
    return text


def _struct_field_symbol(inst_offset: int, base_register: str, displacement: int,
                         hunk_session: HunkDisassemblySession,
                         used_structs: set[str] | None) -> str | None:
    reg_types = hunk_session.struct_map.get(inst_offset)
    if not reg_types or base_register not in reg_types:
        return None
    reg_info = reg_types[base_register]
    field_name = reg_info["fields"].get(displacement)
    if not field_name:
        return None
    if used_structs is not None:
        used_structs.add(reg_info["struct"])
    return field_name


def _app_offset_symbol(base_register: str, displacement: int,
                       hunk_session: HunkDisassemblySession) -> str | None:
    base_info = hunk_session.platform.get("initial_base_reg")
    if not (hunk_session.app_offsets and base_info):
        return None
    if base_register != f"a{base_info[0]}":
        return None
    return hunk_session.app_offsets.get(displacement)


def _pc_relative_text(label: str | None, decoded_op, token: str) -> str:
    if label is None:
        return token
    if decoded_op.mode == "pcdisp":
        return f"{label}(pc)"
    index_reg = getattr(decoded_op, "index_reg", None)
    if index_reg is None:
        raise ValueError(f"PC-index operand missing index register: {token!r}")
    prefix = "a" if getattr(decoded_op, "index_is_addr", False) else "d"
    index_size = getattr(decoded_op, "index_size", None)
    if not index_size:
        raise ValueError(f"PC-index operand missing index size: {token!r}")
    return f"{label}(pc,{prefix}{index_reg}.{index_size})"


def _base_disp_text(base_register: str, displacement: int, token: str,
                    decoded_op, symbol: str | None) -> str:
    if symbol is not None:
        if getattr(decoded_op, "mode", None) == "index":
            index_reg = getattr(decoded_op, "index_reg", None)
            if index_reg is None:
                raise ValueError(f"Indexed operand missing index register: {token!r}")
            prefix = "a" if getattr(decoded_op, "index_is_addr", False) else "d"
            index_size = getattr(decoded_op, "index_size", None)
            if not index_size:
                raise ValueError(f"Indexed operand missing index size: {token!r}")
            return f"{symbol}({base_register},{prefix}{index_reg}.{index_size})"
        return f"{symbol}({base_register})"
    return token


def _register_operand(token: str, mode: str, reg: int) -> SemanticOperand:
    return SemanticOperand(
        kind="register",
        text=_register_text(mode, reg, token),
        register=_register_name(mode, reg, token),
    )


def _index_metadata(decoded_op, inst) -> dict[str, object]:
    index_reg = getattr(decoded_op, "index_reg", None)
    if index_reg is None:
        raise ValueError(
            f"Indexed operand missing index register for {_instruction_ref(inst)}")
    index_size = getattr(decoded_op, "index_size", None)
    if not index_size:
        raise ValueError(
            f"Indexed operand missing index size for {_instruction_ref(inst)}")
    prefix = "a" if getattr(decoded_op, "index_is_addr", False) else "d"
    return {
        "index_register": f"{prefix}{index_reg}",
        "index_size": index_size,
    }


def _full_index_metadata(decoded_op, inst) -> dict[str, object]:
    if getattr(decoded_op, "index_suppressed", False):
        metadata = {
            "index_register": None,
            "index_size": None,
            "index_scale": None,
        }
    else:
        metadata = _index_metadata(decoded_op, inst)
        metadata["index_scale"] = getattr(decoded_op, "index_scale", 1)
    metadata["base_register"] = (
        None
        if getattr(decoded_op, "base_suppressed", False)
        else ("pc" if getattr(decoded_op, "mode", None) == "pcindex"
              else _address_base_name(decoded_op.reg))
    )
    metadata["memory_indirect"] = getattr(decoded_op, "memory_indirect", False)
    metadata["postindexed"] = getattr(decoded_op, "postindexed", False)
    metadata["preindexed"] = bool(metadata["memory_indirect"] and not metadata["postindexed"])
    metadata["base_suppressed"] = getattr(decoded_op, "base_suppressed", False)
    metadata["index_suppressed"] = getattr(decoded_op, "index_suppressed", False)
    metadata["base_displacement"] = getattr(decoded_op, "base_displacement", None)
    metadata["outer_displacement"] = getattr(decoded_op, "outer_displacement", None)
    return metadata


def _decoded_operand_specs(inst, hunk_session: HunkDisassemblySession,
                           meta: dict) -> list[tuple[str, object]]:
    decoded = meta["decoded"]
    operand_types = _operand_types_for_inst(inst, meta)
    if operand_types == ():
        return []
    ea_op = decoded["ea_op"]
    dst_op = decoded["dst_op"]
    reg_num = decoded["reg_num"]
    reg_mode = decoded.get("reg_mode")
    secondary_reg = decoded.get("secondary_reg")
    imm_val = decoded.get("imm_val")
    bitfield = decoded.get("bitfield")
    compare_reg = decoded.get("compare_reg")
    update_reg = decoded.get("update_reg")
    control_register = decoded.get("control_register")
    ea_is_source = decoded["ea_is_source"]

    if operand_types == ("label",):
        return [("label", None)]
    if ea_op is None and dst_op is None and reg_num is None and imm_val is None:
        return []
    if operand_types == ("imm", "ea"):
        if imm_val is None or ea_op is None:
            raise ValueError(f"Decoded immediate/ea shape incomplete for {_instruction_ref(inst)}")
        return [("immediate", imm_val), ("decoded", ea_op)]
    if operand_types == ("bf_ea",):
        if ea_op is None or bitfield is None:
            raise ValueError(f"Decoded bitfield ea shape incomplete for {_instruction_ref(inst)}")
        return [("bitfield_ea", (ea_op, bitfield))]
    if operand_types == ("bf_ea", "dn"):
        if ea_op is None or bitfield is None or reg_num is None:
            raise ValueError(
                f"Decoded bitfield ea/register shape incomplete for {_instruction_ref(inst)}")
        return [("bitfield_ea", (ea_op, bitfield)), ("register", ("dn", reg_num))]
    if operand_types == ("dn", "bf_ea"):
        if ea_op is None or bitfield is None or reg_num is None:
            raise ValueError(
                f"Decoded register/bitfield-ea shape incomplete for {_instruction_ref(inst)}")
        return [("register", ("dn", reg_num)), ("bitfield_ea", (ea_op, bitfield))]
    if operand_types == ("dn", "dn", "ea"):
        if compare_reg is None or update_reg is None or ea_op is None:
            raise ValueError(f"Decoded CAS shape incomplete for {_instruction_ref(inst)}")
        return [
            ("register", ("dn", compare_reg)),
            ("register", ("dn", update_reg)),
            ("decoded", ea_op),
        ]
    if operand_types == ("ea", "rn"):
        if ea_op is None or reg_num is None or reg_mode is None:
            raise ValueError(f"Decoded ea/rn shape incomplete for {_instruction_ref(inst)}")
        return [("decoded", ea_op), ("register", (reg_mode, reg_num))]
    if operand_types == ("usp", "an"):
        if reg_num is None:
            raise ValueError(
                f"Decoded usp/address-register shape incomplete for {_instruction_ref(inst)}")
        return [("special_register", "usp"), ("register", ("an", reg_num))]
    if operand_types == ("an", "usp"):
        if reg_num is None:
            raise ValueError(
                f"Decoded address-register/usp shape incomplete for {_instruction_ref(inst)}")
        return [("register", ("an", reg_num)), ("special_register", "usp")]
    if operand_types == ("ctrl_reg", "rn"):
        if control_register is None or reg_num is None or reg_mode is None:
            raise ValueError(f"Decoded control-register/rn shape incomplete for {_instruction_ref(inst)}")
        return [("special_register", control_register), ("register", (reg_mode, reg_num))]
    if operand_types == ("rn", "ctrl_reg"):
        if control_register is None or reg_num is None or reg_mode is None:
            raise ValueError(f"Decoded rn/control-register shape incomplete for {_instruction_ref(inst)}")
        return [("register", (reg_mode, reg_num)), ("special_register", control_register)]
    if operand_types == ("an", "imm"):
        if reg_num is None or imm_val is None:
            raise ValueError(
                f"Decoded address-register/immediate shape incomplete for {_instruction_ref(inst)}")
        return [("register", ("an", reg_num)), ("immediate", imm_val)]
    if operand_types == ("imm", "dn"):
        if imm_val is None or reg_num is None:
            raise ValueError(
                f"Decoded immediate/register shape incomplete for {_instruction_ref(inst)}")
        return [("immediate", imm_val), ("register", ("dn", reg_num))]
    if operand_types == ("dn",):
        if reg_num is None:
            raise ValueError(f"Decoded single-register shape incomplete for {_instruction_ref(inst)}")
        return [("register", ("dn", reg_num))]
    if operand_types == ("rn",):
        if reg_num is None or reg_mode is None:
            raise ValueError(f"Decoded rn shape incomplete for {_instruction_ref(inst)}")
        return [("register", (reg_mode, reg_num))]
    if operand_types == ("an",):
        if reg_num is None:
            raise ValueError(
                f"Decoded single-address-register shape incomplete for {_instruction_ref(inst)}")
        return [("register", ("an", reg_num))]
    if operand_types == ("dn", "dn"):
        if reg_num is None:
            raise ValueError(f"Decoded register/register shape incomplete for {_instruction_ref(inst)}")
        dest = _selected_form_register(inst, meta, 1)
        if dest is None:
            dest = decode_inst_destination(inst, meta["mnemonic"])
        if dest is None:
            raise ValueError(
                f"Unable to resolve destination operand from decode for {_instruction_ref(inst)}")
        return [("register", ("dn", reg_num)), ("register", dest)]
    if operand_types == ("dn", "dn", "imm"):
        if ea_op is None or reg_num is None or secondary_reg is None or imm_val is None:
            raise ValueError(f"Decoded PACK/UNPK register form incomplete for {_instruction_ref(inst)}")
        return [("register", ("dn", reg_num)), ("register", ("dn", secondary_reg)), ("immediate", imm_val)]
    if operand_types == ("dn", "ea"):
        if reg_num is None or ea_op is None:
            raise ValueError(f"Decoded register/ea shape incomplete for {_instruction_ref(inst)}")
        return [("register", ("dn", reg_num)), ("decoded", ea_op)]
    if operand_types == ("dn", "disp"):
        if reg_num is None or ea_op is None:
            raise ValueError(
                f"Decoded register/displacement shape incomplete for {_instruction_ref(inst)}")
        return [("register", ("dn", reg_num)), ("decoded", ea_op)]
    if operand_types == ("ea", "ccr"):
        if ea_op is None:
            raise ValueError(f"Decoded ea/ccr shape incomplete for {_instruction_ref(inst)}")
        return [("decoded", ea_op), ("special_register", "ccr")]
    if operand_types == ("ea", "sr"):
        if ea_op is None:
            raise ValueError(f"Decoded ea/sr shape incomplete for {_instruction_ref(inst)}")
        return [("decoded", ea_op), ("special_register", "sr")]
    if operand_types == ("sr", "ea"):
        if ea_op is None:
            raise ValueError(f"Decoded sr/ea shape incomplete for {_instruction_ref(inst)}")
        return [("special_register", "sr"), ("decoded", ea_op)]
    if operand_types == ("ccr", "ea"):
        if ea_op is None:
            raise ValueError(f"Decoded ccr/ea shape incomplete for {_instruction_ref(inst)}")
        return [("special_register", "ccr"), ("decoded", ea_op)]
    if operand_types == ("ea", "dn"):
        if ea_op is None or reg_num is None:
            raise ValueError(f"Decoded ea/register shape incomplete for {_instruction_ref(inst)}")
        if secondary_reg is not None and secondary_reg != reg_num:
            return [("decoded", ea_op), ("register_pair", (secondary_reg, reg_num))]
        return [("decoded", ea_op), ("register", ("dn", reg_num))]
    if operand_types == ("ea", "dn_pair"):
        if ea_op is None or reg_num is None or secondary_reg is None:
            raise ValueError(
                f"Decoded ea/register-pair shape incomplete for {_instruction_ref(inst)}")
        return [("decoded", ea_op), ("register_pair", (secondary_reg, reg_num))]
    if operand_types == ("disp", "dn"):
        if ea_op is None or reg_num is None:
            raise ValueError(
                f"Decoded displacement/register shape incomplete for {_instruction_ref(inst)}")
        return [("decoded", ea_op), ("register", ("dn", reg_num))]
    if operand_types == ("ea", "an"):
        if ea_op is None or reg_num is None:
            raise ValueError(
                f"Decoded ea/address-register shape incomplete for {_instruction_ref(inst)}")
        return [("decoded", ea_op), ("register", ("an", reg_num))]
    if operand_types == ("predec", "predec"):
        if ea_op is None or dst_op is None:
            raise ValueError(
                f"Decoded predecrement/predecrement shape incomplete for {_instruction_ref(inst)}")
        return [("decoded", ea_op), ("decoded", dst_op)]
    if operand_types == ("predec", "predec", "imm"):
        if ea_op is None or dst_op is None or imm_val is None:
            raise ValueError(
                f"Decoded PACK/UNPK predecrement form incomplete for {_instruction_ref(inst)}")
        return [("decoded", ea_op), ("decoded", dst_op), ("immediate", imm_val)]
    if operand_types == ("postinc", "postinc"):
        if ea_op is None or dst_op is None:
            raise ValueError(f"Decoded postincrement/postincrement shape incomplete for {_instruction_ref(inst)}")
        return [("decoded", ea_op), ("decoded", dst_op)]
    if operand_types in {("absl", "postinc"), ("postinc", "absl"), ("absl", "ind"), ("ind", "absl")}:
        if ea_op is None or dst_op is None:
            raise ValueError(f"Decoded MOVE16 mixed addressing shape incomplete for {_instruction_ref(inst)}")
        return [("decoded", ea_op), ("decoded", dst_op)]
    if dst_op is None and reg_num is None:
        if operand_types == ("reglist", "ea"):
            if ea_op is None:
                raise ValueError(f"Decoded ea operand missing for {_instruction_ref(inst)}")
            return [("reglist", None), ("decoded", ea_op)]
        if operand_types == ("ea", "reglist"):
            if ea_op is None:
                raise ValueError(f"Decoded ea operand missing for {_instruction_ref(inst)}")
            return [("decoded", ea_op), ("reglist", None)]
        if operand_types == ("ea",):
            if ea_op is None:
                raise ValueError(f"Decoded ea operand missing for {_instruction_ref(inst)}")
            return [("decoded", ea_op)]
        if operand_types == ("imm",):
            if imm_val is None:
                raise ValueError(f"Decoded immediate operand missing for {_instruction_ref(inst)}")
            return [("immediate", imm_val)]
        if ea_op is not None and imm_val is not None:
            return [("immediate", imm_val), ("decoded", ea_op)]
        if ea_op is not None:
            return [("decoded", ea_op)]
        if imm_val is not None:
            return [("immediate", imm_val)]
        raise ValueError(
            f"Unsupported single-operand instruction shape for {_instruction_ref(inst)}")
    if operand_types == ("dn", "label"):
        return [("register", ("dn", reg_num)), ("label", None)]
    if operand_types == ("rn", "ea"):
        if ea_op is None or reg_num is None or reg_mode is None or ea_is_source is None:
            raise ValueError(f"Decoded rn/ea shape incomplete for {_instruction_ref(inst)}")
        reg_spec = ("register", (reg_mode, reg_num))
        return [reg_spec, ("decoded", ea_op)] if ea_is_source else [("decoded", ea_op), reg_spec]
    if ea_is_source is not None and ea_op is not None and reg_num is not None:
        reg_spec = ("register", ("dn", reg_num))
        return [("decoded", ea_op), reg_spec] if ea_is_source else [reg_spec, ("decoded", ea_op)]

    if ea_op is not None:
        first = ("decoded", ea_op)
    elif imm_val is not None:
        first = ("immediate", imm_val)
    else:
        raise ValueError(
            f"Unable to resolve first operand from decode for {_instruction_ref(inst)}")

    if dst_op is not None:
        second = ("decoded", dst_op)
    else:
        dest = decode_inst_destination(inst, meta["mnemonic"])
        if dest is None:
            raise ValueError(
                f"Unable to resolve destination operand from decode for {_instruction_ref(inst)}")
        second = ("register", dest)
    return [first, second]


def _operand_text_slots(inst, operand_count: int) -> list[str]:
    if operand_count == 0:
        return []
    if inst.operand_texts is None:
        raise ValueError(
            f"Instruction at ${inst.offset:06x} is missing operand_texts")
    tokens = [token for token in inst.operand_texts if token]
    if len(tokens) != operand_count:
        raise ValueError(
            f"Operand text count mismatch for {_instruction_ref(inst)}: "
            f"decoded {operand_count}, text {len(tokens)}")
    return tokens


def _simple_semantic_from_node(inst, node, spec_type: str, spec_value,
                               operand_index: int,
                               hunk_session: HunkDisassemblySession,
                               meta: dict,
                               used_structs: set[str] | None,
                               include_arg_subs: bool) -> SemanticOperand | None:
    flow_type = runtime_m68k_analysis.FLOW_TYPES[meta["mnemonic"]]
    labels = hunk_session.labels

    if spec_type == "register" and node.kind == "register":
        mode, reg = spec_value
        expected = f"{'a' if mode == 'an' else 'd'}{reg}"
        if not _same_register_name(expected, node.register):
            raise ValueError(
                f"Typed register mismatch for {_instruction_ref(inst)}: "
                f"decoded {expected}, node {node.register}")
        return SemanticOperand(kind="register", text=node.text.lower(), register=node.register)

    if spec_type == "special_register" and node.kind == "special_register":
        if str(spec_value) != node.register:
            raise ValueError(
                f"Typed special-register mismatch for {_instruction_ref(inst)}: "
                f"decoded {spec_value}, node {node.register}")
        return SemanticOperand(kind="register", text=node.text.lower(), register=node.register)

    if spec_type == "reglist" and node.kind == "register_list":
        return SemanticOperand(
            kind="register_list",
            text=node.text,
            metadata=dict(node.metadata),
        )

    if spec_type == "register_pair" and node.kind == "register_pair":
        expected = [f"d{spec_value[0]}", f"d{spec_value[1]}"]
        actual = node.metadata.get("registers")
        if actual != expected:
            raise ValueError(
                f"Typed register-pair mismatch for {_instruction_ref(inst)}: "
                f"decoded {expected}, node {actual}")
        return SemanticOperand(
            kind="register_pair",
            text=node.text.lower(),
            metadata={"registers": expected},
        )

    if spec_type == "immediate" and node.kind == "immediate":
        value = spec_value
        same_encoded_value = False
        if node.value is not None and value is not None:
            for bits in (8, 16, 32):
                mask = (1 << bits) - 1
                if (node.value & mask) == value:
                    same_encoded_value = True
                    break
        if node.value != value and not same_encoded_value:
            raise ValueError(
                f"Typed immediate mismatch for {_instruction_ref(inst)}: "
                f"decoded {value}, node {node.value}")
        target = _reloc_target(inst, hunk_session, value)
        label = labels.get(target) if target is not None else None
        text = f"#{label}" if label is not None else node.text
        text = _apply_instruction_text_substitutions(
            text, inst.offset, hunk_session, include_arg_subs)
        return SemanticOperand(
            kind="immediate_symbol" if label is not None else "immediate",
            text=text,
            value=value,
            target_addr=target,
            metadata={"symbol": label} if label is not None else {},
        )

    if (spec_type == "immediate"
            and node.kind == "branch_target"
            and flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL)):
        target_addr = node.target
        if target_addr is None:
            raise ValueError(f"Typed branch target missing for {_instruction_ref(inst)}")
        label = labels.get(target_addr)
        text = label if label is not None else node.text
        return SemanticOperand(
            kind="call_target" if flow_type == _FLOW_CALL else "branch_target",
            text=text,
            value=target_addr,
            target_addr=target_addr,
            metadata={"symbol": label} if label is not None else {},
        )

    if spec_type == "label" and node.kind == "branch_target":
        target_addr = node.target
        if target_addr is None:
            raise ValueError(f"Typed branch target missing for {_instruction_ref(inst)}")
        label = labels.get(target_addr)
        text = label if label is not None else node.text
        return SemanticOperand(
            kind="call_target" if flow_type == _FLOW_CALL else "branch_target",
            text=text,
            value=target_addr,
            target_addr=target_addr,
            metadata={"symbol": label} if label is not None else {},
        )

    if spec_type == "bitfield_ea" and node.kind == "bitfield_ea":
        decoded_op, bitfield = spec_value
        base_node = node.metadata.get("base_node")
        if base_node is None:
            raise ValueError(f"Typed bitfield operand missing base node for {_instruction_ref(inst)}")
        base = _simple_semantic_from_node(
            inst, base_node, "decoded", decoded_op, operand_index,
            hunk_session, meta, used_structs, include_arg_subs)
        if base is None:
            raise ValueError(f"Typed bitfield base node did not decode for {_instruction_ref(inst)}")
        for key in ("offset_is_register", "offset_value", "width_is_register", "width_value"):
            if node.metadata.get(key) != bitfield.get(key):
                raise ValueError(
                    f"Typed bitfield operand mismatch for {_instruction_ref(inst)}: "
                    f"{key} decoded {bitfield.get(key)}, node {node.metadata.get(key)}")
        metadata = dict(base.metadata)
        metadata["bitfield"] = bitfield
        return SemanticOperand(
            kind="bitfield_ea",
            text=node.text,
            value=base.value,
            register=base.register,
            base_register=base.base_register,
            displacement=base.displacement,
            target_addr=base.target_addr,
            metadata=metadata,
        )

    if spec_type == "decoded":
        decoded_op = spec_value
        op_mode = getattr(decoded_op, "mode", None)
        op_value = getattr(decoded_op, "value", None)
        metadata: dict[str, object] = {}
        kind = "text"
        value = None
        register = None
        base_register = None
        displacement = None
        target_addr = None
        text = node.text

        if op_mode in ("dn", "dreg") and node.kind == "register":
            expected = f"d{decoded_op.reg}"
            if node.register != expected:
                raise ValueError(
                    f"Typed register mismatch for {_instruction_ref(inst)}: "
                    f"decoded {expected}, node {node.register}")
            kind = "register"
            register = node.register
            text = node.text.lower()
        elif op_mode in ("an", "areg") and node.kind == "register":
            expected = f"a{decoded_op.reg}"
            if not _same_register_name(expected, node.register):
                raise ValueError(
                    f"Typed register mismatch for {_instruction_ref(inst)}: "
                    f"decoded {expected}, node {node.register}")
            kind = "register"
            register = node.register
            text = node.text.lower()
        elif op_mode == "imm" and node.kind == "immediate":
            value = op_value
            same_encoded_value = False
            if node.value is not None and value is not None:
                for bits in (8, 16, 32):
                    mask = (1 << bits) - 1
                    if (node.value & mask) == value:
                        same_encoded_value = True
                        break
            if node.value != value and not same_encoded_value:
                raise ValueError(
                    f"Typed immediate mismatch for {_instruction_ref(inst)}: "
                    f"decoded {value}, node {node.value}")
            target = _reloc_target(inst, hunk_session, value) if value is not None else None
            label = labels.get(target) if target is not None else None
            if label is not None:
                kind = "immediate_symbol"
                target_addr = target
                metadata["symbol"] = label
                text = f"#{label}"
            else:
                kind = "immediate"
        elif op_mode == "ind" and node.kind == "indirect":
            base_register = _address_base_name(decoded_op.reg)
            if node.metadata.get("base_register") != base_register:
                raise ValueError(
                    f"Typed indirect mismatch for {_instruction_ref(inst)}: "
                    f"decoded {base_register}, node {node.metadata.get('base_register')}")
            kind = "indirect"
        elif op_mode == "postinc" and node.kind == "postincrement":
            base_register = _address_base_name(decoded_op.reg)
            if node.metadata.get("base_register") != base_register:
                raise ValueError(
                    f"Typed postincrement mismatch for {_instruction_ref(inst)}: "
                    f"decoded {base_register}, node {node.metadata.get('base_register')}")
            kind = "postincrement"
        elif op_mode == "predec" and node.kind == "predecrement":
            base_register = _address_base_name(decoded_op.reg)
            if node.metadata.get("base_register") != base_register:
                raise ValueError(
                    f"Typed predecrement mismatch for {_instruction_ref(inst)}: "
                    f"decoded {base_register}, node {node.metadata.get('base_register')}")
            kind = "predecrement"
        elif op_mode == "disp" and node.kind == "base_displacement":
            base_register = _address_base_name(decoded_op.reg)
            displacement = op_value
            if node.metadata.get("base_register") != base_register:
                raise ValueError(
                    f"Typed base displacement mismatch for {_instruction_ref(inst)}: "
                    f"decoded {base_register}, node {node.metadata.get('base_register')}")
            if node.metadata.get("displacement") != displacement:
                raise ValueError(
                    f"Typed base displacement mismatch for {_instruction_ref(inst)}: "
                    f"decoded {displacement}, node {node.metadata.get('displacement')}")
            value = displacement
            symbol = (_struct_field_symbol(inst.offset, base_register, displacement,
                                           hunk_session, used_structs)
                      or _app_offset_symbol(base_register, displacement, hunk_session))
            if symbol is not None:
                kind = "base_displacement_symbol"
                metadata["symbol"] = symbol
            else:
                kind = "base_displacement"
            text = _base_disp_text(base_register, displacement, node.text, decoded_op, symbol)
        elif op_mode in ("absw", "absl") and node.kind == "absolute_target":
            value = _normalized_absolute_value(decoded_op)
            target_addr = value
            if node.target != target_addr:
                raise ValueError(
                    f"Typed absolute target mismatch for {_instruction_ref(inst)}: "
                    f"decoded {target_addr}, node {node.target}")
            label = labels.get(target_addr)
            text = label if label is not None else node.text
            if flow_type == _FLOW_CALL and operand_index == 0:
                kind = "call_target"
            elif flow_type in (_FLOW_BRANCH, _FLOW_JUMP) and operand_index == 0:
                kind = "branch_target"
            else:
                kind = "absolute_target"
        elif op_mode == "pcdisp" and node.kind == "pc_relative_target":
            target_addr = op_value
            value = op_value
            if node.target != target_addr:
                raise ValueError(
                    f"Typed PC-relative target mismatch for {_instruction_ref(inst)}: "
                    f"decoded {target_addr}, node {node.target}")
            label = labels.get(target_addr)
            text = _pc_relative_text(label, decoded_op, node.text)
            if flow_type == _FLOW_CALL and operand_index == 0:
                kind = "call_target"
            elif flow_type in (_FLOW_BRANCH, _FLOW_JUMP) and operand_index == 0:
                kind = "branch_target"
            else:
                kind = "pc_relative_target"
        elif op_mode == "index" and node.kind == "indexed":
            base_register = _address_base_name(decoded_op.reg)
            displacement = op_value
            if node.metadata.get("base_register") != base_register:
                raise ValueError(
                    f"Typed indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {base_register}, node {node.metadata.get('base_register')}")
            if node.metadata.get("displacement") != displacement:
                raise ValueError(
                    f"Typed indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {displacement}, node {node.metadata.get('displacement')}")
            metadata.update(_index_metadata(decoded_op, inst))
            if node.metadata.get("index_register") != metadata["index_register"]:
                raise ValueError(
                    f"Typed indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {metadata['index_register']}, node {node.metadata.get('index_register')}")
            if node.metadata.get("index_size") != metadata["index_size"]:
                raise ValueError(
                    f"Typed indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {metadata['index_size']}, node {node.metadata.get('index_size')}")
            value = displacement
            symbol = (_struct_field_symbol(inst.offset, base_register, displacement,
                                           hunk_session, used_structs)
                      or _app_offset_symbol(base_register, displacement, hunk_session))
            kind = "base_displacement_symbol" if symbol is not None else "indexed"
            if symbol is not None:
                metadata["symbol"] = symbol
            text = _base_disp_text(base_register, displacement, node.text, decoded_op, symbol)
        elif op_mode == "index" and node.kind == "memory_indirect_indexed":
            base_register = _address_base_name(decoded_op.reg)
            metadata.update(_full_index_metadata(decoded_op, inst))
            if node.metadata != metadata:
                raise ValueError(
                    f"Typed full indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {metadata}, node {node.metadata}")
            displacement = metadata["base_displacement"]
            value = displacement
            kind = "memory_indirect_indexed"
            text = node.text
        elif op_mode == "pcindex" and node.kind == "pc_relative_indexed":
            target_addr = op_value
            if node.target != target_addr:
                raise ValueError(
                    f"Typed PC-indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {target_addr}, node {node.target}")
            metadata.update(_index_metadata(decoded_op, inst))
            if node.metadata.get("index_register") != metadata["index_register"]:
                raise ValueError(
                    f"Typed PC-indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {metadata['index_register']}, node {node.metadata.get('index_register')}")
            if node.metadata.get("index_size") != metadata["index_size"]:
                raise ValueError(
                    f"Typed PC-indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {metadata['index_size']}, node {node.metadata.get('index_size')}")
            value = op_value
            label = labels.get(target_addr)
            text = _pc_relative_text(label, decoded_op, node.text)
            kind = "pc_relative_indexed"
        elif op_mode == "pcindex" and node.kind == "pc_memory_indirect_indexed":
            target_addr = op_value
            if node.target != target_addr:
                raise ValueError(
                    f"Typed PC full indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {target_addr}, node {node.target}")
            metadata.update(_full_index_metadata(decoded_op, inst))
            if node.metadata != metadata:
                raise ValueError(
                    f"Typed PC full indexed operand mismatch for {_instruction_ref(inst)}: "
                    f"decoded {metadata}, node {node.metadata}")
            value = op_value
            kind = "pc_memory_indirect_indexed"
            text = node.text
        else:
            return None

        text = _apply_instruction_text_substitutions(
            text, inst.offset, hunk_session, include_arg_subs)
        return SemanticOperand(
            kind=kind,
            text=text,
            value=value,
            register=register,
            base_register=base_register,
            displacement=displacement,
            target_addr=target_addr,
            metadata=metadata,
        )

    return None


def _build_decoded_semantic_operand(inst, token: str, spec_type: str, spec_value,
                                    operand_index: int,
                                    hunk_session: HunkDisassemblySession,
                                    meta: dict,
                                    used_structs: set[str] | None,
                                    include_arg_subs: bool) -> SemanticOperand:
    flow_type = runtime_m68k_analysis.FLOW_TYPES[meta["mnemonic"]]
    branch_target = None
    if flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL):
        branch_target = extract_branch_target(inst, inst.offset)
    labels = hunk_session.labels

    if spec_type == "register":
        mode, reg = spec_value
        return _register_operand(token, mode, reg)

    if spec_type == "bitfield_ea":
        decoded_op, bitfield = spec_value
        base = _build_decoded_semantic_operand(
            inst, token, "decoded", decoded_op, operand_index,
            hunk_session, meta, used_structs, include_arg_subs)
        metadata = dict(base.metadata)
        metadata["bitfield"] = bitfield
        return SemanticOperand(
            kind="bitfield_ea",
            text=base.text,
            value=base.value,
            register=base.register,
            base_register=base.base_register,
            displacement=base.displacement,
            target_addr=base.target_addr,
            metadata=metadata,
        )

    if spec_type == "special_register":
        return SemanticOperand(
            kind="register",
            text=token.lower(),
            register=str(spec_value),
        )

    if spec_type == "register_pair":
        hi, lo = spec_value
        return SemanticOperand(
            kind="register_pair",
            text=token.lower(),
            metadata={"registers": [f"d{hi}", f"d{lo}"]},
        )

    if spec_type == "reglist":
        return SemanticOperand(kind="register_list", text=token)

    if spec_type == "label":
        if branch_target is None:
            raise ValueError(
                f"Decoded label operand missing branch target for {_instruction_ref(inst)}")
        label = labels.get(branch_target)
        text = label if label is not None else token
        return SemanticOperand(
            kind="call_target" if flow_type == _FLOW_CALL else "branch_target",
            text=text,
            value=branch_target,
            target_addr=branch_target,
            metadata={"symbol": label} if label is not None else {},
        )

    if spec_type == "immediate":
        value = spec_value
        target = branch_target if flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL) else _reloc_target(
            inst, hunk_session, value)
        label = labels.get(target) if target is not None else None
        if flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL) and label is not None:
            text = label
            kind = "call_target" if flow_type == _FLOW_CALL else "branch_target"
        else:
            text = f"#{label}" if label is not None else token
            kind = "immediate_symbol" if label is not None else "immediate"
        text = _apply_instruction_text_substitutions(
            text, inst.offset, hunk_session, include_arg_subs)
        return SemanticOperand(
            kind=kind,
            text=text,
            value=value,
            target_addr=target,
            metadata={"symbol": label} if label is not None else {},
        )

    decoded_op = spec_value
    op_mode = getattr(decoded_op, "mode", None)
    op_value = getattr(decoded_op, "value", None)
    metadata: dict[str, object] = {}
    kind = "text"
    value = None
    register = None
    base_register = None
    displacement = None
    target_addr = None
    text = token

    if op_mode in ("dn", "dreg"):
        register = _register_name("dn", decoded_op.reg, token)
        kind = "register"
        text = _register_text("dn", decoded_op.reg, token)
    elif op_mode in ("an", "areg"):
        register = _register_name("an", decoded_op.reg, token)
        kind = "register"
        text = _register_text("an", decoded_op.reg, token)
    elif op_mode == "imm":
        value = op_value
        target = _reloc_target(inst, hunk_session, value) if value is not None else None
        label = labels.get(target) if target is not None else None
        if label is not None:
            kind = "immediate_symbol"
            target_addr = target
            metadata["symbol"] = label
            text = f"#{label}"
        else:
            kind = "immediate"
    elif op_mode in ("absw", "absl"):
        value = _normalized_absolute_value(decoded_op)
        target_addr = value
        label = labels.get(target_addr)
        text = label if label is not None else token
        if flow_type == _FLOW_CALL and operand_index == 0:
            kind = "call_target"
        elif flow_type in (_FLOW_BRANCH, _FLOW_JUMP) and operand_index == 0:
            kind = "branch_target"
        else:
            kind = "absolute_target"
    elif op_mode in ("pcdisp", "pcindex"):
        target_addr = op_value
        value = op_value
        label = labels.get(target_addr)
        text = _pc_relative_text(label, decoded_op, token)
        if flow_type == _FLOW_CALL and operand_index == 0:
            kind = "call_target"
        elif flow_type in (_FLOW_BRANCH, _FLOW_JUMP) and operand_index == 0:
            kind = "branch_target"
        elif op_mode == "pcindex" and getattr(decoded_op, "memory_indirect", False):
            metadata.update(_full_index_metadata(decoded_op, inst))
            kind = "pc_memory_indirect_indexed"
        elif op_mode == "pcindex":
            kind = "pc_relative_indexed"
        else:
            kind = "pc_relative_target"
    elif op_mode == "disp":
        base_register = f"a{decoded_op.reg}"
        displacement = op_value
        value = op_value
        symbol = (_struct_field_symbol(inst.offset, base_register, displacement,
                                       hunk_session, used_structs)
                  or _app_offset_symbol(base_register, displacement, hunk_session))
        if symbol is not None:
            kind = "base_displacement_symbol"
            metadata["symbol"] = symbol
        else:
            kind = "base_displacement"
        text = _base_disp_text(base_register, displacement, token, decoded_op, symbol)
    elif op_mode == "ind":
        base_register = f"a{decoded_op.reg}"
        kind = "indirect"
    elif op_mode == "postinc":
        base_register = f"a{decoded_op.reg}"
        kind = "postincrement"
    elif op_mode == "predec":
        base_register = f"a{decoded_op.reg}"
        kind = "predecrement"
    elif op_mode == "index":
        base_register = f"a{decoded_op.reg}"
        displacement = op_value
        value = op_value
        if getattr(decoded_op, "memory_indirect", False):
            metadata.update(_full_index_metadata(decoded_op, inst))
            kind = "memory_indirect_indexed"
        else:
            metadata.update(_index_metadata(decoded_op, inst))
            kind = "indexed"
    else:
        raise ValueError(
            f"Unsupported decoded operand mode {op_mode!r} in {_instruction_ref(inst)}")

    if (flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL)
            and operand_index == 0
            and branch_target is not None):
        target_addr = branch_target
        value = branch_target if value is None else value
        label = labels.get(branch_target)
        if label is not None and op_mode not in ("pcdisp", "pcindex"):
            text = label
        kind = "call_target" if flow_type == _FLOW_CALL else "branch_target"

    text = _apply_instruction_text_substitutions(
        text, inst.offset, hunk_session, include_arg_subs)
    return SemanticOperand(
        kind=kind,
        text=text,
        value=value,
        register=register,
        base_register=base_register,
        displacement=displacement,
        target_addr=target_addr,
        metadata=metadata,
    )


def build_instruction_semantic_operands(
        inst, hunk_session: HunkDisassemblySession,
        used_structs: set[str] | None = None,
        include_arg_subs: bool = True
) -> tuple[SemanticOperand, ...]:
    meta = decode_inst_for_emit(inst)
    specs = _decoded_operand_specs(inst, hunk_session, meta)
    nodes = list(inst.operand_nodes or ())
    tokens = _operand_text_slots(inst, len(specs))

    return tuple(
        (_simple_semantic_from_node(
            inst, nodes[idx], spec_type, spec_value, idx,
            hunk_session, meta, used_structs, include_arg_subs,
        ) if idx < len(nodes) else None)
        or _build_decoded_semantic_operand(
            inst,
            token,
            spec_type,
            spec_value,
            idx,
            hunk_session,
            meta,
            used_structs,
            include_arg_subs,
        )
        for idx, (token, (spec_type, spec_value)) in enumerate(zip(tokens, specs))
    )
