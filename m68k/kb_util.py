"""Shared KB utilities for M68K analysis tools.

Provides common helpers used across jump_tables, os_calls, name_entities,
subroutine_scan, and build_entities. Single source of truth for KB access
patterns and encoding field extraction.
"""

import struct

from .decode_errors import DecodeError
from .m68k_executor import (_load_kb, _find_kb_entry,
                           _decode_ea, Operand, _xf)


class KB:
    """Cached KB access with common lookups pre-resolved."""

    def __init__(self):
        self.by_name, _, self.meta = _load_kb()
        self.cc_defs = self.meta["cc_test_definitions"]
        self.cc_aliases = self.meta["cc_aliases"]
        self.opword_bytes = self.meta["opword_bytes"]
        self.ea_enc = self.meta["ea_mode_encoding"]
        self.size_bytes = self.meta["size_byte_count"]
        self.align_mask = self.opword_bytes - 1
        # EA modes that use an address register as base for memory access
        # without side effects.  Derived from ea_mode_encoding: modes that
        # encode a register in the EA field (mode < 7) and are not register-
        # direct (dn/an) or auto-modify (postinc/predec).
        _direct = {"dn", "an"}
        _automod = {"postinc", "predec"}
        self.reg_indirect_modes = frozenset(
            name for name, (mode_val, reg_val) in self.ea_enc.items()
            if reg_val is None  # uses register field from EA
            and name not in _direct
            and name not in _automod)
        # Address size derived from RTS sp_effects: the number of bytes
        # popped by RTS defines the address width.
        rts = self.find("RTS")
        if rts is None:
            raise KeyError("KB missing RTS instruction")
        self.rts_sp_inc = sum(
            e["bytes"] for e in rts.get("sp_effects", [])
            if e.get("action") == "increment")
        if not self.rts_sp_inc:
            raise ValueError("KB RTS has no sp_effects increment")
        self.addr_size = next(
            (k for k, v in self.size_bytes.items()
             if v == self.rts_sp_inc), None)
        if self.addr_size is None:
            raise ValueError(
                f"KB size_byte_count has no entry for "
                f"{self.rts_sp_inc} bytes (RTS pop size)")
        # Address mask derived from address size (e.g. 4 bytes -> 0xFFFFFFFF)
        self.addr_mask = (1 << (self.rts_sp_inc * 8)) - 1

    def find(self, mnemonic: str) -> dict | None:
        """Look up KB entry for a mnemonic (handles CC families)."""
        return _find_kb_entry(self.by_name, mnemonic,
                              self.cc_defs, self.cc_aliases)

    def instruction_kb(self, inst) -> dict:
        """Look up the exact KB entry named on an Instruction."""
        if not inst.kb_mnemonic:
            raise KeyError(
                f"Instruction at ${inst.offset:06x} is missing kb_mnemonic")
        ikb = self.find(inst.kb_mnemonic)
        if ikb is None:
            raise KeyError(
                f"KB missing instruction entry for {inst.kb_mnemonic!r} "
                f"at ${inst.offset:06x}")
        return ikb

    def flow_type(self, inst) -> tuple[str | None, bool]:
        """Get (flow_type, conditional) for a decoded instruction.

        Returns (None, False) if instruction has no flow effect or is
        not in KB.
        """
        ikb = self.instruction_kb(inst)
        pc_effects = ikb.get("pc_effects")
        if pc_effects is None:
            return None, False
        flow = pc_effects["flow"]
        return flow["type"], flow.get("conditional", False)

    def ea_field_spec(self, inst_kb: dict) -> tuple | None:
        """Extract (mode_field, reg_field) from KB encoding for EA instructions.

        Returns ((hi, lo, width), (hi, lo, width)) for source MODE and
        REGISTER fields, or None.
        """
        encodings = inst_kb.get("encodings", [])
        if not encodings:
            return None
        fields = encodings[0].get("fields", [])
        mode_f = reg_f = None
        for f in fields:
            if f["name"] == "MODE":
                mode_f = (f["bit_hi"], f["bit_lo"],
                          f["bit_hi"] - f["bit_lo"] + 1)
            elif f["name"] == "REGISTER" and f["bit_hi"] <= 5:
                reg_f = (f["bit_hi"], f["bit_lo"],
                         f["bit_hi"] - f["bit_lo"] + 1)
        if mode_f and reg_f:
            return mode_f, reg_f
        return None

    def dst_reg_field(self, inst_kb: dict) -> tuple | None:
        """Extract destination REGISTER field (higher bits) for MOVEA etc.

        For instructions with two REGISTER fields, returns the one at
        higher bit positions.
        """
        encodings = inst_kb.get("encodings", [])
        if not encodings:
            return None
        fields = encodings[0].get("fields", [])
        reg_fields = [f for f in fields if f["name"] == "REGISTER"]
        if len(reg_fields) < 2:
            return None
        reg_fields.sort(key=lambda f: f["bit_lo"], reverse=True)
        dst = reg_fields[0]
        return (dst["bit_hi"], dst["bit_lo"],
                dst["bit_hi"] - dst["bit_lo"] + 1)


def xf(opcode: int, field: tuple) -> int:
    """Extract a bit field from an opcode. field = (bit_hi, bit_lo, width)."""
    return (opcode >> field[1]) & ((1 << field[2]) - 1)


def _encoding_matches_opcode(opcode: int, encoding: dict) -> bool:
    for field in encoding.get("fields", []):
        name = field["name"]
        if name not in {"0", "1"}:
            continue
        width = field["bit_hi"] - field["bit_lo"] + 1
        value = (opcode >> field["bit_lo"]) & ((1 << width) - 1)
        expected = 0 if name == "0" else (1 << width) - 1
        if value != expected:
            return False
    return True


def select_encoding_index(inst_kb: dict, opcode: int) -> int:
    encodings = inst_kb.get("encodings", [])
    if not encodings:
        raise ValueError(f"KB entry {inst_kb.get('mnemonic', '<unknown>')} has no encodings")
    forms = inst_kb.get("forms") or []
    form_operand_types = [
        tuple(operand.get("type") for operand in (form.get("operands") or []))
        for form in forms
    ]
    if form_operand_types == [("dn", "dn"), ("imm", "dn"), ("ea",)]:
        return 1 if ((opcode >> 6) & 0b11) == 0b11 else 0
    primary_count = min(len(encodings), len(forms)) if forms else len(encodings)
    matches = [
        index
        for index, encoding in enumerate(encodings[:primary_count])
        if _encoding_matches_opcode(opcode, encoding)
    ]
    if not matches:
        literal_encodings = [
            index
            for index, encoding in enumerate(encodings)
            if any(field["name"] in {"0", "1"} for field in encoding.get("fields", []))
        ]
        matches = [
            index
            for index in literal_encodings
            if _encoding_matches_opcode(opcode, encodings[index])
        ]
    if len(matches) > 1:
        literal_counts = {
            index: sum(
                1
                for field in encodings[index].get("fields", [])
                if field["name"] in {"0", "1"}
            )
            for index in matches
        }
        max_literals = max(literal_counts.values())
        matches = [index for index in matches if literal_counts[index] == max_literals]
    if len(matches) != 1:
        raise ValueError(
            f"KB encoding match count {len(matches)} for opcode ${opcode:04x} "
            f"in {inst_kb.get('mnemonic', '<unknown>')}")
    return matches[0]


def select_encoding_fields(inst_kb: dict, opcode: int) -> list[dict]:
    return inst_kb["encodings"][select_encoding_index(inst_kb, opcode)].get("fields", [])


def select_operand_types(inst_kb: dict, opcode: int) -> tuple[str, ...]:
    forms = inst_kb.get("forms") or []
    if not forms:
        return ()
    form_operand_types = [
        tuple(operand.get("type") for operand in (form.get("operands") or []))
        for form in forms
    ]
    if len(forms) == 1:
        return form_operand_types[0]

    encoding_index = select_encoding_index(inst_kb, opcode)
    if form_operand_types == [("dn", "dn"), ("imm", "dn"), ("ea",)]:
        if encoding_index == 0:
            return form_operand_types[0] if ((opcode >> 5) & 1) else form_operand_types[1]
        if encoding_index == 1:
            return form_operand_types[2]

    if form_operand_types == [("dn", "disp"), ("disp", "dn")]:
        enc_fields = inst_kb["encodings"][encoding_index].get("fields", [])
        opmode_f = next((f for f in enc_fields if f["name"] == "OPMODE"), None)
        opmode_table = inst_kb.get("constraints", {}).get("opmode_table") or []
        if opmode_f is None:
            raise ValueError(
                f"MOVEP-style form selection missing OPMODE in {inst_kb.get('mnemonic', '<unknown>')}")
        opmode = _xf(opcode, (opmode_f["bit_hi"], opmode_f["bit_lo"],
                              opmode_f["bit_hi"] - opmode_f["bit_lo"] + 1))
        entry = next((entry for entry in opmode_table if entry["opmode"] == opmode), None)
        if entry is None:
            raise ValueError(
                f"No KB opmode_table entry for opcode ${opcode:04x} "
                f"in {inst_kb.get('mnemonic', '<unknown>')}")
        desc = entry.get("description", "").lower()
        if "register to memory" in desc:
            return form_operand_types[0]
        if "memory to register" in desc:
            return form_operand_types[1]
        raise ValueError(
            f"Unsupported MOVEP-style opmode description {entry.get('description')!r}")

    if form_operand_types == [("reglist", "ea"), ("ea", "reglist")]:
        enc_fields = inst_kb["encodings"][encoding_index].get("fields", [])
        dr_field = next((f for f in enc_fields if f["name"] == "dr"), None)
        if dr_field is None:
            raise ValueError(
                f"MOVEM-style form selection missing dr in {inst_kb.get('mnemonic', '<unknown>')}")
        dr = _xf(opcode, (dr_field["bit_hi"], dr_field["bit_lo"], dr_field["width"]))
        return form_operand_types[1] if dr else form_operand_types[0]

    if form_operand_types == [("ctrl_reg", "rn"), ("rn", "ctrl_reg")]:
        enc_fields = inst_kb["encodings"][encoding_index].get("fields", [])
        dr_field = next((f for f in enc_fields if f["name"] == "dr"), None)
        if dr_field is None:
            raise ValueError(
                f"MOVEC-style form selection missing dr in {inst_kb.get('mnemonic', '<unknown>')}")
        dr = _xf(opcode, (dr_field["bit_hi"], dr_field["bit_lo"], dr_field["width"]))
        return form_operand_types[1] if dr else form_operand_types[0]

    operand_modes = inst_kb.get("constraints", {}).get("operand_modes") or {}
    if operand_modes:
        field_name = operand_modes.get("field")
        values = operand_modes.get("values") or {}
        enc_fields = inst_kb["encodings"][encoding_index].get("fields", [])
        mode_field = next((f for f in enc_fields if f["name"] == field_name), None)
        if mode_field is None:
            raise ValueError(
                f"Operand-mode selection missing {field_name!r} in {inst_kb.get('mnemonic', '<unknown>')}")
        mode_value = _xf(opcode, (mode_field["bit_hi"], mode_field["bit_lo"], mode_field["width"]))
        form_text = values.get(str(mode_value))
        if form_text is None:
            raise ValueError(
                f"No operand_modes entry for value {mode_value} in {inst_kb.get('mnemonic', '<unknown>')}")
        normalized = tuple(part.strip() for part in form_text.split(","))
        if normalized in form_operand_types:
            return normalized
        matching_forms = [
            operand_types for operand_types in form_operand_types
            if operand_types[:len(normalized)] == normalized
        ]
        if len(matching_forms) == 1:
            return matching_forms[0]
        raise ValueError(
            f"Operand_modes resolved to unsupported form {normalized!r} in {inst_kb.get('mnemonic', '<unknown>')}")

    if encoding_index < len(form_operand_types):
        return form_operand_types[encoding_index]

    raise ValueError(
        f"Unable to resolve operand form for opcode ${opcode:04x} "
        f"in {inst_kb.get('mnemonic', '<unknown>')}")


def select_operand_types_from_raw(inst_kb: dict, inst_raw: bytes) -> tuple[str, ...]:
    if len(inst_raw) < 2:
        raise ValueError("Instruction bytes missing opcode word")
    opcode = struct.unpack_from(">H", inst_raw, 0)[0]
    operand_types = select_operand_types(inst_kb, opcode)
    encoding_index = select_encoding_index(inst_kb, opcode)
    mnemonic = inst_kb.get("mnemonic")
    forms = inst_kb.get("forms") or []
    form_operand_types = [
        tuple(operand.get("type") for operand in (form.get("operands") or []))
        for form in forms
    ]
    if mnemonic == "MOVE16" and encoding_index == 2:
        enc_fields = inst_kb["encodings"][2].get("fields", [])
        opmode_field = next((f for f in enc_fields if f["name"] == "OPMODE"), None)
        if opmode_field is None:
            raise ValueError("MOVE16 absolute form missing OPMODE field")
        opmode = _xf(opcode, (opmode_field["bit_hi"], opmode_field["bit_lo"], opmode_field["width"]))
        opmode_table = inst_kb.get("constraints", {}).get("opmode_table") or []
        entry = next((entry for entry in opmode_table if entry["opmode"] == opmode), None)
        if entry is None:
            raise ValueError(f"MOVE16 missing opmode_table entry for {opmode}")

        def _move16_operand_type(operand_text: str) -> str:
            normalized = operand_text.replace(" ", "")
            if normalized == "(xxx).L":
                return "absl"
            if normalized == "(Ay)+":
                return "postinc"
            if normalized == "(Ay)":
                return "ind"
            raise ValueError(f"Unsupported MOVE16 operand text {operand_text!r}")

        return (
            _move16_operand_type(entry["source"]),
            _move16_operand_type(entry["destination"]),
        )
    if mnemonic == "PTRAPcc":
        enc_fields = inst_kb["encodings"][0].get("fields", [])
        opmode_field = next((f for f in enc_fields if f["name"] == "OPMODE"), None)
        if opmode_field is None:
            raise ValueError("PTRAPcc missing OPMODE field")
        opmode = _xf(opcode, (opmode_field["bit_hi"], opmode_field["bit_lo"], opmode_field["width"]))
        opmode_table = inst_kb.get("constraints", {}).get("opmode_table") or []
        entry = next((entry for entry in opmode_table if entry["opmode"] == opmode), None)
        if entry is None:
            raise ValueError(f"PTRAPcc missing opmode_table entry for {opmode}")
        return ("imm",) if entry["size"] in {"w", "l"} else ()
    if encoding_index != 1 or len(inst_raw) < 4:
        return operand_types

    if (mnemonic in {"MULS", "MULU"}
            and form_operand_types == [("ea", "dn"), ("ea", "dn"), ("ea", "dn_pair")]
            and len(inst_kb.get("encodings", [])) >= 3):
        ext = struct.unpack_from(">H", inst_raw, 2)[0]
        fields = inst_kb["encodings"][2].get("fields", [])
        size_field = next((f for f in fields if f["name"] == "SIZE"), None)
        if size_field is None:
            raise ValueError(f"{mnemonic} extension SIZE field missing")
        size_bit = _xf(ext, (size_field["bit_hi"], size_field["bit_lo"], size_field["width"]))
        return ("ea", "dn_pair") if size_bit else ("ea", "dn")

    if (mnemonic in {"DIVS, DIVSL", "DIVU, DIVUL"}
            and form_operand_types == [("ea", "dn"), ("ea", "dn"), ("ea", "dn_pair"), ("ea", "dn_pair")]
            and len(inst_kb.get("encodings", [])) >= 3):
        ext = struct.unpack_from(">H", inst_raw, 2)[0]
        fields = inst_kb["encodings"][2].get("fields", [])
        size_field = next((f for f in fields if f["name"] == "SIZE"), None)
        dq_field = next((f for f in fields if f["name"] == "REGISTER Dq"), None)
        dr_field = next((f for f in fields if f["name"] == "REGISTER Dr"), None)
        if size_field is None or dq_field is None or dr_field is None:
            raise ValueError(f"{mnemonic} extension fields missing")
        size_bit = _xf(ext, (size_field["bit_hi"], size_field["bit_lo"], size_field["width"]))
        dq = _xf(ext, (dq_field["bit_hi"], dq_field["bit_lo"], dq_field["width"]))
        dr = _xf(ext, (dr_field["bit_hi"], dr_field["bit_lo"], dr_field["width"]))
        return ("ea", "dn_pair") if (size_bit or dq != dr) else ("ea", "dn")

    return operand_types


def _decode_bitfield_extension(inst_raw: bytes, meta: dict, inst_kb: dict) -> dict:
    encodings = inst_kb.get("encodings", [])
    if len(encodings) < 2:
        raise ValueError(f"KB bitfield extension encoding missing in {inst_kb.get('mnemonic', '<unknown>')}")
    if len(inst_raw) < meta["opword_bytes"] + 2:
        raise ValueError("Bitfield extension word missing")
    ext = struct.unpack_from(">H", inst_raw, meta["opword_bytes"])[0]
    fields = encodings[1].get("fields", [])

    def _field(name: str):
        return next((f for f in fields if f["name"] == name), None)

    do_field = _field("Do")
    dw_field = _field("Dw")
    off_field = _field("OFFSET")
    width_field = _field("WIDTH")
    if do_field is None or dw_field is None or off_field is None or width_field is None:
        raise ValueError(f"KB bitfield encoding incomplete in {inst_kb.get('mnemonic', '<unknown>')}")
    offset_is_register = bool(_xf(ext, (do_field["bit_hi"], do_field["bit_lo"], do_field["width"])))
    width_is_register = bool(_xf(ext, (dw_field["bit_hi"], dw_field["bit_lo"], dw_field["width"])))
    offset_value = _xf(ext, (off_field["bit_hi"], off_field["bit_lo"], off_field["width"]))
    width_value = _xf(ext, (width_field["bit_hi"], width_field["bit_lo"], width_field["width"]))
    if not offset_is_register and offset_value >= 16:
        offset_value -= 32
    if not width_is_register and width_value == 0:
        width_value = 32
    result = {
        "offset_is_register": offset_is_register,
        "offset_value": offset_value,
        "width_is_register": width_is_register,
        "width_value": width_value,
    }
    reg_field = _field("REGISTER")
    if reg_field is not None:
        result["register"] = _xf(ext, (reg_field["bit_hi"], reg_field["bit_lo"], reg_field["width"]))
    return result


def decode_instruction_operands(inst_raw: bytes, inst_kb: dict,
                                meta: dict, size: str,
                                inst_offset: int) -> dict:
    """Decode source and destination operands from raw instruction bytes.

    Extracts structured operand info using KB encoding fields, without
    executing the instruction.  This is the same decode logic used in the
    executor's _apply_instruction, extracted for use by downstream tools.

    Returns dict with:
        ea_op: Operand from MODE/REGISTER (bits 5-0), or None
        dst_op: Operand from upper MODE/REGISTER (MOVE only), or None
        reg_num: register number from upper REGISTER field, or None
        imm_val: decoded immediate (from DATA field or extension words), or None
        ea_is_source: bool from OPMODE (None if no OPMODE)
    """
    result = {"ea_op": None, "dst_op": None, "reg_num": None,
              "imm_val": None, "ea_is_source": None,
              "compare_reg": None, "update_reg": None,
              "reg_mode": None, "secondary_reg": None,
              "control_register": None}

    if len(inst_raw) < meta["opword_bytes"]:
        return result

    opcode = struct.unpack_from(">H", inst_raw, 0)[0]
    encoding_index = select_encoding_index(inst_kb, opcode)
    enc_fields = inst_kb["encodings"][encoding_index].get("fields", [])
    operand_types = select_operand_types_from_raw(inst_kb, inst_raw)

    mode_fields = sorted(
        [f for f in enc_fields if f["name"] == "MODE"],
        key=lambda f: f["bit_lo"])
    reg_fields = sorted(
        [f for f in enc_fields if f["name"] == "REGISTER"],
        key=lambda f: f["bit_lo"])
    imm_range = inst_kb.get("constraints", {}).get("immediate_range")

    ext_pos = meta["opword_bytes"]
    if (operand_types and operand_types[0] == "imm"
            and imm_range is not None
            and imm_range.get("field") is None):
        imm_bytes = max(2, (imm_range.get("bits", 16) + 7) // 8)
        if len(inst_raw) < ext_pos + imm_bytes:
            raise ValueError(
                f"{inst_kb.get('mnemonic', '<unknown>')} immediate missing")
        ext_pos += imm_bytes
    if operand_types in {("reglist", "ea"), ("ea", "reglist")}:
        if len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError(f"MOVEM register mask missing for {inst_kb.get('mnemonic', '<unknown>')}")
        ext_pos += 2
    if "bf_ea" in operand_types:
        if len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError(f"Bitfield extension word missing for {inst_kb.get('mnemonic', '<unknown>')}")
        ext_pos += 2
    if (inst_kb.get("mnemonic") in {"DIVS, DIVSL", "DIVU, DIVUL", "MULS", "MULU"}
            and encoding_index > 0):
        if len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} extension word missing")
        ext_pos += 2
    if (inst_kb.get("mnemonic") in {"PFLUSHR", "PScc", "PFLUSH PFLUSHA"}
            and "ea" in operand_types):
        if len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} extension word missing")
        ext_pos += 2

    if "bf_ea" in operand_types:
        result["bitfield"] = _decode_bitfield_extension(inst_raw, meta, inst_kb)
    if inst_kb.get("mnemonic") == "MOVES" and operand_types in {("rn", "ea"), ("ea", "rn")}:
        encodings = inst_kb.get("encodings", [])
        if len(encodings) < 2 or len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} extension word missing")
        ext = struct.unpack_from(">H", inst_raw, meta["opword_bytes"])[0]
        ext_pos = meta["opword_bytes"] + 2
        fields = encodings[1].get("fields", [])
        ad_field = next((f for f in fields if f["name"] == "A/D"), None)
        reg_field = next((f for f in fields if f["name"] == "REGISTER"), None)
        dr_field = next((f for f in fields if f["name"] == "dr"), None)
        if ad_field is None or reg_field is None or dr_field is None:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} extension fields missing")
        result["reg_mode"] = "an" if _xf(ext, (ad_field["bit_hi"], ad_field["bit_lo"], ad_field["width"])) else "dn"
        result["reg_num"] = _xf(ext, (reg_field["bit_hi"], reg_field["bit_lo"], reg_field["width"]))
        dr = _xf(ext, (dr_field["bit_hi"], dr_field["bit_lo"], dr_field["width"]))
        if mode_fields and reg_fields:
            mf = mode_fields[0]
            rf = reg_fields[0]
            ea_mode = _xf(opcode, (mf["bit_hi"], mf["bit_lo"], mf["bit_hi"] - mf["bit_lo"] + 1))
            ea_reg = _xf(opcode, (rf["bit_hi"], rf["bit_lo"], rf["bit_hi"] - rf["bit_lo"] + 1))
            ea_op, _ = _decode_ea(inst_raw, ext_pos, ea_mode, ea_reg, size, inst_offset)
            result["ea_op"] = ea_op
        result["ea_is_source"] = bool(dr)
    if inst_kb.get("mnemonic") == "MOVEC" and operand_types in {("ctrl_reg", "rn"), ("rn", "ctrl_reg")}:
        encodings = inst_kb.get("encodings", [])
        ctrl_regs = inst_kb.get("constraints", {}).get("control_registers") or []
        if len(encodings) < 2 or len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} extension word missing")
        ext = struct.unpack_from(">H", inst_raw, meta["opword_bytes"])[0]
        fields = encodings[1].get("fields", [])
        ad_field = next((f for f in fields if f["name"] == "A/D"), None)
        reg_field = next((f for f in fields if f["name"] == "REGISTER"), None)
        ctrl_field = next((f for f in fields if f["name"] == "CONTROL REGISTER"), None)
        if ad_field is None or reg_field is None or ctrl_field is None:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} extension fields missing")
        result["reg_mode"] = "an" if _xf(ext, (ad_field["bit_hi"], ad_field["bit_lo"], ad_field["width"])) else "dn"
        result["reg_num"] = _xf(ext, (reg_field["bit_hi"], reg_field["bit_lo"], reg_field["width"]))
        ctrl = _xf(ext, (ctrl_field["bit_hi"], ctrl_field["bit_lo"], ctrl_field["width"]))
        ctrl_entry = next((entry for entry in ctrl_regs if int(entry["hex"], 16) == ctrl), None)
        if ctrl_entry is None:
            raise ValueError(f"Unknown MOVEC control register ${ctrl:03x}")
        result["control_register"] = ctrl_entry["abbrev"]
    if inst_kb.get("mnemonic") == "PTRAPcc" and operand_types == ("imm",):
        if len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError("PTRAPcc condition word missing")
        ext_pos = meta["opword_bytes"] + 2
        if size == "w":
            if len(inst_raw) < ext_pos + 2:
                raise ValueError("PTRAPcc word immediate missing")
            result["imm_val"] = struct.unpack_from(">H", inst_raw, ext_pos)[0]
        elif size == "l":
            if len(inst_raw) < ext_pos + 4:
                raise ValueError("PTRAPcc long immediate missing")
            result["imm_val"] = struct.unpack_from(">I", inst_raw, ext_pos)[0]
        else:
            raise ValueError(f"Unsupported PTRAPcc operand size {size!r}")
    if inst_kb.get("mnemonic") == "LINK" and operand_types == ("an", "imm"):
        reg_field = next((f for f in enc_fields if f["name"] == "REGISTER"), None)
        if reg_field is None:
            raise ValueError("LINK register field missing")
        result["reg_num"] = _xf(opcode, (reg_field["bit_hi"], reg_field["bit_lo"], reg_field["width"]))
        if encoding_index == 2:
            if len(inst_raw) < meta["opword_bytes"] + 4:
                raise ValueError("LINK.L displacement words missing")
            result["imm_val"] = struct.unpack_from(">I", inst_raw, meta["opword_bytes"])[0]
        else:
            if len(inst_raw) < meta["opword_bytes"] + 2:
                raise ValueError("LINK.W displacement word missing")
            result["imm_val"] = struct.unpack_from(">h", inst_raw, meta["opword_bytes"])[0] & 0xFFFFFFFF
    if inst_kb.get("mnemonic") == "MOVE16" and operand_types == ("postinc", "postinc"):
        encodings = inst_kb.get("encodings", [])
        if len(encodings) < 2 or len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError("MOVE16 extension word missing")
        op_fields = encodings[0].get("fields", [])
        ext_fields = encodings[1].get("fields", [])
        ax_field = next((f for f in op_fields if f["name"] == "REGISTER Ax"), None)
        ay_field = next((f for f in ext_fields if f["name"] == "REGISTER Ay"), None)
        if ax_field is None or ay_field is None:
            raise ValueError("MOVE16 register fields missing")
        ext = struct.unpack_from(">H", inst_raw, meta["opword_bytes"])[0]
        ax = _xf(opcode, (ax_field["bit_hi"], ax_field["bit_lo"], ax_field["width"]))
        ay = _xf(ext, (ay_field["bit_hi"], ay_field["bit_lo"], ay_field["width"]))
        result["ea_op"] = Operand(mode="postinc", reg=ax, value=None)
        result["dst_op"] = Operand(mode="postinc", reg=ay, value=None)
    if inst_kb.get("mnemonic") == "MOVE16" and operand_types in {
            ("absl", "postinc"), ("postinc", "absl"), ("absl", "ind"), ("ind", "absl")}:
        encodings = inst_kb.get("encodings", [])
        if len(encodings) < 3 or len(inst_raw) < meta["opword_bytes"] + 4:
            raise ValueError("MOVE16 absolute address words missing")
        op_fields = encodings[2].get("fields", [])
        opmode_field = next((f for f in op_fields if f["name"] == "OPMODE"), None)
        reg_field = next((f for f in op_fields if f["name"] == "REGISTER Ay"), None)
        if opmode_field is None or reg_field is None:
            raise ValueError("MOVE16 absolute form fields missing")
        opmode = _xf(opcode, (opmode_field["bit_hi"], opmode_field["bit_lo"], opmode_field["width"]))
        opmode_table = inst_kb.get("constraints", {}).get("opmode_table") or []
        entry = next((entry for entry in opmode_table if entry["opmode"] == opmode), None)
        if entry is None:
            raise ValueError(f"MOVE16 missing opmode_table entry for {opmode}")
        an = _xf(opcode, (reg_field["bit_hi"], reg_field["bit_lo"], reg_field["width"]))
        addr = struct.unpack_from(">I", inst_raw, meta["opword_bytes"])[0]

        def _move16_operand(text: str) -> Operand:
            normalized = text.replace(" ", "")
            if normalized == "(xxx).L":
                return Operand(mode="absl", reg=None, value=addr)
            if normalized == "(Ay)+":
                return Operand(mode="postinc", reg=an, value=None)
            if normalized == "(Ay)":
                return Operand(mode="ind", reg=an, value=None)
            raise ValueError(f"Unsupported MOVE16 operand text {text!r}")

        result["ea_op"] = _move16_operand(entry["source"])
        result["dst_op"] = _move16_operand(entry["destination"])
    if inst_kb.get("mnemonic") == "CMPM" and operand_types == ("postinc", "postinc"):
        ax_field = next((f for f in enc_fields if f["name"] == "REGISTER Ax"), None)
        ay_field = next((f for f in enc_fields if f["name"] == "REGISTER Ay"), None)
        if ax_field is None or ay_field is None:
            raise ValueError("CMPM register fields missing")
        ax = _xf(opcode, (ax_field["bit_hi"], ax_field["bit_lo"], ax_field["width"]))
        ay = _xf(opcode, (ay_field["bit_hi"], ay_field["bit_lo"], ay_field["width"]))
        result["ea_op"] = Operand(mode="postinc", reg=ay, value=None)
        result["dst_op"] = Operand(mode="postinc", reg=ax, value=None)
    if inst_kb.get("mnemonic") in {"PACK", "UNPK"} and operand_types in {
            ("dn", "dn", "imm"), ("predec", "predec", "imm")}:
        if len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} adjustment word missing")
        named_reg_fields = sorted(
            [f for f in enc_fields if f["name"].startswith("REGISTER ")],
            key=lambda f: f["bit_lo"])
        if len(named_reg_fields) != 2:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} register fields missing")
        src_reg = _xf(opcode, (named_reg_fields[0]["bit_hi"], named_reg_fields[0]["bit_lo"], named_reg_fields[0]["width"]))
        dst_reg = _xf(opcode, (named_reg_fields[1]["bit_hi"], named_reg_fields[1]["bit_lo"], named_reg_fields[1]["width"]))
        imm = struct.unpack_from(">H", inst_raw, meta["opword_bytes"])[0]
        result["imm_val"] = imm
        if operand_types == ("dn", "dn", "imm"):
            result["ea_op"] = Operand(mode="dn", reg=src_reg, value=None)
            result["reg_num"] = src_reg
            result["secondary_reg"] = dst_reg
        else:
            result["ea_op"] = Operand(mode="predec", reg=src_reg, value=None)
            result["dst_op"] = Operand(mode="predec", reg=dst_reg, value=None)
    if inst_kb.get("mnemonic") in {"CHK2", "CMP2"} and operand_types == ("ea", "rn"):
        encodings = inst_kb.get("encodings", [])
        if len(encodings) < 2 or len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} extension word missing")
        ext = struct.unpack_from(">H", inst_raw, meta["opword_bytes"])[0]
        ext_pos = meta["opword_bytes"] + 2
        fields = encodings[1].get("fields", [])
        da_field = next((f for f in fields if f["name"] == "D/A"), None)
        reg_field = next((f for f in fields if f["name"] == "REGISTER"), None)
        if da_field is None or reg_field is None:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} extension fields missing")
        result["reg_mode"] = "an" if _xf(ext, (da_field["bit_hi"], da_field["bit_lo"], da_field["width"])) else "dn"
        result["reg_num"] = _xf(ext, (reg_field["bit_hi"], reg_field["bit_lo"], reg_field["width"]))
    if operand_types == ("dn", "dn", "ea"):
        encodings = inst_kb.get("encodings", [])
        if len(encodings) < 2 or len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError(f"CAS extension word missing for {inst_kb.get('mnemonic', '<unknown>')}")
        ext = struct.unpack_from(">H", inst_raw, meta["opword_bytes"])[0]
        ext_pos = meta["opword_bytes"] + 2
        fields = encodings[1].get("fields", [])
        du_field = next((f for f in fields if f["name"] == "Du"), None)
        dc_field = next((f for f in fields if f["name"] == "Dc"), None)
        if du_field is None or dc_field is None:
            raise ValueError(f"CAS extension fields missing for {inst_kb.get('mnemonic', '<unknown>')}")
        result["update_reg"] = _xf(ext, (du_field["bit_hi"], du_field["bit_lo"], du_field["width"]))
        result["compare_reg"] = _xf(ext, (dc_field["bit_hi"], dc_field["bit_lo"], dc_field["width"]))
    if operand_types == ("ea", "rn"):
        encodings = inst_kb.get("encodings", [])
        if len(encodings) < 2 or len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} extension word missing")
        ext = struct.unpack_from(">H", inst_raw, meta["opword_bytes"])[0]
        fields = encodings[1].get("fields", [])
        da_field = next((f for f in fields if f["name"] == "D/A"), None)
        reg_field = next((f for f in fields if f["name"] == "REGISTER"), None)
        if da_field is None or reg_field is None:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} extension fields missing")
        result["reg_mode"] = "an" if _xf(ext, (da_field["bit_hi"], da_field["bit_lo"], da_field["width"])) else "dn"
        result["reg_num"] = _xf(ext, (reg_field["bit_hi"], reg_field["bit_lo"], reg_field["width"]))
    if operand_types == ("rn",):
        da_field = next((f for f in enc_fields if f["name"] == "D/A"), None)
        reg_field = next((f for f in enc_fields if f["name"] == "REGISTER"), None)
        if da_field is None or reg_field is None:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} register fields missing")
        result["reg_mode"] = "an" if _xf(opcode, (da_field["bit_hi"], da_field["bit_lo"], da_field["width"])) else "dn"
        result["reg_num"] = _xf(opcode, (reg_field["bit_hi"], reg_field["bit_lo"], reg_field["width"]))
    if operand_types == ("dn", "label"):
        reg_field = next(
            (f for f in enc_fields if f["name"] in {"COUNT REGISTER", "REGISTER"}),
            None,
        )
        if reg_field is None:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} count register field missing")
        result["reg_num"] = _xf(opcode, (reg_field["bit_hi"], reg_field["bit_lo"], reg_field["width"]))
    if operand_types in {("usp", "an"), ("an", "usp")}:
        dr_field = next((f for f in enc_fields if f["name"] == "dr"), None)
        reg_field = next((f for f in enc_fields if f["name"] == "REGISTER"), None)
        if dr_field is None or reg_field is None:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} direction/register fields missing")
        result["reg_mode"] = "an"
        result["reg_num"] = _xf(opcode, (reg_field["bit_hi"], reg_field["bit_lo"], reg_field["width"]))
        result["ea_is_source"] = bool(_xf(opcode, (dr_field["bit_hi"], dr_field["bit_lo"], dr_field["width"])))
    if inst_kb.get("mnemonic") in {"ADDX", "SUBX", "ABCD", "SBCD"}:
        named_reg_fields = sorted(
            [f for f in enc_fields if f["name"].startswith("REGISTER ")],
            key=lambda f: f["bit_lo"])
        if len(named_reg_fields) != 2:
            raise ValueError(f"{inst_kb.get('mnemonic', '<unknown>')} register fields missing")
        src_reg = _xf(opcode, (named_reg_fields[0]["bit_hi"], named_reg_fields[0]["bit_lo"], named_reg_fields[0]["width"]))
        dst_reg = _xf(opcode, (named_reg_fields[1]["bit_hi"], named_reg_fields[1]["bit_lo"], named_reg_fields[1]["width"]))
        if operand_types == ("dn", "dn"):
            result["ea_op"] = Operand(mode="dn", reg=src_reg, value=None)
            result["reg_num"] = src_reg
        elif operand_types == ("predec", "predec"):
            result["ea_op"] = Operand(mode="predec", reg=src_reg, value=None)
            result["dst_op"] = Operand(mode="predec", reg=dst_reg, value=None)
    if (operand_types in {("ea", "dn"), ("ea", "dn_pair")}
            and encoding_index > 0
            and len(inst_raw) >= meta["opword_bytes"] + 2):
        encodings = inst_kb.get("encodings", [])
        if len(encodings) >= 3:
            ext = struct.unpack_from(">H", inst_raw, meta["opword_bytes"])[0]
            fields = encodings[2].get("fields", [])
            ext_reg_fields = [f for f in fields if f["name"].startswith("REGISTER ")]
            if ext_reg_fields:
                reg_values = {
                    f["name"]: _xf(ext, (f["bit_hi"], f["bit_lo"], f["width"]))
                    for f in ext_reg_fields
                }
                if "REGISTER Dr" in reg_values and "REGISTER Dq" in reg_values:
                    result["reg_num"] = reg_values["REGISTER Dr"]
                    result["secondary_reg"] = reg_values["REGISTER Dq"]
                elif "REGISTER Dl" in reg_values and "REGISTER Dh" in reg_values:
                    result["reg_num"] = reg_values["REGISTER Dl"]
                    result["secondary_reg"] = reg_values["REGISTER Dh"]
                elif "REGISTER Dh" in reg_values and "REGISTER DI" in reg_values:
                    result["reg_num"] = reg_values["REGISTER DI"]
                    result["secondary_reg"] = reg_values["REGISTER Dh"]

    # Decode EA from lowest MODE + lowest REGISTER
    if mode_fields and reg_fields:
        mf = mode_fields[0]
        rf = reg_fields[0]
        ea_mode = _xf(opcode, (mf["bit_hi"], mf["bit_lo"],
                               mf["bit_hi"] - mf["bit_lo"] + 1))
        ea_reg = _xf(opcode, (rf["bit_hi"], rf["bit_lo"],
                              rf["bit_hi"] - rf["bit_lo"] + 1))
        try:
            ea_op, ext_pos = _decode_ea(
                inst_raw, ext_pos,
                ea_mode, ea_reg, size, inst_offset)
            result["ea_op"] = ea_op
        except (ValueError, DecodeError):
            ext_pos = meta["opword_bytes"]

        # Destination EA from upper MODE + upper REGISTER (MOVE)
        if len(mode_fields) >= 2 and len(reg_fields) >= 2:
            dmf = mode_fields[1]
            drf = reg_fields[1]
            d_mode = _xf(opcode, (dmf["bit_hi"], dmf["bit_lo"],
                                  dmf["bit_hi"] - dmf["bit_lo"] + 1))
            d_reg = _xf(opcode, (drf["bit_hi"], drf["bit_lo"],
                                 drf["bit_hi"] - drf["bit_lo"] + 1))
            try:
                dst_op, _ = _decode_ea(
                    inst_raw, ext_pos,
                    d_mode, d_reg, size, inst_offset)
                result["dst_op"] = dst_op
            except (ValueError, DecodeError):
                pass

    if operand_types in {("dn", "disp"), ("disp", "dn")}:
        data_reg_field = next((f for f in enc_fields if f["name"] == "DATA REGISTER"), None)
        addr_reg_field = next((f for f in enc_fields if f["name"] == "ADDRESS REGISTER"), None)
        if data_reg_field is None or addr_reg_field is None:
            raise ValueError(f"MOVEP decode fields missing for {inst_kb.get('mnemonic', '<unknown>')}")
        result["reg_num"] = _xf(opcode, (data_reg_field["bit_hi"], data_reg_field["bit_lo"],
                                         data_reg_field["bit_hi"] - data_reg_field["bit_lo"] + 1))
        if len(inst_raw) < meta["opword_bytes"] + 2:
            raise ValueError(f"MOVEP displacement missing for opcode ${opcode:04x}")
        disp = struct.unpack_from(">H", inst_raw, meta["opword_bytes"])[0]
        if disp >= 0x8000:
            disp -= 0x10000
        addr_reg = _xf(opcode, (addr_reg_field["bit_hi"], addr_reg_field["bit_lo"],
                                addr_reg_field["bit_hi"] - addr_reg_field["bit_lo"] + 1))
        result["ea_op"] = Operand(mode="disp", reg=addr_reg, value=disp,
                                  index_reg=None, index_is_addr=False,
                                  index_size="w", size=None)
    if operand_types == ("bf_ea", "dn"):
        bitfield = result.get("bitfield")
        if bitfield is None or "register" not in bitfield:
            raise ValueError(f"Bitfield destination register missing for {inst_kb.get('mnemonic', '<unknown>')}")
        result["reg_num"] = bitfield["register"]
    if operand_types == ("dn", "bf_ea"):
        bitfield = result.get("bitfield")
        if bitfield is None or "register" not in bitfield:
            raise ValueError(f"Bitfield source register missing for {inst_kb.get('mnemonic', '<unknown>')}")
        result["reg_num"] = bitfield["register"]

    # Register number from REGISTER field.
    # With 2+ REGISTER fields: upper field is the "other" register (bits 11-9).
    # With exactly 1 REGISTER and no MODE: the sole REGISTER is the
    # destination (e.g. MOVEQ where DATA has the immediate).
    if result["reg_num"] is None and operand_types == ("imm", "dn") and len(reg_fields) >= 2:
        rf = reg_fields[0]
        result["reg_num"] = _xf(opcode, (rf["bit_hi"], rf["bit_lo"],
                                         rf["bit_hi"] - rf["bit_lo"] + 1))
    elif result["reg_num"] is None and len(reg_fields) >= 2:
        rf = reg_fields[-1]
        result["reg_num"] = _xf(opcode, (rf["bit_hi"], rf["bit_lo"],
                                         rf["bit_hi"] - rf["bit_lo"] + 1))
    elif result["reg_num"] is None and len(reg_fields) == 1 and not mode_fields:
        rf = reg_fields[0]
        result["reg_num"] = _xf(opcode, (rf["bit_hi"], rf["bit_lo"],
                                         rf["bit_hi"] - rf["bit_lo"] + 1))

    # OPMODE direction from KB opmode_table
    opmode_table = inst_kb.get("constraints", {}).get("opmode_table")
    if opmode_table:
        opmode_f = next(
            (f for f in enc_fields if f["name"] == "OPMODE"), None)
        if opmode_f:
            opmode_val = _xf(opcode, (
                opmode_f["bit_hi"], opmode_f["bit_lo"],
                opmode_f["bit_hi"] - opmode_f["bit_lo"] + 1))
            for entry in opmode_table:
                if entry["opmode"] == opmode_val:
                    result["ea_is_source"] = entry.get("ea_is_source")
                    break

    # Decode immediate value from opcode (KB-driven).
    # Pattern 1: DATA field in opcode (ADDQ/SUBQ/MOVEQ)
    # Pattern 2: extension word immediate (ADDI/SUBI/etc.)
    if result["imm_val"] is not None:
        imm_range = None
    data_field_name = imm_range.get("field") if imm_range else None
    if data_field_name:
        df = next((f for f in enc_fields
                   if f["name"] == data_field_name), None)
        if df:
            raw_val = _xf(opcode, (df["bit_hi"], df["bit_lo"],
                                   df["bit_hi"] - df["bit_lo"] + 1))
            if imm_range.get("zero_means") and raw_val == 0:
                raw_val = imm_range["zero_means"]
            if imm_range.get("signed"):
                bits = imm_range["bits"]
                if raw_val >= (1 << (bits - 1)):
                    raw_val -= (1 << bits)
                raw_val &= 0xFFFFFFFF
            result["imm_val"] = raw_val
        elif operand_types == ("imm", "dn") and len(reg_fields) >= 2:
            rf = reg_fields[-1]
            raw_val = _xf(opcode, (rf["bit_hi"], rf["bit_lo"],
                                   rf["bit_hi"] - rf["bit_lo"] + 1))
            if imm_range.get("zero_means") and raw_val == 0:
                raw_val = imm_range["zero_means"]
            if imm_range.get("signed"):
                bits = imm_range["bits"]
                if raw_val >= (1 << (bits - 1)):
                    raw_val -= (1 << bits)
                raw_val &= 0xFFFFFFFF
            result["imm_val"] = raw_val
        elif "imm" in operand_types and len(inst_raw) >= meta["opword_bytes"] + 2:
            imm_bytes = max(2, (imm_range.get("bits", 16) + 7) // 8)
            pos = meta["opword_bytes"]
            if imm_bytes <= 2:
                imm_val = struct.unpack_from(">H", inst_raw, pos)[0]
            else:
                imm_val = struct.unpack_from(">I", inst_raw, pos)[0]
            bits = imm_range.get("bits")
            if bits:
                imm_val &= (1 << bits) - 1
            if imm_range.get("signed") and bits:
                if imm_val >= (1 << (bits - 1)):
                    imm_val -= (1 << bits)
                imm_val &= 0xFFFFFFFF
            result["imm_val"] = imm_val
            if mode_fields and reg_fields:
                mf = mode_fields[0]
                rf = reg_fields[0]
                ea_m = _xf(opcode, (mf["bit_hi"], mf["bit_lo"],
                                    mf["bit_hi"] - mf["bit_lo"] + 1))
                ea_r = _xf(opcode, (rf["bit_hi"], rf["bit_lo"],
                                    rf["bit_hi"] - rf["bit_lo"] + 1))
                try:
                    ea_op, _ = _decode_ea(
                        inst_raw, pos + max(imm_bytes, 2),
                        ea_m, ea_r, size, inst_offset)
                    result["ea_op"] = ea_op
                except (ValueError, DecodeError):
                    pass

    elif (not opmode_table and not data_field_name
          and len(mode_fields) == 1 and not imm_range
          and "imm" in operand_types):
        # Pattern 2: extension word immediate (ADDI etc.)
        imm_bytes = meta["size_byte_count"].get(
            size, meta["size_byte_count"]["w"])
        pos = meta["opword_bytes"]
        if pos + imm_bytes <= len(inst_raw):
            if imm_bytes <= 2:
                imm_val = struct.unpack_from(">H", inst_raw, pos)[0]
                if size == "b":
                    imm_val &= 0xFF
            else:
                imm_val = struct.unpack_from(">I", inst_raw, pos)[0]
            result["imm_val"] = imm_val
            # Re-decode EA after the immediate
            if mode_fields and reg_fields:
                mf = mode_fields[0]
                rf = reg_fields[0]
                ea_m = _xf(opcode, (mf["bit_hi"], mf["bit_lo"],
                                    mf["bit_hi"] - mf["bit_lo"] + 1))
                ea_r = _xf(opcode, (rf["bit_hi"], rf["bit_lo"],
                                    rf["bit_hi"] - rf["bit_lo"] + 1))
                try:
                    ea_op, _ = _decode_ea(
                        inst_raw, pos + max(imm_bytes, 2),
                        ea_m, ea_r, size, inst_offset)
                    result["ea_op"] = ea_op
                except (ValueError, DecodeError):
                    pass

    return result


def decode_destination(inst_raw: bytes, inst_kb: dict,
                       meta: dict, size: str,
                       inst_offset: int) -> tuple[str, int] | None:
    """Determine the destination register of an instruction.

    Returns (mode, reg_num) where mode is "dn" or "an", or None if the
    destination cannot be determined from opcode bits.

    Handles:
    - MOVE/MOVEA: dst_op from upper MODE/REGISTER fields
    - OPMODE instructions: ea_is_source=False means EA is dst, else reg_num
    - Single-EA + reg_num: destination is the upper REGISTER (e.g. LEA)
    """
    decoded = decode_instruction_operands(
        inst_raw, inst_kb, meta, size, inst_offset)

    # MOVE/MOVEA: has dst_op with explicit mode
    dst_op = decoded["dst_op"]
    if dst_op is not None:
        if dst_op.mode in ("dn", "an"):
            return (dst_op.mode, dst_op.reg)
        return None  # destination is memory, not a register

    # OPMODE instructions (ADD, SUB, AND, OR, etc.)
    ea_is_source = decoded["ea_is_source"]
    ea_op = decoded["ea_op"]
    reg_num = decoded["reg_num"]
    if ea_is_source is not None:
        if ea_is_source:
            # EA is source -> destination is the upper register (Dn)
            if reg_num is not None:
                return ("dn", reg_num)
        else:
            # EA is destination
            if ea_op and ea_op.mode in ("dn", "an"):
                return (ea_op.mode, ea_op.reg)
        return None

    # Single-EA with upper register: LEA, MOVEA-like, etc.
    # Check if instruction writes to An via source_sign_extend (MOVEA pattern)
    if inst_kb.get("source_sign_extend") and reg_num is not None:
        return ("an", reg_num)

    # Default: reg_num is destination Dn (MOVEQ, ADDQ to Dn, etc.)
    if reg_num is not None:
        # If ea_op is a register and no OPMODE, check operation_type
        op_type = inst_kb.get("operation_type")
        if op_type == "move":
            return ("dn", reg_num)
        # For ALU ops without OPMODE (ADDQ/SUBQ), EA is the destination
        if ea_op and ea_op.mode in ("dn", "an"):
            return (ea_op.mode, ea_op.reg)

    return None


def parse_reg_name(name: str) -> tuple[str, int]:
    """Parse a register name like "D0"/"A1" to ("dn", 0)/("an", 1).

    Raises ValueError on unrecognized format.
    """
    name = name.strip().upper()
    if len(name) == 2 and name[1].isdigit():
        if name[0] == "D":
            return ("dn", int(name[1]))
        if name[0] == "A":
            return ("an", int(name[1]))
    raise ValueError(f"Cannot parse register name: {name}")


def read_string_at(data: bytes, addr: int, max_len: int = 64) -> str | None:
    """Read a null-terminated ASCII string from data bytes.

    Returns None if addr is out of range or string is empty/non-ASCII.
    """
    if addr >= len(data):
        return None
    end = min(addr + max_len, len(data))
    result = []
    for i in range(addr, end):
        b = data[i]
        if b == 0:
            break
        result.append(b)
    if not result:
        return None
    try:
        return bytes(result).decode("ascii")
    except UnicodeDecodeError:
        return None


def find_containing_sub(addr: int, sorted_subs: list[dict]) -> int | None:
    """Binary search for the subroutine containing addr.

    sorted_subs: list of dicts with int "addr" and "end" keys, sorted by addr.
    Returns the subroutine's start address, or None.
    """
    lo, hi = 0, len(sorted_subs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        s = sorted_subs[mid]
        if addr < s["addr"]:
            hi = mid - 1
        elif addr >= s["end"]:
            lo = mid + 1
        else:
            return s["addr"]
    return None
