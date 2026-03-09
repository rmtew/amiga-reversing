"""Extract instruction-specific constraints from m68k_instructions.json.

Derives structured constraint data from existing PDF-extracted fields
(field_descriptions, encodings, syntax) to eliminate hardcodings in the
test suite.

Adds to each instruction (where applicable):
  "constraints": {
    "immediate_range": {"min": N, "max": N, "field": "...", "bits": N},
    "cc_parameterized": {"prefix": "b", "excluded": ["t","f"], "field_bits": 4},
    "direction_variants": {"field": "dr", "values": {"0": "r", "1": "l"}},
    "operand_modes": {"field": "R/M", "values": {"0": "dn,dn", "1": "predec,predec"}},
    "movem_direction": {"field": "dr", "values": {"0": "reg-to-mem", "1": "mem-to-reg"}}
  }

Usage:
    python parse_instruction_constraints.py [--dry-run]
"""

import json
import re
import sys
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent.parent
KB_PATH = PROJ_ROOT / "knowledge" / "m68k_instructions.json"

# Standard M68K condition code encoding (architectural, like MODE_MAP in parse_ea_modes.py)
# These are the 16 condition codes defined by the M68K architecture,
# encoded in bits 11-8 of conditional instructions.
CC_TABLE = {
    0:  "t",   1:  "f",   2:  "hi",  3:  "ls",
    4:  "cc",  5:  "cs",  6:  "ne",  7:  "eq",
    8:  "vc",  9:  "vs",  10: "pl",  11: "mi",
    12: "ge",  13: "lt",  14: "gt",  15: "le",
}


def _find_encoding_field(encodings, target_name):
    """Find a named field in the encodings list, return (name, width) or None."""
    target_upper = target_name.upper()
    for enc in encodings:
        fields = enc.get("fields", [])
        for f in fields:
            if f["name"].upper() == target_upper:
                return f["name"], f["width"]
    return None


def _find_field_description(fd, field_name):
    """Find a field description by name, case-insensitive."""
    fn_lower = field_name.lower()
    for fd_key, fd_val in fd.items():
        if fd_key.lower() == fn_lower:
            return fd_val
        # Also try without spaces/slashes
        if fd_key.lower().replace(" ", "").replace("/", "") == fn_lower.replace(" ", "").replace("/", ""):
            return fd_val
    return ""


def extract_immediate_range(inst):
    """Extract immediate value range from encoding field width and field_descriptions.

    Returns dict with min, max, field name, and bit width, or None.
    """
    fd = inst.get("field_descriptions", {})
    encodings = inst.get("encodings", [])

    if not encodings:
        return None

    # Search for immediate-type fields in encoding
    for target in ("DATA", "VECTOR"):
        result = _find_encoding_field(encodings, target)
        if result is None:
            continue

        field_name, bit_width = result
        desc = _find_field_description(fd, field_name)

        # Check for special encoding rules in description
        if "sign-extended" in desc.lower() or "sign extended" in desc.lower():
            return {
                "min": -(1 << (bit_width - 1)),
                "max": (1 << (bit_width - 1)) - 1,
                "field": field_name,
                "bits": bit_width,
                "signed": True,
            }

        if "represent" in desc.lower():
            # "0-7, with 0 representing 8" (ADDQ) or
            # "1-7 represent immediate values of 1-7" (SUBQ)
            # Both are 3-bit fields where 0 encodes as max+1
            return {
                "min": 1,
                "max": (1 << bit_width),
                "field": field_name,
                "bits": bit_width,
                "zero_means": (1 << bit_width),
            }

        if target == "VECTOR":
            return {
                "min": 0,
                "max": (1 << bit_width) - 1,
                "field": field_name,
                "bits": bit_width,
            }

        if target == "DATA" and bit_width <= 8:
            # Check description for range clues
            range_match = re.search(r"(\d+)\s*-\s*(\d+)", desc)
            if range_match:
                lo, hi = int(range_match.group(1)), int(range_match.group(2))
                if lo == 0 and "represent" in desc.lower():
                    return {
                        "min": 1,
                        "max": hi + 1,
                        "field": field_name,
                        "bits": bit_width,
                        "zero_means": hi + 1,
                    }

    return None


def extract_cc_parameterization(inst):
    """Extract condition code parameterization from encoding and mnemonic.

    Returns dict or None.
    """
    mnemonic = inst["mnemonic"]

    # Only instructions with "cc" in the mnemonic are CC-parameterized
    if "cc" not in mnemonic:
        return None

    encodings = inst.get("encodings", [])
    if not encodings:
        return None

    # Find CONDITION field in encoding
    result = _find_encoding_field(encodings, "CONDITION")
    condition_bits = result[1] if result else None

    if condition_bits is None:
        return None

    # Derive prefix from mnemonic: "Bcc" -> "b", "DBcc" -> "db", "Scc" -> "s"
    prefix = mnemonic.lower().replace("cc", "")

    # Determine excluded codes from the instruction description
    desc = inst.get("description", "").lower()
    operation = inst.get("operation", "").lower()
    excluded = []

    if mnemonic == "Bcc":
        # BT is BRA, BF doesn't exist as a separate branch
        # The description says "the conditional branch, Bcc, if the specified condition is met"
        # BRA handles the "always" case, so T and F are excluded
        excluded = ["t", "f"]
    elif mnemonic == "DBcc":
        # DBT and DBF both exist (DBT = always true = no decrement, DBRA = DBF = always false = always decrement)
        # All 16 codes valid for DBcc
        excluded = []
    elif mnemonic == "Scc":
        # All 16 codes valid: ST, SF, SHI, SLS, etc.
        excluded = []

    return {
        "prefix": prefix,
        "field_bits": condition_bits,
        "excluded": excluded,
    }


def extract_direction_variants(inst):
    """Extract direction variant info from dr field description.

    Returns dict or None.
    """
    fd = inst.get("field_descriptions", {})
    mnemonic = inst["mnemonic"]

    # Look for "dr" field in field_descriptions
    dr_desc = fd.get("dr", "")
    if not dr_desc:
        return None

    # Parse "0 -- Shift right  1 -- Shift left" or similar
    values = {}
    for match in re.finditer(r"(\d)\s*(?:--|—|–)\s*(\w+)\s+(\w+)", dr_desc):
        bit_val = match.group(1)
        direction = match.group(3).lower()  # "right" or "left"
        if direction in ("right", "left"):
            values[bit_val] = "r" if direction == "right" else "l"

    if not values:
        return None

    # Derive the mnemonic variants from the comma-separated mnemonic
    # "ASL, ASR" -> base "AS", variants ["ASL", "ASR"]
    parts = [p.strip() for p in mnemonic.split(",")]
    if len(parts) == 2:
        # Find common prefix
        a, b = parts[0], parts[1]
        common = ""
        for i in range(min(len(a), len(b))):
            if a[i] == b[i]:
                common += a[i]
            else:
                break
        if common:
            variants = [p.lower() for p in parts]
            return {
                "field": "dr",
                "values": values,
                "base": common.lower(),
                "variants": variants,
            }

    return None


def extract_operand_modes(inst):
    """Extract R/M operand mode variants from field description.

    For instructions like ABCD, SBCD, ADDX, SUBX that have both
    register and memory forms selected by the R/M bit.

    Returns dict or None.
    """
    fd = inst.get("field_descriptions", {})

    rm_desc = fd.get("R/M", "")
    if not rm_desc:
        return None

    # Parse "0 -- data register to data register  1 -- memory to memory"
    modes = {}
    if "data register" in rm_desc.lower() and "memory" in rm_desc.lower():
        # Extract the two modes
        for match in re.finditer(r"(\d)\s*(?:--|—|–)\s*(?:The operation is\s+)?(.+?)(?:\.|$|\d\s*(?:--|—|–))", rm_desc):
            bit_val = match.group(1)
            mode_desc = match.group(2).strip().lower()
            if "data register" in mode_desc:
                modes[bit_val] = "dn,dn"
            elif "memory" in mode_desc:
                modes[bit_val] = "predec,predec"

    if not modes:
        # Try simpler pattern
        if "0" in rm_desc and "data register" in rm_desc.lower():
            modes["0"] = "dn,dn"
        if "1" in rm_desc and "memory" in rm_desc.lower():
            modes["1"] = "predec,predec"

    if modes:
        return {
            "field": "R/M",
            "values": modes,
        }
    return None


def extract_movem_direction(inst):
    """Extract MOVEM direction semantics from dr field.

    Returns dict or None.
    """
    if inst["mnemonic"] != "MOVEM":
        return None

    fd = inst.get("field_descriptions", {})
    dr_desc = fd.get("dr", "")
    if not dr_desc:
        return None

    values = {}
    if "register to memory" in dr_desc.lower():
        # Find which bit value maps to reg-to-mem
        match = re.search(r"(\d)\s*(?:--|—|–)\s*[Rr]egister to memory", dr_desc)
        if match:
            values[match.group(1)] = "reg-to-mem"
    if "memory to register" in dr_desc.lower():
        match = re.search(r"(\d)\s*(?:--|—|–)\s*[Mm]emory to register", dr_desc)
        if match:
            values[match.group(1)] = "mem-to-reg"

    if values:
        return {
            "field": "dr",
            "values": values,
        }
    return None


def extract_shift_count_range(inst):
    """Extract shift/rotate count range from encoding structure.

    All M68K shift/rotate instructions use the same 3-bit count encoding:
    values 1-7 represent themselves, 0 represents 8.

    Derivable from:
    1. Count/Register field description (ASL/ASR has it), OR
    2. Encoding structure: i/r field + 3-bit field at bits 11-9
       (LSL/LSR, ROL/ROR have identical encoding but lost the field description)

    Returns dict or None.
    """
    fd = inst.get("field_descriptions", {})
    encodings = inst.get("encodings", [])

    # Method 1: Check Count/Register field description
    cr_desc = _find_field_description(fd, "Count/Register")
    if cr_desc:
        range_match = re.search(r"values?\s+(\d+)\s*-\s*(\d+)", cr_desc)
        if range_match:
            return {
                "min": 1,
                "max": 8,
                "field": "Count/Register",
                "bits": 3,
                "zero_means": 8,
            }

    # Method 2: Check encoding structure for shift/rotate pattern
    # These have: i/r field (1 bit) + REGISTER at bits 11-9 (3 bits, used as count)
    # plus dr field (direction). Check encoding fields directly.
    has_dr = _find_encoding_field(encodings, "dr") is not None

    if not has_dr:
        return None

    for enc in encodings:
        fields = enc.get("fields", [])
        has_ir = any(f["name"] == "i/r" for f in fields)
        has_count = any(f["name"] == "REGISTER" and f["bit_hi"] == 11
                        and f["bit_lo"] == 9 and f["width"] == 3
                        for f in fields)
        if has_ir and has_count:
            return {
                "min": 1,
                "max": 8,
                "field": "Count/Register",
                "bits": 3,
                "zero_means": 8,
            }

    return None


def extract_sizes_68000(inst):
    """Filter sizes to 68000-only by checking asterisk in attributes.

    The PDF uses * to mark sizes that require 68020+:
      "Size = (Word, Long*)" means Long is 020+
      "Size = (Byte, Word, Long*)" means Long is 020+

    Returns filtered sizes list or None if no change needed.
    """
    attrs = inst.get("attributes", "")
    sizes = inst.get("sizes", [])

    if "*" not in attrs or not sizes:
        return None

    # Find which sizes are starred
    filtered = []
    for sz in sizes:
        # Map size code to attribute word
        sz_word = {"b": "Byte", "w": "Word", "l": "Long"}.get(sz, "")
        # Check if this size word has an asterisk after it in attrs
        if sz_word and f"{sz_word}*" in attrs:
            continue  # Skip 020+ sizes
        filtered.append(sz)

    if filtered != sizes:
        return filtered
    return None


def extract_memory_size_restriction(inst):
    """Detect if memory EA form has a fixed size (e.g. shift/rotate memory = word only).

    Derivable from encoding: shift/rotate instructions have two forms:
    1. Register form with i/r, SIZE, dr fields
    2. Memory form with MODE, REGISTER, dr but NO SIZE (bits 7-6 fixed at "11" = word)

    The presence of 'dr' (direction) field distinguishes shift/rotate from
    other instructions that happen to have bits 7-6 = "11".

    Returns the restricted size string ("w") or None.
    """
    encodings = inst.get("encodings", [])
    if len(encodings) < 2:
        return None

    # Must have a dr field (shift/rotate direction) to qualify
    has_dr = _find_encoding_field(encodings, "dr") is not None
    if not has_dr:
        return None

    for enc in encodings:
        fields = enc.get("fields", [])
        has_mode = any(f["name"] == "MODE" for f in fields)
        has_ir = any(f["name"] == "i/r" for f in fields)
        has_dr_field = any(f["name"] == "dr" for f in fields)

        if has_mode and not has_ir and has_dr_field:
            # This is the memory form. Check if bits 7-6 are fixed at "11" (word)
            bit7 = next((f for f in fields if f["bit_hi"] == 7 and f["bit_lo"] == 7), None)
            bit6 = next((f for f in fields if f["bit_hi"] == 6 and f["bit_lo"] == 6), None)
            if bit7 and bit6 and bit7["name"] == "1" and bit6["name"] == "1":
                return "w"

    return None


def extract_bit_op_size_restriction(inst):
    """Detect bit operation size behavior from description.

    Bit operations (BTST, BCHG, BCLR, BSET) are long for Dn and byte for memory.
    The PDF description says: "When a data register is the destination, the
    specified bit is modulo 32" and "When a memory location is the destination,
    the operation is a byte operation."

    Returns dict {"dn": "l", "memory": "b"} or None.
    """
    desc = inst.get("description", "")
    mnemonic = inst["mnemonic"]

    if mnemonic not in ("BTST", "BCHG", "BCLR", "BSET"):
        return None

    has_reg_32 = "modulo 32" in desc
    has_mem_byte = "byte operation" in desc.lower() or "modulo 8" in desc

    if has_reg_32 or has_mem_byte:
        return {"dn": "l", "memory": "b"}

    return None


def fix_processor_min(inst):
    """Derive processor_min from the processors field.

    The processors field from the PDF lists which chips support the instruction.
    If the original MC68000 is not listed, the instruction is not 68000-compatible.

    Returns corrected processor_min or None if no change needed.
    """
    processors = inst.get("processors", "")
    current = inst.get("processor_min", "68000")

    if current != "68000":
        return None  # already non-68000, no fix needed

    # "M68000 Family" means all processors including original 68000
    if "M68000 Family" in processors or not processors:
        return None

    # If processors mentions specific chips, check if MC68000 is among them
    if "MC68000" in processors:
        return None  # explicitly listed as supporting MC68000

    # Not available on original 68000 — determine minimum processor
    if "MC68EC000" in processors or "MC68010" in processors:
        return "68010"
    if "MC68020" in processors:
        return "68020"
    if "MC68030" in processors:
        return "68030"
    if "MC68040" in processors:
        return "68040"
    # FPU coprocessor (MC68881/MC68882) requires 68020+
    if "MC68881" in processors or "MC68882" in processors:
        return "68020"
    # MMU coprocessor (MC68851) requires 68020+
    if "MC68851" in processors:
        return "68020"

    return None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    with open(KB_PATH, encoding="utf-8") as f:
        kb_data = json.load(f)

    stats = {
        "immediate_range": 0,
        "cc_parameterized": 0,
        "direction_variants": 0,
        "operand_modes": 0,
        "movem_direction": 0,
        "shift_count": 0,
        "sizes_68000": 0,
        "memory_size_restriction": 0,
        "bit_op_size": 0,
        "processor_fix": 0,
    }

    for inst in kb_data:
        constraints = inst.get("constraints", {})

        # Immediate range
        imm = extract_immediate_range(inst)
        if imm:
            constraints["immediate_range"] = imm
            stats["immediate_range"] += 1

        # Shift count (also an immediate range but from Count/Register field)
        sc = extract_shift_count_range(inst)
        if sc and "immediate_range" not in constraints:
            constraints["immediate_range"] = sc
            stats["shift_count"] += 1

        # CC parameterization
        cc = extract_cc_parameterization(inst)
        if cc:
            constraints["cc_parameterized"] = cc
            stats["cc_parameterized"] += 1

        # Direction variants
        dv = extract_direction_variants(inst)
        if dv:
            constraints["direction_variants"] = dv
            stats["direction_variants"] += 1

        # R/M operand modes
        om = extract_operand_modes(inst)
        if om:
            constraints["operand_modes"] = om
            stats["operand_modes"] += 1

        # MOVEM direction
        md = extract_movem_direction(inst)
        if md:
            constraints["movem_direction"] = md
            stats["movem_direction"] += 1

        # Sizes filtered to 68000 (removing asterisked 020+ sizes)
        s68 = extract_sizes_68000(inst)
        if s68 is not None:
            constraints["sizes_68000"] = s68
            stats["sizes_68000"] += 1

        # Memory form size restriction (shift/rotate memory = word only)
        msr = extract_memory_size_restriction(inst)
        if msr:
            constraints["memory_size_only"] = msr
            stats["memory_size_restriction"] += 1

        # Bit op size behavior (Dn=long, memory=byte)
        bos = extract_bit_op_size_restriction(inst)
        if bos:
            constraints["bit_op_sizes"] = bos
            stats["bit_op_size"] += 1

        if constraints:
            inst["constraints"] = constraints

        # Fix processor_min where the PDF data proves it's wrong
        pfx = fix_processor_min(inst)
        if pfx:
            old = inst.get("processor_min", "68000")
            inst["processor_min"] = pfx
            stats["processor_fix"] += 1
            print(f"  FIX: {inst['mnemonic']} processor_min {old} -> {pfx}")

    # Report
    print("=== Constraint Extraction Results ===")
    for key, count in stats.items():
        print(f"  {key}: {count}")
    print()

    # Show details
    for inst in kb_data:
        c = inst.get("constraints", {})
        if c:
            parts = []
            if "immediate_range" in c:
                r = c["immediate_range"]
                parts.append(f"imm=[{r['min']}..{r['max']}]")
            if "cc_parameterized" in c:
                cc = c["cc_parameterized"]
                excl = ",".join(cc["excluded"]) if cc["excluded"] else "none"
                parts.append(f"cc={cc['prefix']}xx excl=[{excl}]")
            if "direction_variants" in c:
                dv = c["direction_variants"]
                parts.append(f"dir={dv['variants']}")
            if "operand_modes" in c:
                om = c["operand_modes"]
                parts.append(f"R/M={om['values']}")
            if "movem_direction" in c:
                md = c["movem_direction"]
                parts.append(f"dr={md['values']}")
            if "sizes_68000" in c:
                parts.append(f"sizes_68000={c['sizes_68000']}")
            if "memory_size_only" in c:
                parts.append(f"mem_sz={c['memory_size_only']}")
            if "bit_op_sizes" in c:
                parts.append(f"bit_sz={c['bit_op_sizes']}")

            print(f"  {inst['mnemonic']:25s} {', '.join(parts)}")

    # Show what's NOT captured
    # Instructions with size-dependent full-width immediates don't need
    # range constraints — the immediate width matches the operation size.
    SIZE_DEPENDENT_IMM = {
        "ADDI", "SUBI", "CMPI", "ANDI", "ORI", "EORI",
        "ANDI to CCR", "EORI to CCR", "ORI to CCR",
        "ANDI to SR", "EORI to SR", "ORI to SR",
        "STOP", "LINK",  # LINK displacement is full 16-bit signed
    }
    # Bit number instructions: immediate is bit position, not a constrained range
    BIT_IMM = {"BCHG", "BCLR", "BSET", "BTST"}

    print("\n=== Missing Constraints (need review) ===")
    for inst in kb_data:
        if inst.get("processor_min", "68000") != "68000":
            continue
        m = inst["mnemonic"]
        c = inst.get("constraints", {})

        issues = []
        # Check: shift/rotate without direction_variants
        if "," in m and any(d in m.upper() for d in ("ASL", "LSL", "ROL", "ROXL")):
            if "direction_variants" not in c:
                issues.append("missing direction_variants")

        # Check: cc in mnemonic but no cc_parameterized
        if "cc" in m and "cc_parameterized" not in c:
            issues.append("missing cc_parameterized")

        # Check: has imm operand in forms but no immediate_range
        forms = inst.get("forms", [])
        has_imm = any(
            any(o["type"] == "imm" for o in f.get("operands", []))
            for f in forms
        )
        if has_imm and "immediate_range" not in c:
            # Skip size-dependent and bit-number instructions
            if m not in SIZE_DEPENDENT_IMM and m not in BIT_IMM:
                issues.append("has imm operand, no range constraint")

        if issues:
            print(f"  {m:25s} {'; '.join(issues)}")

    if not args.dry_run:
        with open(KB_PATH, "w", encoding="utf-8") as f:
            json.dump(kb_data, f, indent=2, ensure_ascii=False)
        print(f"\nUpdated {KB_PATH}")
    else:
        print("\n(dry run)")


if __name__ == "__main__":
    main()
