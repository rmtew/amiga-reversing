"""Parse instruction syntax patterns from m68k_instructions.json into structured forms.

Each instruction's `syntax` field (from the PDF) is parsed into `forms`:
structured descriptions of operand types that can drive test generation
and simulation.

Adds to each instruction:
  "forms": [
    {
      "syntax": "ADD <ea>,Dn",         # normalized
      "operands": [                     # ordered list
        {"type": "ea", "role": "src"},
        {"type": "dn", "role": "dst"}
      ]
    },
    ...
  ]

Also adds:
  "affects": {                          # derived from operation field
    "reads": ["src", "dst", "X"],       # what the instruction reads
    "writes": ["dst", "X", "N", "Z", "V", "C"],  # what it writes
    "reads_pc": false,
    "writes_pc": false,
    "reads_sp": false,
    "writes_sp": false,
    "privileged": false
  }

Usage:
    python parse_syntax_patterns.py [--dry-run]
"""

import json
import re
import sys
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent.parent
KB_PATH = PROJ_ROOT / "knowledge" / "m68k_instructions.json"


def normalize_syntax(raw):
    """Normalize a raw PDF syntax string."""
    s = raw.strip()
    # Remove leading asterisks (marks 020+ variants)
    s = s.lstrip("*").strip()
    # Normalize angle brackets: "< ea >" -> "<ea>"
    s = re.sub(r"<\s*(\w+)\s*>", r"<\1>", s)
    # Normalize spaces around commas
    s = re.sub(r"\s*,\s*", ",", s)
    # Normalize "– (Ax)" -> "-(Ax)"
    s = re.sub(r"–\s*\(", "-(", s)
    # Normalize "(Ay) +" -> "(Ay)+"
    s = re.sub(r"\)\s*\+", ")+", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s)
    return s


def parse_operand(token):
    """Parse a single operand token into a type descriptor.

    Returns dict with 'type' and optional extra fields.
    """
    t = token.strip()
    tl = t.lower()

    if t in ("<ea>",):
        return {"type": "ea"}
    if t in ("<label>",):
        return {"type": "label"}
    if re.match(r"^#\s*<?\s*(data|vector|displacement)\s*>?$", t):
        return {"type": "imm"}
    if t.startswith("#"):
        return {"type": "imm"}
    if t in ("CCR", "ccr"):
        return {"type": "ccr"}
    if t in ("SR", "sr"):
        return {"type": "sr"}
    if t in ("USP", "usp"):
        return {"type": "usp"}
    if re.match(r"^[Dd][0-7nxylhqr]?$", t):
        return {"type": "dn"}
    if re.match(r"^[Aa][0-7nxy]$", t):
        return {"type": "an"}
    if re.match(r"^-\([Aa][0-7xy]\)$", t):
        return {"type": "predec"}
    if re.match(r"^\([Aa][0-7xy]\)\+$", t):
        return {"type": "postinc"}
    if re.match(r"^\(d?\d+,[Aa][0-7xy]\)$", t):
        return {"type": "disp"}
    # Dh–Dl or Dh-Dl (long multiply/divide pair)
    if re.match(r"^[Dd]\w+\s*[–-]\s*[Dd]\w+$", t):
        return {"type": "dn_pair"}
    if t == "<list>":
        return {"type": "reglist"}
    # Dr:Dq pattern (long divide/multiply)
    if re.match(r"^[Dd]\w+:[Dd]\w+$", t):
        return {"type": "dn_pair"}

    return {"type": "unknown", "raw": t}


def split_concatenated_forms(syntax_list, mnemonic):
    """Split concatenated syntax entries into separate forms.

    The PDF sometimes concatenates multiple forms into one string, e.g.:
      "EXG Ax,Ay EXG Dx,Ay" -> ["EXG Ax,Ay", "EXG Dx,Ay"]
      "ROd #<data>,Dy ROd <ea> where d is..." -> ["ROd #<data>,Dy", "ROd <ea>"]

    Returns list of (syntax_str, is_020plus) tuples.
    """
    result = []
    base = mnemonic.split(",")[0].split()[0]  # "ASL, ASR" -> "ASL"

    for raw_s in syntax_list:
        # Detect * prefix marking 020+ forms before normalization strips it
        is_020 = raw_s.strip().startswith("*")

        s = normalize_syntax(raw_s)
        # Skip descriptive lines and footnotes
        if s.lower().startswith("where ") or s.lower().startswith("applies to"):
            continue
        if s.strip() in ("→", "->"):
            continue

        # Try to split on repeated mnemonic patterns
        # Look for a second occurrence of a mnemonic-like word after the first
        parts_to_add = [s]

        # Check for concatenated forms: "INST ops INST ops"
        # Find all positions where a word matches the base mnemonic pattern
        words = s.split()
        if len(words) > 2:
            splits = []
            for i, w in enumerate(words):
                w_base = w.split(".")[0].upper()
                # Match mnemonic variants (ASd, LSd, ROd, ROXd, etc.)
                # or exact mnemonic
                if i > 0 and (w_base == base.upper() or
                              w_base.rstrip("DLRS") == base.upper().rstrip("DLRS")):
                    splits.append(i)

            if splits:
                # Split at each occurrence
                parts_to_add = []
                prev = 0
                for split_idx in splits:
                    chunk = " ".join(words[prev:split_idx]).strip()
                    if chunk:
                        parts_to_add.append(chunk)
                    prev = split_idx
                chunk = " ".join(words[prev:]).strip()
                if chunk:
                    parts_to_add.append(chunk)

        result.extend((p, is_020) for p in parts_to_add)

    return result


def parse_syntax_to_form(mnemonic, syntax_str):
    """Parse a single syntax string into a structured form.

    Returns dict with 'syntax' and 'operands', or None if unparseable.
    """
    s = normalize_syntax(syntax_str)

    # Skip descriptive lines
    if s.lower().startswith("where ") or s.startswith("Applies to"):
        return None
    if s.strip() in ("→", "->"):
        return None

    # Split into mnemonic and operands
    parts = s.split(None, 1)
    if not parts:
        return None

    inst_name = parts[0]

    # Validate that the first word looks like the instruction mnemonic
    # (with optional .size suffix). Skip continuation lines like "MC68040,CPU32)"
    base_mnemonic = mnemonic.split(",")[0].split()[0]  # "EXT, EXTB" -> "EXT"
    inst_base = inst_name.split(".")[0].upper().lstrip("*")
    known_variants = {base_mnemonic.upper()}
    # Add variant mnemonics (e.g., "EXTB" from "EXT, EXTB")
    for part in mnemonic.split(","):
        for word in part.strip().split():
            known_variants.add(word.upper())
    if inst_base not in known_variants:
        # Handle PDF 'd' suffix convention: ASd = ASL/ASR, ROXd = ROXL/ROXR
        # The PDF uses 'd' as a placeholder for direction (L/R)
        if not (inst_base.endswith("D") and any(
            v.startswith(inst_base[:-1]) and len(v) == len(inst_base)
            for v in known_variants
        )):
            return None

    operand_str = parts[1] if len(parts) > 1 else ""

    # Remove trailing descriptions from the full operand string
    # before splitting on commas (e.g., "where d is direction, L or R")
    operand_str = re.sub(r"\s+where\s+.*$", "", operand_str, flags=re.IGNORECASE)
    operand_str = re.sub(r"\s*(?:→|->).*$", "", operand_str)

    if not operand_str:
        return {"syntax": s, "operands": []}

    # Split operands by comma (respecting parentheses),
    # then clean up each token
    tokens = split_operands(operand_str)
    operands = []
    for tok in tokens:
        # Clean trailing descriptions from this token
        # Allow zero-width match before digits (PDF concatenates "Dn32/16...")
        tok = re.sub(r"\s*\d+\s*[/x]\s*\d+.*$", "", tok)
        tok = re.sub(r"\s*(?:→|->).*$", "", tok)
        tok = re.sub(r"\s*extend\s+.*$", "", tok, flags=re.IGNORECASE)
        tok = re.sub(r"\s*\(MC68.*$", "", tok)
        tok = re.sub(r"\s*MC68.*$", "", tok)
        tok = re.sub(r"\s*where\s+.*$", "", tok, flags=re.IGNORECASE)
        tok = tok.strip()
        if not tok:
            continue
        op = parse_operand(tok)
        operands.append(op)

    return {"syntax": s, "operands": operands}


def split_operands(s):
    """Split operand string by commas, respecting parentheses."""
    parts = []
    depth = 0
    current = []
    for ch in s:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return parts


def parse_operation_effects(operation, condition_codes, mnemonic):
    """Parse the operation field into structured read/write effects."""
    effects = {
        "reads_pc": False,
        "writes_pc": False,
        "reads_sp": False,
        "writes_sp": False,
        "privileged": False,
    }

    op = operation

    # PC effects
    if "→ PC" in op or "-> PC" in op:
        effects["writes_pc"] = True
    if "PC +" in op or "PC →" in op or "PC ->" in op:
        effects["reads_pc"] = True

    # SP effects (SP or SSP)
    if "SP –" in op or "SP -" in op or "SP +" in op:
        effects["reads_sp"] = True
        effects["writes_sp"] = True
    if "→ SP" in op or "-> SP" in op:
        effects["writes_sp"] = True
    if "(SP)" in op or "(SSP)" in op:
        effects["reads_sp"] = True
    if "SSP" in op:
        effects["reads_sp"] = True
        effects["writes_sp"] = True

    # Privilege
    if "Supervisor State" in op or "S-Bit" in op:
        effects["privileged"] = True

    # Condition code effects from the condition_codes dict
    cc_read = []
    cc_write = []
    dash = "—"
    for flag in ("X", "N", "Z", "V", "C"):
        val = condition_codes.get(flag, dash)
        if val == dash or val == "Not affected" or val == "Undefined":
            continue
        # "Set the same as the carry bit" -> reads C, writes X
        if "same as" in val.lower():
            cc_write.append(flag)
        elif "unchanged" in val.lower():
            pass  # conditionally unchanged means it may be read
        else:
            cc_write.append(flag)

    effects["cc_write"] = cc_write

    return effects


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    with open(KB_PATH, encoding="utf-8") as f:
        kb_data = json.load(f)

    for inst in kb_data:
        mnemonic = inst["mnemonic"]
        syntax_list = inst.get("syntax", [])

        # Split concatenated forms, then parse each
        split_syntaxes = split_concatenated_forms(syntax_list, mnemonic)
        forms = []
        for syn, is_020 in split_syntaxes:
            form = parse_syntax_to_form(mnemonic, syn)
            if form:
                if is_020:
                    form["processor_020"] = True
                forms.append(form)
        inst["forms"] = forms

        # Parse operation effects
        effects = parse_operation_effects(
            inst.get("operation", ""),
            inst.get("condition_codes", {}),
            mnemonic,
        )
        inst["effects"] = effects

    # Report
    with_forms = sum(1 for i in kb_data if i["forms"])
    total_forms = sum(len(i["forms"]) for i in kb_data)
    with_pc = sum(1 for i in kb_data if i["effects"]["writes_pc"])
    with_sp = sum(1 for i in kb_data if i["effects"]["writes_sp"])
    priv = sum(1 for i in kb_data if i["effects"]["privileged"])

    print(f"Instructions with forms: {with_forms}/{len(kb_data)}")
    print(f"Total forms: {total_forms}")
    print(f"Writes PC: {with_pc}, Writes SP: {with_sp}, Privileged: {priv}")
    print()

    for inst in kb_data:
        if inst.get("processor_min") != "68000":
            continue
        forms = inst["forms"]
        eff = inst["effects"]
        flags = []
        if eff["writes_pc"]:
            flags.append("PC")
        if eff["writes_sp"]:
            flags.append("SP")
        if eff["privileged"]:
            flags.append("PRIV")
        if eff["cc_write"]:
            flags.append(f"CC:{''.join(eff['cc_write'])}")

        form_strs = []
        for f in forms:
            ops = ", ".join(o["type"] for o in f["operands"])
            form_strs.append(f"({ops})" if ops else "()")
        print(f"  {inst['mnemonic']:25s} forms={' | '.join(form_strs):40s} {' '.join(flags)}")

    if not args.dry_run:
        with open(KB_PATH, "w", encoding="utf-8") as f:
            json.dump(kb_data, f, indent=2, ensure_ascii=False)
        print(f"\nUpdated {KB_PATH}")
    else:
        print("\n(dry run)")


if __name__ == "__main__":
    main()
