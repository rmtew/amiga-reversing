from __future__ import annotations
"""Build semantic operands from decoded instruction operands."""

from m68k.kb_util import decode_destination
from m68k.m68k_executor import _extract_branch_target

from disasm.decode import decode_inst_for_emit
from disasm.types import HunkDisassemblySession, SemanticOperand


def _split_operand_tokens(operands: str) -> list[str]:
    tokens = []
    start = 0
    depth = 0
    for idx, ch in enumerate(operands):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            tokens.append(operands[start:idx].strip())
            start = idx + 1
    tokens.append(operands[start:].strip())
    return tokens


def build_semantic_operands(operand_text: str) -> tuple[SemanticOperand, ...]:
    if not operand_text:
        return ()
    return tuple(
        SemanticOperand(kind="text", text=token.strip())
        for token in _split_operand_tokens(operand_text)
        if token.strip()
    )


def _normalized_absolute_value(decoded_op) -> int | None:
    if decoded_op is None or getattr(decoded_op, "value", None) is None:
        return None
    if decoded_op.mode == "absw":
        return decoded_op.value & 0xFFFF
    if decoded_op.mode == "absl":
        return decoded_op.value
    return None


def _reloc_target(inst, hunk_session: HunkDisassemblySession, value: int) -> int | None:
    for ext_off in range(inst.offset + hunk_session.kb.opword_bytes,
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


def _index_metadata(decoded_op, inst_text: str, token: str) -> dict[str, object]:
    index_reg = getattr(decoded_op, "index_reg", None)
    if index_reg is None:
        raise ValueError(f"Indexed operand missing index register: {inst_text!r}")
    index_size = getattr(decoded_op, "index_size", None)
    if not index_size:
        raise ValueError(f"Indexed operand missing index size: {inst_text!r}")
    prefix = "a" if getattr(decoded_op, "index_is_addr", False) else "d"
    return {
        "index_register": f"{prefix}{index_reg}",
        "index_size": index_size,
    }


def _decoded_operand_specs(inst, hunk_session: HunkDisassemblySession,
                           meta: dict) -> list[tuple[str, object]]:
    decoded = meta["decoded"]
    ea_op = decoded["ea_op"]
    dst_op = decoded["dst_op"]
    reg_num = decoded["reg_num"]
    imm_val = decoded.get("imm_val")
    ea_is_source = decoded["ea_is_source"]

    if ea_op is None and dst_op is None and reg_num is None and imm_val is None:
        return []
    if dst_op is None and reg_num is None:
        if ea_op is not None:
            return [("decoded", ea_op)]
        if imm_val is not None:
            return [("immediate", imm_val)]
        raise ValueError(f"Unsupported single-operand instruction shape: {inst.text!r}")

    if ea_is_source is not None and ea_op is not None and reg_num is not None:
        reg_spec = ("register", ("dn", reg_num))
        return [("decoded", ea_op), reg_spec] if ea_is_source else [reg_spec, ("decoded", ea_op)]

    if ea_op is not None:
        first = ("decoded", ea_op)
    elif imm_val is not None:
        first = ("immediate", imm_val)
    else:
        raise ValueError(f"Unable to resolve first operand from decode: {inst.text!r}")

    if dst_op is not None:
        second = ("decoded", dst_op)
    else:
        dest = decode_destination(inst.raw, meta["inst_kb"], hunk_session.kb.meta,
                                  meta["size"], inst.offset)
        if dest is None:
            raise ValueError(f"Unable to resolve destination operand from decode: {inst.text!r}")
        second = ("register", dest)
    return [first, second]


def _operand_text_slots(inst_text: str, operand_count: int) -> list[str]:
    parts = inst_text.strip().split(None, 1)
    if operand_count == 0:
        return []
    if len(parts) < 2:
        raise ValueError(f"Decoded operands missing text slots for {inst_text!r}")
    tokens = [token for token in _split_operand_tokens(parts[1]) if token]
    if len(tokens) != operand_count:
        raise ValueError(
            f"Operand text count mismatch for {inst_text!r}: "
            f"decoded {operand_count}, text {len(tokens)}")
    return tokens


def _build_decoded_semantic_operand(inst, token: str, spec_type: str, spec_value,
                                    operand_index: int,
                                    hunk_session: HunkDisassemblySession,
                                    meta: dict,
                                    used_structs: set[str] | None,
                                    include_arg_subs: bool) -> SemanticOperand:
    flow_type = meta["inst_kb"].get("pc_effects", {}).get("flow", {}).get("type")
    branch_target = _extract_branch_target(inst, inst.offset)
    labels = hunk_session.labels

    if spec_type == "register":
        mode, reg = spec_value
        return _register_operand(token, mode, reg)

    if spec_type == "immediate":
        value = spec_value
        target = branch_target if flow_type in ("branch", "jump", "call") else _reloc_target(
            inst, hunk_session, value)
        label = labels.get(target) if target is not None else None
        if flow_type in ("branch", "jump", "call") and label is not None:
            text = label
            kind = "call_target" if flow_type == "call" else "branch_target"
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
        if flow_type == "call" and operand_index == 0:
            kind = "call_target"
        elif flow_type in ("branch", "jump") and operand_index == 0:
            kind = "branch_target"
        else:
            kind = "absolute_target"
    elif op_mode in ("pcdisp", "pcindex"):
        target_addr = op_value
        value = op_value
        label = labels.get(target_addr)
        text = _pc_relative_text(label, decoded_op, token)
        if flow_type == "call" and operand_index == 0:
            kind = "call_target"
        elif flow_type in ("branch", "jump") and operand_index == 0:
            kind = "branch_target"
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
    elif op_mode == "index":
        base_register = f"a{decoded_op.reg}"
        displacement = op_value
        value = op_value
        metadata.update(_index_metadata(decoded_op, inst.text, token))
        kind = "indexed"
    else:
        raise ValueError(f"Unsupported decoded operand mode {op_mode!r} in {inst.text!r}")

    if (flow_type in ("branch", "jump", "call")
            and operand_index == 0
            and branch_target is not None):
        target_addr = branch_target
        value = branch_target if value is None else value
        label = labels.get(branch_target)
        if label is not None and op_mode not in ("pcdisp", "pcindex"):
            text = label
        kind = "call_target" if flow_type == "call" else "branch_target"

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
    meta = decode_inst_for_emit(inst, hunk_session.kb)
    specs = _decoded_operand_specs(inst, hunk_session, meta)
    tokens = _operand_text_slots(inst.text, len(specs))

    return tuple(
        _build_decoded_semantic_operand(
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
