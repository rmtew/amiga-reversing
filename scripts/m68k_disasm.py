"""M68K disassembler targeting vasm-compatible Motorola syntax.

Decodes 68000 instructions from raw bytes and emits assembly text.
"""

import json
import struct
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass
class Instruction:
    offset: int       # byte offset within hunk
    size: int         # total instruction size in bytes
    opcode: int       # first word
    text: str         # disassembled text (mnemonic + operands)
    raw: bytes        # raw instruction bytes


class DecodeError(Exception):
    pass


SIZE_BYTE = 0
SIZE_WORD = 1
SIZE_LONG = 2

SIZE_SUFFIX = {SIZE_BYTE: ".b", SIZE_WORD: ".w", SIZE_LONG: ".l"}
SIZE_NAMES = {SIZE_BYTE: "byte", SIZE_WORD: "word", SIZE_LONG: "long"}

CPU_ORDER = {
    "68000": 0,
    "68010": 1,
    "68020": 2,
    "68030": 3,
    "68040": 4,
    "68060": 5,
    "cpu32": 2,
}


def _normalize_cpu(cpu_name: str | None) -> str:
    if not cpu_name:
        return "68000"
    if cpu_name.startswith("-m"):
        cpu_name = cpu_name[2:]
    if cpu_name == "68020up":
        return "68020"
    if cpu_name in ("cf", "cfpu"):
        return "68060"
    return cpu_name


@lru_cache(maxsize=1)
def _load_kb_processor_mins() -> dict[str, str]:
    path = Path(__file__).resolve().parent.parent / "knowledge" / "m68k_instructions.json"
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        kb = json.load(f)

    mins: dict[str, str] = {}
    for inst in kb:
        min_cpu = _normalize_cpu(inst.get("processor_min", "68000"))
        mnemonic = inst.get("mnemonic", "")
        for part in mnemonic.split(","):
            tokens = part.strip().split()
            if not tokens:
                continue
            # Keep full token and individual alias tokens like "ASL" and "ASR".
            for token in tokens:
                mins[token.lower()] = min_cpu
    return mins


CC_CODES = {
    "t", "f", "hi", "ls", "cc", "cs", "ne", "eq",
    "vc", "vs", "pl", "mi", "ge", "lt", "gt", "le",
}


def _canonical_mnemonic(decoded: str) -> str:
    """Normalize a decoded token to a KB mnemonic key."""
    tok = decoded.split(".", 1)[0].lower()
    if tok in ("", "#"):
        return tok

    for cc in CC_CODES:
        if tok == f"db{cc}":
            return "dbcc"
        if tok == f"trap{cc}":
            return "trapcc"
        if tok == f"pb{cc}":
            return "pbcc"
        if tok == f"pdb{cc}":
            return "pdbcc"
        if tok == f"ps{cc}":
            return "pscc"
        if tok == f"ptrap{cc}":
            return "ptrapcc"
        if tok == f"s{cc}" and tok != "src":
            return "scc"

        if tok == f"b{cc}" and not tok.startswith("bsr") and not tok.startswith("bra"):
            return "bcc"

    return tok


def _ensure_cpu_supported(decoded_text: str, max_cpu: str | None) -> None:
    if not max_cpu:
        return

    max_cpu = _normalize_cpu(max_cpu)
    if max_cpu not in CPU_ORDER:
        return

    canonical = _canonical_mnemonic(decoded_text)
    required_cpu = _load_kb_processor_mins().get(canonical)
    if required_cpu is None:
        return

    if CPU_ORDER.get(required_cpu, 0) > CPU_ORDER[max_cpu]:
        raise DecodeError(
            f"unsupported instruction '{canonical}' for max_cpu={max_cpu}; "
            f"requires {required_cpu}"
        )


class _Decoder:
    """Stateful instruction decoder."""

    def __init__(self, data: bytes, base_offset: int = 0):
        self.data = data
        self.base = base_offset
        self.pos = 0

    def remaining(self) -> int:
        return len(self.data) - self.pos

    def peek_u16(self) -> int:
        return struct.unpack_from(">H", self.data, self.pos)[0]

    def read_u16(self) -> int:
        val = struct.unpack_from(">H", self.data, self.pos)[0]
        self.pos += 2
        return val

    def read_i16(self) -> int:
        val = struct.unpack_from(">h", self.data, self.pos)[0]
        self.pos += 2
        return val

    def read_u32(self) -> int:
        val = struct.unpack_from(">I", self.data, self.pos)[0]
        self.pos += 4
        return val

    def read_i32(self) -> int:
        val = struct.unpack_from(">i", self.data, self.pos)[0]
        self.pos += 4
        return val


def _reg_name(reg: int, is_addr: bool = False) -> str:
    if is_addr:
        return f"a{reg}" if reg < 7 else "sp"
    return f"d{reg}"


def _ea_str(d: _Decoder, mode: int, reg: int, size: int, pc_offset: int) -> str:
    """Decode effective address and return string representation.

    pc_offset: byte offset of the instruction start (for PC-relative).
    """
    if mode == 0:  # Dn
        return _reg_name(reg)
    elif mode == 1:  # An
        return _reg_name(reg, True)
    elif mode == 2:  # (An)
        return f"({_reg_name(reg, True)})"
    elif mode == 3:  # (An)+
        return f"({_reg_name(reg, True)})+"
    elif mode == 4:  # -(An)
        return f"-({_reg_name(reg, True)})"
    elif mode == 5:  # d16(An)
        disp = d.read_i16()
        return f"{disp}({_reg_name(reg, True)})"
    elif mode == 6:  # d8(An,Xn)
        ext = d.read_u16()
        xreg = (ext >> 12) & 7
        xtype = "a" if ext & 0x8000 else "d"
        xsize = ".l" if ext & 0x0800 else ".w"
        disp = ext & 0xFF
        if disp & 0x80:
            disp -= 256
        return f"{disp}({_reg_name(reg, True)},{xtype}{xreg}{xsize})"
    elif mode == 7:
        if reg == 0:  # abs.w
            addr = d.read_i16()
            if addr < 0:
                return f"(${''.join(f'{b:02x}' for b in struct.pack('>h', addr))}).w"
            return f"(${addr:04x}).w"
        elif reg == 1:  # abs.l
            addr = d.read_u32()
            return f"${addr:08x}"
        elif reg == 2:  # d16(PC)
            disp = d.read_i16()
            return f"{disp}(pc)"
        elif reg == 3:  # d8(PC,Xn)
            ext = d.read_u16()
            xreg = (ext >> 12) & 7
            xtype = "a" if ext & 0x8000 else "d"
            xsize = ".l" if ext & 0x0800 else ".w"
            disp = ext & 0xFF
            if disp & 0x80:
                disp -= 256
            return f"{disp}(pc,{xtype}{xreg}{xsize})"
        elif reg == 4:  # #imm
            if size == SIZE_BYTE or size == SIZE_WORD:
                imm = d.read_u16()
                if size == SIZE_BYTE:
                    imm &= 0xFF
                return f"#${imm:x}"
            elif size == SIZE_LONG:
                imm = d.read_u32()
                return f"#${imm:x}"
    raise DecodeError(f"unknown EA mode={mode} reg={reg}")


def _movem_reglist(mask: int, direction: int) -> str:
    """Convert MOVEM register mask to register list string.

    direction: 0 = register-to-memory (reversed bit order for predecrement)
               1 = memory-to-register (normal bit order)
    """
    if direction == 0:
        # Predecrement: bit 0 = A7, bit 15 = D0
        regs = []
        for i in range(16):
            if mask & (1 << i):
                if i < 8:
                    regs.append(f"a{7 - i}")
                else:
                    regs.append(f"d{15 - i}")
    else:
        # Normal: bit 0 = D0, bit 15 = A7
        regs = []
        for i in range(16):
            if mask & (1 << i):
                if i < 8:
                    regs.append(f"d{i}")
                else:
                    regs.append(f"a{i - 8}")

    # Compress into ranges
    return _compress_reglist(regs)


def _compress_reglist(regs: list[str]) -> str:
    """Compress register list into range notation."""
    if not regs:
        return ""
    # Group by type (d/a) and find ranges
    groups = []
    dregs = sorted([int(r[1]) for r in regs if r[0] == 'd'])
    aregs = sorted([int(r[1]) for r in regs if r[0] == 'a'])

    def ranges(nums, prefix):
        if not nums:
            return
        start = nums[0]
        end = start
        for n in nums[1:]:
            if n == end + 1:
                end = n
            else:
                if start == end:
                    groups.append(f"{prefix}{start}")
                else:
                    groups.append(f"{prefix}{start}-{prefix}{end}")
                start = end = n
        if start == end:
            groups.append(f"{prefix}{start}")
        else:
            groups.append(f"{prefix}{start}-{prefix}{end}")

    ranges(dregs, "d")
    ranges(aregs, "a")
    return "/".join(groups)


def _branch_target(offset: int, disp: int) -> str:
    """Format branch target address."""
    target = offset + 2 + disp
    return f"${target:x}"


def _decode_one(d: _Decoder, max_cpu: str | None) -> Instruction:
    """Decode a single instruction at current position."""
    start = d.pos
    pc_offset = d.base + start
    opcode = d.read_u16()

    # Decode based on upper nibble and bit patterns
    group = (opcode >> 12) & 0xF
    try:
        text = _decode_opcode(d, opcode, group, pc_offset)
    except struct.error as e:
        raise DecodeError(
            f"truncated instruction at offset=${pc_offset:06x} opcode=${opcode:04x}"
        ) from e
    _ensure_cpu_supported(text, max_cpu)

    size = d.pos - start
    raw = d.data[start:d.pos]
    return Instruction(offset=pc_offset, size=size, opcode=opcode,
                       text=text, raw=raw)


def _decode_opcode(d: _Decoder, op: int, group: int, pc: int) -> str:
    """Main opcode decoder."""

    if group == 0:
        return _decode_group0(d, op, pc)
    elif group == 1:
        return _decode_move_byte(d, op, pc)
    elif group == 2:
        return _decode_move_long(d, op, pc)
    elif group == 3:
        return _decode_move_word(d, op, pc)
    elif group == 4:
        return _decode_group4(d, op, pc)
    elif group == 5:
        return _decode_group5(d, op, pc)
    elif group == 6:
        return _decode_group6(d, op, pc)
    elif group == 7:
        return _decode_moveq(d, op, pc)
    elif group == 8:
        return _decode_group8(d, op, pc)
    elif group == 9:
        return _decode_sub(d, op, pc)
    elif group == 0xA:
        raise DecodeError(f"unsupported line-A op=${op:04x}")
    elif group == 0xB:
        return _decode_cmp_eor(d, op, pc)
    elif group == 0xC:
        return _decode_group_c(d, op, pc)
    elif group == 0xD:
        return _decode_add(d, op, pc)
    elif group == 0xE:
        return _decode_shift(d, op, pc)
    elif group == 0xF:
        return _decode_line_f(d, op, pc)

    raise DecodeError(f"unhandled group {group}")


# --- Group decoders ---

def _decode_group0(d: _Decoder, op: int, pc: int) -> str:
    """Bit operations and immediate ops (ORI, ANDI, SUBI, ADDI, EORI, CMPI, BTST, etc.)"""
    if op & 0x0100:
        # Dynamic bit operations: BTST/BCHG/BCLR/BSET Dn,<ea>
        reg = (op >> 9) & 7
        mode = (op >> 3) & 7
        ea_reg = op & 7
        bit_op = (op >> 6) & 3
        names = ["btst", "bchg", "bclr", "bset"]

        if mode == 1:
            # MOVEP
            dreg = (op >> 9) & 7
            areg = op & 7
            disp = d.read_i16()
            opmode = (op >> 6) & 7
            if opmode == 4:
                return f"movep.w {disp}(a{areg}),d{dreg}"
            elif opmode == 5:
                return f"movep.l {disp}(a{areg}),d{dreg}"
            elif opmode == 6:
                return f"movep.w d{dreg},{disp}(a{areg})"
            elif opmode == 7:
                return f"movep.l d{dreg},{disp}(a{areg})"

        sz = SIZE_LONG if mode == 0 else SIZE_BYTE
        ea = _ea_str(d, mode, ea_reg, sz, pc)
        return f"{names[bit_op]}    d{reg},{ea}"
    else:
        # Static bit ops or immediate ops
        top_bits = (op >> 9) & 7
        size_bits = (op >> 6) & 3

        if top_bits == 4:
            # Static bit operations
            mode = (op >> 3) & 7
            ea_reg = op & 7
            bit_op = size_bits
            names = ["btst", "bchg", "bclr", "bset"]
            bit_num = d.read_u16() & 0xFF
            sz = SIZE_LONG if mode == 0 else SIZE_BYTE
            ea = _ea_str(d, mode, ea_reg, sz, pc)
            return f"{names[bit_op]}    #{bit_num},{ea}"

        # CALLM / RTM (68020): top_bits=3, size_bits=3
        if top_bits == 3 and size_bits == 3:
            mode = (op >> 3) & 7
            ea_reg = op & 7
            if mode == 0:
                # RTM Dn
                return f"rtm     d{ea_reg}"
            elif mode == 1:
                # RTM An
                return f"rtm     a{ea_reg}"
            else:
                # CALLM #<data>,<ea>
                ext = d.read_u16()
                arg_count = ext & 0xFF
                ea = _ea_str(d, mode, ea_reg, SIZE_LONG, pc)
                return f"callm   #{arg_count},{ea}"

        # Immediate operations
        imm_names = {0: "ori", 1: "andi", 2: "subi", 3: "addi",
                     5: "eori", 6: "cmpi"}
        if top_bits not in imm_names:
            raise DecodeError(f"unknown group0 top={top_bits}")

        name = imm_names[top_bits]
        mode = (op >> 3) & 7
        ea_reg = op & 7

        # Special cases: ORI/ANDI/EORI to CCR/SR
        if size_bits == 0 and mode == 7 and ea_reg == 4:
            imm = d.read_u16() & 0xFF
            return f"{name}.b  #${imm:x},ccr"
        if size_bits == 1 and mode == 7 and ea_reg == 4:
            imm = d.read_u16()
            return f"{name}.w  #${imm:x},sr"

        sz = size_bits
        sfx = SIZE_SUFFIX[sz]
        if sz == SIZE_BYTE:
            imm = d.read_u16() & 0xFF
            imm_s = f"#${imm:x}"
        elif sz == SIZE_WORD:
            imm = d.read_u16()
            imm_s = f"#${imm:x}"
        else:
            imm = d.read_u32()
            imm_s = f"#${imm:x}"

        ea = _ea_str(d, mode, ea_reg, sz, pc)
        return f"{name}{sfx}  {imm_s},{ea}"


def _decode_move(d: _Decoder, op: int, pc: int, size: int) -> str:
    """Decode MOVE/MOVEA instruction."""
    src_mode = (op >> 3) & 7
    src_reg = op & 7
    dst_reg = (op >> 9) & 7
    dst_mode = (op >> 6) & 7
    sfx = SIZE_SUFFIX[size]

    src = _ea_str(d, src_mode, src_reg, size, pc)

    if dst_mode == 1:
        # MOVEA
        dst = _reg_name(dst_reg, True)
        return f"movea{sfx} {src},{dst}"

    dst = _ea_str(d, dst_mode, dst_reg, size, pc)
    return f"move{sfx}  {src},{dst}"


def _decode_move_byte(d: _Decoder, op: int, pc: int) -> str:
    return _decode_move(d, op, pc, SIZE_BYTE)

def _decode_move_long(d: _Decoder, op: int, pc: int) -> str:
    return _decode_move(d, op, pc, SIZE_LONG)

def _decode_move_word(d: _Decoder, op: int, pc: int) -> str:
    return _decode_move(d, op, pc, SIZE_WORD)


def _decode_group4(d: _Decoder, op: int, pc: int) -> str:
    """Miscellaneous: LEA, PEA, CLR, NEG, NOT, TST, MOVEM, JMP, JSR, etc."""
    if op == 0x4E70:
        return "reset"
    if op == 0x4E71:
        return "nop"
    if op == 0x4E72:
        imm = d.read_u16()
        return f"stop    #${imm:04x}"
    if op == 0x4E73:
        return "rte"
    if op == 0x4E74:
        disp = d.read_i16()
        return f"rtd     #{disp}"
    if op == 0x4E75:
        return "rts"
    if op == 0x4E76:
        return "trapv"
    if op == 0x4E77:
        return "rtr"
    if op == 0x4AFC:
        return "illegal"

    # TRAP
    if (op & 0xFFF0) == 0x4E40:
        vec = op & 0xF
        return f"trap    #{vec}"

    # LINK
    if (op & 0xFFF8) == 0x4E50:
        areg = op & 7
        disp = d.read_i16()
        return f"link    {_reg_name(areg, True)},#{disp}"

    # UNLK
    if (op & 0xFFF8) == 0x4E58:
        areg = op & 7
        return f"unlk    {_reg_name(areg, True)}"

    # MOVE USP
    if (op & 0xFFF0) == 0x4E60:
        areg = op & 7
        if op & 8:
            return f"move.l  usp,{_reg_name(areg, True)}"
        else:
            return f"move.l  {_reg_name(areg, True)},usp"

    # JSR
    if (op & 0xFFC0) == 0x4E80:
        mode = (op >> 3) & 7
        reg = op & 7
        ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
        return f"jsr     {ea}"

    # JMP
    if (op & 0xFFC0) == 0x4EC0:
        mode = (op >> 3) & 7
        reg = op & 7
        ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
        return f"jmp     {ea}"

    # LEA
    if (op & 0xF1C0) == 0x41C0:
        areg = (op >> 9) & 7
        mode = (op >> 3) & 7
        reg = op & 7
        ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
        return f"lea     {ea},{_reg_name(areg, True)}"

    # BKPT (68010+)
    if (op & 0xFFF8) == 0x4848:
        vec = op & 7
        return f"bkpt    #{vec}"

    # SWAP (must be before PEA — both match $4840 but SWAP has mode=0)
    if (op & 0xFFF8) == 0x4840:
        return f"swap    d{op & 7}"

    # EXT (must be before MOVEM — both match $4880/$48C0 but EXT has mode=0)
    if (op & 0xFFF8) == 0x4880:
        return f"ext.w   d{op & 7}"
    if (op & 0xFFF8) == 0x48C0:
        return f"ext.l   d{op & 7}"

    # PEA
    if (op & 0xFFC0) == 0x4840:
        mode = (op >> 3) & 7
        reg = op & 7
        ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
        return f"pea     {ea}"

    # CHK
    if (op & 0xF1C0) == 0x4180:
        dreg = (op >> 9) & 7
        mode = (op >> 3) & 7
        reg = op & 7
        ea = _ea_str(d, mode, reg, SIZE_WORD, pc)
        return f"chk     {ea},d{dreg}"

    # MOVEM (mode >= 2 guaranteed now since EXT caught mode=0)
    if (op & 0xFB80) == 0x4880:
        direction = (op >> 10) & 1  # 0=reg-to-mem, 1=mem-to-reg
        sz = SIZE_LONG if op & 0x0040 else SIZE_WORD
        sfx = SIZE_SUFFIX[sz]
        mode = (op >> 3) & 7
        reg = op & 7
        mask = d.read_u16()

        is_predec = (mode == 4)
        reglist = _movem_reglist(mask, 0 if is_predec else 1)
        ea = _ea_str(d, mode, reg, sz, pc)

        if direction == 0:
            return f"movem{sfx} {reglist},{ea}"
        else:
            return f"movem{sfx} {ea},{reglist}"

    # CLR, NEG, NEGX, NOT
    for pattern, name in [(0x4200, "clr"), (0x4400, "neg"),
                           (0x4000, "negx"), (0x4600, "not")]:
        if (op & 0xFF00) == pattern:
            sz = (op >> 6) & 3
            if sz == 3:
                continue  # not this instruction
            sfx = SIZE_SUFFIX[sz]
            mode = (op >> 3) & 7
            reg = op & 7
            ea = _ea_str(d, mode, reg, sz, pc)
            return f"{name}{sfx}  {ea}"

    # TST
    if (op & 0xFF00) == 0x4A00:
        sz = (op >> 6) & 3
        if sz < 3:
            sfx = SIZE_SUFFIX[sz]
            mode = (op >> 3) & 7
            reg = op & 7
            ea = _ea_str(d, mode, reg, sz, pc)
            return f"tst{sfx}   {ea}"

    # TAS
    if (op & 0xFFC0) == 0x4AC0:
        mode = (op >> 3) & 7
        reg = op & 7
        ea = _ea_str(d, mode, reg, SIZE_BYTE, pc)
        return f"tas     {ea}"

    # NBCD
    if (op & 0xFFC0) == 0x4800:
        mode = (op >> 3) & 7
        reg = op & 7
        ea = _ea_str(d, mode, reg, SIZE_BYTE, pc)
        return f"nbcd    {ea}"

    # MOVE from SR
    if (op & 0xFFC0) == 0x40C0:
        mode = (op >> 3) & 7
        reg = op & 7
        ea = _ea_str(d, mode, reg, SIZE_WORD, pc)
        return f"move.w  sr,{ea}"

    # MOVE to CCR
    if (op & 0xFFC0) == 0x44C0:
        mode = (op >> 3) & 7
        reg = op & 7
        ea = _ea_str(d, mode, reg, SIZE_WORD, pc)
        return f"move.w  {ea},ccr"

    # MOVE to SR
    if (op & 0xFFC0) == 0x46C0:
        mode = (op >> 3) & 7
        reg = op & 7
        ea = _ea_str(d, mode, reg, SIZE_WORD, pc)
        return f"move.w  {ea},sr"

    raise DecodeError(f"unknown group4 op=${op:04x}")


def _decode_group5(d: _Decoder, op: int, pc: int) -> str:
    """ADDQ, SUBQ, Scc, DBcc"""
    size_bits = (op >> 6) & 3

    if size_bits == 3:
        # Scc, DBcc, or TRAPcc
        condition = (op >> 8) & 0xF
        mode = (op >> 3) & 7
        reg = op & 7

        if mode == 1:
            # DBcc
            disp = d.read_i16()
            target = _branch_target(pc, disp)
            cc = _cc_name(condition)
            return f"db{cc}    d{reg},{target}"
        elif mode == 7 and reg in (2, 3, 4):
            # TRAPcc (68020+)
            cc = _cc_name(condition)
            if reg == 2:
                imm = d.read_u16()
                return f"trap{cc}.w #${imm:04x}"
            elif reg == 3:
                imm = d.read_u32()
                return f"trap{cc}.l #${imm:08x}"
            else:  # reg == 4
                return f"trap{cc}"
        else:
            # Scc
            ea = _ea_str(d, mode, reg, SIZE_BYTE, pc)
            cc = _cc_name(condition)
            return f"s{cc}     {ea}"
    else:
        # ADDQ / SUBQ
        data = (op >> 9) & 7
        if data == 0:
            data = 8
        is_sub = op & 0x0100
        name = "subq" if is_sub else "addq"
        sfx = SIZE_SUFFIX[size_bits]
        mode = (op >> 3) & 7
        reg = op & 7
        ea = _ea_str(d, mode, reg, size_bits, pc)
        return f"{name}{sfx} #{data},{ea}"


CC_NAMES = ["t", "f", "hi", "ls", "cc", "cs", "ne", "eq",
            "vc", "vs", "pl", "mi", "ge", "lt", "gt", "le"]

def _cc_name(cc: int) -> str:
    return CC_NAMES[cc]


def _decode_group6(d: _Decoder, op: int, pc: int) -> str:
    """Bcc, BSR, BRA"""
    condition = (op >> 8) & 0xF
    disp8 = op & 0xFF

    if disp8 == 0:
        disp = d.read_i16()
        sfx = ".w"
    elif disp8 == 0xFF:
        # 68020+ long branch
        disp = d.read_i32()
        sfx = ".l"
    else:
        disp = disp8 if disp8 < 128 else disp8 - 256
        sfx = ".s"

    target = _branch_target(pc, disp)

    if condition == 0:
        return f"bra{sfx}   {target}"
    elif condition == 1:
        return f"bsr{sfx}   {target}"
    else:
        cc = _cc_name(condition)
        return f"b{cc}{sfx}    {target}"


def _decode_moveq(d: _Decoder, op: int, pc: int) -> str:
    """MOVEQ"""
    if op & 0x0100:
        raise DecodeError(f"invalid moveq ${op:04x}")
    reg = (op >> 9) & 7
    data = op & 0xFF
    if data & 0x80:
        data -= 256
    return f"moveq   #{data},d{reg}"


def _decode_group8(d: _Decoder, op: int, pc: int) -> str:
    """OR, DIV, SBCD"""
    reg = (op >> 9) & 7
    opmode = (op >> 6) & 7
    mode = (op >> 3) & 7
    ea_reg = op & 7

    if opmode == 3:
        # DIVU
        ea = _ea_str(d, mode, ea_reg, SIZE_WORD, pc)
        return f"divu.w  {ea},d{reg}"
    elif opmode == 7:
        # DIVS
        ea = _ea_str(d, mode, ea_reg, SIZE_WORD, pc)
        return f"divs.w  {ea},d{reg}"

    if opmode == 0 and mode == 0 and not (op & 0x01F0):
        # Could be SBCD Dy,Dx
        pass

    # SBCD
    if (op & 0xF1F0) == 0x8100:
        ry = op & 7
        rx = (op >> 9) & 7
        if op & 8:
            return f"sbcd    -(a{ry}),-(a{rx})"
        return f"sbcd    d{ry},d{rx}"

    # OR
    sz = opmode if opmode < 3 else opmode - 4
    sfx = SIZE_SUFFIX[sz]
    ea = _ea_str(d, mode, ea_reg, sz, pc)
    if opmode < 3:
        return f"or{sfx}    {ea},d{reg}"
    else:
        return f"or{sfx}    d{reg},{ea}"


def _decode_sub(d: _Decoder, op: int, pc: int) -> str:
    """SUB, SUBA, SUBX"""
    reg = (op >> 9) & 7
    opmode = (op >> 6) & 7
    mode = (op >> 3) & 7
    ea_reg = op & 7

    # SUBA
    if opmode == 3:
        ea = _ea_str(d, mode, ea_reg, SIZE_WORD, pc)
        return f"suba.w  {ea},a{reg}"
    if opmode == 7:
        ea = _ea_str(d, mode, ea_reg, SIZE_LONG, pc)
        return f"suba.l  {ea},a{reg}"

    # SUBX
    if (op & 0xF130) == 0x9100 and (mode == 0 or mode == 1):
        ry = op & 7
        rx = (op >> 9) & 7
        sz = (op >> 6) & 3
        sfx = SIZE_SUFFIX[sz]
        if mode == 1:
            return f"subx{sfx} -(a{ry}),-(a{rx})"
        return f"subx{sfx} d{ry},d{rx}"

    # SUB
    sz = opmode if opmode < 3 else opmode - 4
    sfx = SIZE_SUFFIX[sz]
    ea = _ea_str(d, mode, ea_reg, sz, pc)
    if opmode < 3:
        return f"sub{sfx}   {ea},d{reg}"
    else:
        return f"sub{sfx}   d{reg},{ea}"


def _decode_cmp_eor(d: _Decoder, op: int, pc: int) -> str:
    """CMP, CMPA, CMPM, EOR"""
    reg = (op >> 9) & 7
    opmode = (op >> 6) & 7
    mode = (op >> 3) & 7
    ea_reg = op & 7

    # CMPA
    if opmode == 3:
        ea = _ea_str(d, mode, ea_reg, SIZE_WORD, pc)
        return f"cmpa.w  {ea},a{reg}"
    if opmode == 7:
        ea = _ea_str(d, mode, ea_reg, SIZE_LONG, pc)
        return f"cmpa.l  {ea},a{reg}"

    # CMPM
    if opmode in (4, 5, 6) and mode == 1:
        sz = opmode - 4
        sfx = SIZE_SUFFIX[sz]
        return f"cmpm{sfx} (a{ea_reg})+,(a{reg})+"

    # EOR (direction bit set, not CMPA)
    if opmode >= 4:
        sz = opmode - 4
        sfx = SIZE_SUFFIX[sz]
        ea = _ea_str(d, mode, ea_reg, sz, pc)
        return f"eor{sfx}   d{reg},{ea}"

    # CMP
    sz = opmode
    sfx = SIZE_SUFFIX[sz]
    ea = _ea_str(d, mode, ea_reg, sz, pc)
    return f"cmp{sfx}   {ea},d{reg}"


def _decode_group_c(d: _Decoder, op: int, pc: int) -> str:
    """AND, MUL, ABCD, EXG"""
    reg = (op >> 9) & 7
    opmode = (op >> 6) & 7
    mode = (op >> 3) & 7
    ea_reg = op & 7

    # MULU
    if opmode == 3:
        ea = _ea_str(d, mode, ea_reg, SIZE_WORD, pc)
        return f"mulu.w  {ea},d{reg}"
    # MULS
    if opmode == 7:
        ea = _ea_str(d, mode, ea_reg, SIZE_WORD, pc)
        return f"muls.w  {ea},d{reg}"

    # ABCD
    if (op & 0xF1F0) == 0xC100:
        ry = op & 7
        rx = (op >> 9) & 7
        if op & 8:
            return f"abcd    -(a{ry}),-(a{rx})"
        return f"abcd    d{ry},d{rx}"

    # EXG
    if (op & 0xF100) == 0xC100:
        exg_mode = (op >> 3) & 0x1F
        ry = op & 7
        rx = (op >> 9) & 7
        if exg_mode == 0x08:  # Dx,Dy
            return f"exg     d{rx},d{ry}"
        elif exg_mode == 0x09:  # Ax,Ay
            return f"exg     a{rx},a{ry}"
        elif exg_mode == 0x11:  # Dx,Ay
            return f"exg     d{rx},a{ry}"

    # AND
    sz = opmode if opmode < 3 else opmode - 4
    sfx = SIZE_SUFFIX[sz]
    ea = _ea_str(d, mode, ea_reg, sz, pc)
    if opmode < 3:
        return f"and{sfx}   {ea},d{reg}"
    else:
        return f"and{sfx}   d{reg},{ea}"


def _decode_add(d: _Decoder, op: int, pc: int) -> str:
    """ADD, ADDA, ADDX"""
    reg = (op >> 9) & 7
    opmode = (op >> 6) & 7
    mode = (op >> 3) & 7
    ea_reg = op & 7

    # ADDA
    if opmode == 3:
        ea = _ea_str(d, mode, ea_reg, SIZE_WORD, pc)
        return f"adda.w  {ea},a{reg}"
    if opmode == 7:
        ea = _ea_str(d, mode, ea_reg, SIZE_LONG, pc)
        return f"adda.l  {ea},a{reg}"

    # ADDX
    if (op & 0xF130) == 0xD100 and (mode == 0 or mode == 1):
        ry = op & 7
        rx = (op >> 9) & 7
        sz = (op >> 6) & 3
        sfx = SIZE_SUFFIX[sz]
        if mode == 1:
            return f"addx{sfx} -(a{ry}),-(a{rx})"
        return f"addx{sfx} d{ry},d{rx}"

    # ADD
    sz = opmode if opmode < 3 else opmode - 4
    sfx = SIZE_SUFFIX[sz]
    ea = _ea_str(d, mode, ea_reg, sz, pc)
    if opmode < 3:
        return f"add{sfx}   {ea},d{reg}"
    else:
        return f"add{sfx}   d{reg},{ea}"


def _decode_shift(d: _Decoder, op: int, pc: int) -> str:
    """ASd, LSd, ROd, ROXd"""
    size_bits = (op >> 6) & 3

    if size_bits == 3:
        # Memory shift (word only, shift by 1)
        direction = "l" if op & 0x0100 else "r"
        shift_type = (op >> 9) & 3
        names = ["as", "ls", "rox", "ro"]
        mode = (op >> 3) & 7
        reg = op & 7
        ea = _ea_str(d, mode, reg, SIZE_WORD, pc)
        return f"{names[shift_type]}{direction}.w  {ea}"

    # Register shift
    direction = "l" if op & 0x0100 else "r"
    shift_type = (op >> 3) & 3
    names = ["as", "ls", "rox", "ro"]
    sfx = SIZE_SUFFIX[size_bits]
    dreg = op & 7
    count_or_reg = (op >> 9) & 7

    if op & 0x0020:
        # Shift by register
        return f"{names[shift_type]}{direction}{sfx}  d{count_or_reg},d{dreg}"
    else:
        # Shift by immediate
        count = count_or_reg if count_or_reg != 0 else 8
        return f"{names[shift_type]}{direction}{sfx}  #{count},d{dreg}"



# --- Line-F (coprocessor / 68040) ---

# MC68851 PMMU condition codes (from PDF Table 10-1)
PMMU_CC = [
    "bs", "bc", "ls", "lc", "ss", "sc", "as", "ac",
    "ws", "wc", "is", "ic", "gs", "gc", "cs", "cc",
]


def _decode_line_f(d: _Decoder, op: int, pc: int) -> str:
    """Line-F: coprocessor (FPU/MMU), MOVE16, etc."""
    cpid = (op >> 9) & 7

    # MOVE16 (68040): 1111 0110 0...
    if (op & 0xFE00) == 0xF600:
        if op & 0x0020:
            # Postincrement: 1111 0110 0010 0 AX(3)
            ax = op & 7
            ext = d.read_u16()
            ay = (ext >> 12) & 7
            return f"move16  (a{ax})+,(a{ay})+"
        else:
            # Absolute long forms: 1111 0110 000 OPMODE(2) AN(3)
            opmode = (op >> 3) & 3
            an = op & 7
            addr = d.read_u32()
            if opmode == 0:
                return f"move16  (a{an})+,${addr:08x}.l"
            elif opmode == 1:
                return f"move16  ${addr:08x}.l,(a{an})+"
            elif opmode == 2:
                return f"move16  (a{an}),${addr:08x}.l"
            elif opmode == 3:
                return f"move16  ${addr:08x}.l,(a{an})"

    # MMU (cpid=0): PRESTORE/PSAVE/PBcc/PDBcc/PScc/PTRAPcc/PFLUSH/PFLUSHR
    if cpid == 0:
        type_bits = (op >> 6) & 7
        mode = (op >> 3) & 7
        reg = op & 7

        if type_bits == 5:
            # PRESTORE: 1111 000 101 MODE(3) REG(3)
            ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
            return f"prestore {ea}"

        if type_bits == 4:
            # PSAVE: 1111 000 100 MODE(3) REG(3)
            ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
            return f"psave   {ea}"

        if type_bits in (2, 3):
            # PBcc: 1111 000 01 SIZE(1) COND(6)
            # type_bits bit 0 = SIZE (0=word, 1=long)
            cond = op & 0x3F
            cc = PMMU_CC[cond] if cond < 16 else f"#{cond}"
            if type_bits == 2:
                disp = d.read_i16()
                target = _branch_target(pc, disp)
                return f"pb{cc}.w  {target}"
            else:
                disp = d.read_i32()
                target = _branch_target(pc, disp)
                return f"pb{cc}.l  {target}"

        if type_bits == 1:
            # PScc/PDBcc/PTRAPcc: 1111 0000 01 MODE(3) REG(3)
            ext = d.read_u16()
            cond = ext & 0x3F
            cc = PMMU_CC[cond] if cond < 16 else f"#{cond}"
            if mode == 1:
                # PDBcc: 1111 0000 0100 1 REG(3)
                disp = d.read_i16()
                target = _branch_target(pc, disp)
                return f"pdb{cc}   d{reg},{target}"
            elif mode == 7 and reg in (2, 3, 4):
                # PTRAPcc
                if reg == 2:
                    imm = d.read_u16()
                    return f"ptrap{cc}.w #{imm}"
                elif reg == 3:
                    imm = d.read_u32()
                    return f"ptrap{cc}.l #{imm}"
                else:
                    return f"ptrap{cc}"
            else:
                ea = _ea_str(d, mode, reg, SIZE_BYTE, pc)
                return f"ps{cc}    {ea}"

        if type_bits == 0:
            # PFLUSH/PFLUSHA/PFLUSHR or PMMU general
            ext = d.read_u16()
            if (ext & 0xE000) == 0x2000:
                # PFLUSH: ext = 001 MODE(2) 0 MASK(3) FC(4)
                pflush_mode = (ext >> 10) & 3
                mask = (ext >> 5) & 7
                fc = ext & 0x1F
                if pflush_mode == 1:
                    return "pflusha"
                ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
                return f"pflush  #{fc},#{mask},{ea}"
            elif ext == 0xA000:
                # PFLUSHR
                ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
                return f"pflushr {ea}"
            # Other PMMU general commands (PMOVE, PLOAD, PTEST, PVALID)
            raise DecodeError(f"unsupported PMMU command: op=${op:04x} ext=${ext:04x}")

    # FPU (cpid=1): FRESTORE/FSAVE
    if cpid == 1:
        type_bits = (op >> 6) & 7
        mode = (op >> 3) & 7
        reg = op & 7

        if type_bits == 5:
            # FRESTORE
            ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
            return f"frestore {ea}"

        if type_bits == 4:
            # FSAVE
            ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
            return f"fsave   {ea}"

        # Other FPU instructions (cpGEN etc.) — not yet decoded
        raise DecodeError(f"unsupported FPU command: op=${op:04x}")

    raise DecodeError(f"unsupported line-F op=${op:04x}")


# --- Public API ---

def disassemble(data: bytes, base_offset: int = 0, max_cpu: str | None = None) -> list[Instruction]:
    """Disassemble M68K code from raw bytes."""
    d = _Decoder(data, base_offset)
    instructions = []
    while d.remaining() >= 2:
        inst = _decode_one(d, max_cpu)
        instructions.append(inst)
    return instructions


def format_instruction(inst: Instruction, labels: dict[int, str] | None = None) -> str:
    """Format instruction for vasm-compatible output."""
    hex_bytes = " ".join(f"{b:02x}" for b in inst.raw[:8])
    if labels and inst.offset in labels:
        label = f"{labels[inst.offset]}:"
    else:
        label = ""
    return f"{label:20s}    {inst.text:40s} ; {inst.offset:06x}: {hex_bytes}"


if __name__ == "__main__":
    import sys
    from hunk_parser import parse_file, HunkType as HT

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hunk_file>")
        sys.exit(1)

    hf = parse_file(sys.argv[1])
    for hunk in hf.hunks:
        if hunk.hunk_type != HT.HUNK_CODE:
            continue
        print(f"; === Hunk #{hunk.index} CODE ({len(hunk.data)} bytes) ===")
        # Build label map from symbols
        labels = {s.value: s.name for s in hunk.symbols}
        instructions = disassemble(hunk.data)
        for inst in instructions:
            print(format_instruction(inst, labels))
        print()
