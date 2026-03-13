#!/usr/bin/env py.exe
"""Parse Amiga NDK 3.1 + OS_CHANGES into structured JSON knowledge base.

Parses:
- FD files: function names, register args, LVO offsets, private flags
- Autodocs: full function documentation (synopsis, description, inputs, results)
- Include files (.I): struct definitions with computed offsets, constants with evaluation
- TYPES.I: type size macros (parsed, not hardcoded)
- OS_CHANGES: version tagging (1.3 -> 2.04 -> 2.1 -> 3.0 -> 3.1 transitions)

Outputs: knowledge/amiga_os_reference.json
"""

import os
import re
import json
import sys
import argparse

sys.stdout.reconfigure(encoding="utf-8")


# =============================================================================
# TYPES.I parser — extract type sizes from macro definitions
# =============================================================================

def scan_type_macros(include_dir: str) -> dict:
    """Scan all .I files for structure-building type macros.

    A type macro is any macro whose body contains `SOFFSET SET SOFFSET+N`
    (direct size) or delegates to another known type macro (e.g. BPTR
    expands to `LONG \\1`).

    Two passes: first collects direct sizes and delegation targets,
    second resolves delegated types.
    """
    # Non-type macros that happen to appear in the same files
    skip_macros = {"STRUCTURE", "ENUM", "EITEM", "BITDEF", "BITDEF0",
                   "EXTERN_LIB", "DOSNAME", "IFND", "IFD"}

    # Pass 1: scan all .I files for macro definitions
    # Collect: direct_sizes {name: int} and delegates {name: delegate_target}
    direct_sizes = {}
    delegates = {}

    for dirpath, _dirnames, filenames in os.walk(include_dir):
        for fname in sorted(filenames):
            if not fname.upper().endswith(".I"):
                continue
            fpath = os.path.join(dirpath, fname)
            current_macro = None
            macro_body = []

            with open(fpath, encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.rstrip()

                    # Macro start: TYPE_NAME MACRO
                    m = re.match(r'^(\w+)\s+MACRO', line)
                    if m:
                        name = m.group(1)
                        if name in skip_macros:
                            current_macro = None
                        else:
                            current_macro = name
                            macro_body = []
                        continue

                    if current_macro is None:
                        continue

                    # End of macro
                    if re.match(r'\s+ENDM', line):
                        # Analyze collected body
                        found_soffset = False
                        delegate_target = None
                        for bline in macro_body:
                            sm = re.match(
                                r'^SOFFSET\s+SET\s+SOFFSET\+(\d+)', bline)
                            if sm:
                                direct_sizes[current_macro] = int(sm.group(1))
                                found_soffset = True
                                break
                            # Delegation: line is just `TYPE_NAME \1` or
                            # `TYPE_NAME  \1` (invoke another type macro)
                            dm = re.match(r'\s+(\w+)\s+\\1\s*$', bline)
                            if dm:
                                delegate_target = dm.group(1)
                        if not found_soffset and delegate_target:
                            delegates[current_macro] = delegate_target
                        elif not found_soffset:
                            # No SOFFSET and no delegation -> size 0 (LABEL)
                            direct_sizes[current_macro] = 0
                        current_macro = None
                        continue

                    macro_body.append(line)

    # Pass 2: resolve delegated types
    type_sizes = dict(direct_sizes)
    for _ in range(10):  # convergence guard
        changed = False
        for name, target in delegates.items():
            if name not in type_sizes and target in type_sizes:
                type_sizes[name] = type_sizes[target]
                changed = True
        if not changed:
            break

    # Any remaining unresolved delegates
    for name, target in delegates.items():
        if name not in type_sizes:
            print(f"  WARNING: type macro {name} delegates to {target} "
                  f"which has unknown size", file=sys.stderr)
            type_sizes[name] = 0

    return type_sizes


# =============================================================================
# FD file parser
# =============================================================================

LVO_SLOT_SIZE = 6  # Each library vector slot is a JMP.L instruction (6 bytes).
# Parser-asserted: ROM Kernel Reference Manual, Libraries 3rd Ed, Ch28
# "Library Vectors". Each vector entry is JMP absolute.long = 2 opword + 4 addr.


def parse_fd_file(path: str) -> dict:
    """Parse a .FD file to extract function definitions with LVO offsets."""
    functions = {}
    base_name = ""
    bias = 0
    public = True
    since_version = None

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()
            if not line:
                continue

            # Track version markers in comments
            if line.startswith("*"):
                vm = re.search(
                    r'(?:[Nn]ew|[Aa]dded)\s+(?:functions?\s+)?(?:for|as of)\s+'
                    r'(?:[Rr]elease\s+|[Vv]ersion\s+|[Vv])(\d[\d.]*)',
                    line
                )
                if vm:
                    since_version = vm.group(1)
                vm2 = re.match(r'\*[-\s]*(\d\.\d)\s+[Nn]ew\b', line)
                if vm2:
                    since_version = vm2.group(1)
                continue

            if line.startswith("##base"):
                base_name = line.split()[-1].lstrip("_")
                continue
            if line.startswith("##bias"):
                bias = int(line.split()[-1])
                continue
            if line.startswith("##private"):
                public = False
                continue
            if line.startswith("##public"):
                public = True
                continue
            if line.startswith("##end"):
                break

            # Parse function: Name(args)(regs) or Name()()
            m = re.match(r"(\w+)\(([^)]*)\)\(([^)]*)\)", line)
            if m:
                name = m.group(1)
                args = [a.strip() for a in m.group(2).split(",") if a.strip()]
                regs = [r.strip().upper() for r in m.group(3).replace("/", ",").split(",") if r.strip()]
                entry = {
                    "lvo": -bias,
                    "args": args,
                    "regs": regs,
                }
                if not public:
                    entry["private"] = True
                if since_version:
                    entry["since"] = since_version
                functions[name] = entry
                bias += LVO_SLOT_SIZE

    return {"base": base_name, "functions": functions}


# =============================================================================
# Autodoc parser
# =============================================================================

def parse_autodoc(path: str) -> dict:
    """Parse an autodoc file to extract function documentation.

    Format: entries separated by form feed (0x0C), each starting with
    library.type/FuncName header.
    """
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    entries = {}
    parts = content.split('\x0c')

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Try double-name format: "exec.library/AllocMem\t\t\texec.library/AllocMem"
        header_m = re.match(r'(\w[\w.]+/)(\w+)\s+\1\2', part)
        if not header_m:
            # Single-name format: "dos.library/Close"
            header_m = re.match(r'(\w[\w.]+/)(\w+)\s*$', part, re.MULTILINE)
        if not header_m:
            continue

        lib_prefix = header_m.group(1).rstrip("/")
        func_name = header_m.group(2)
        doc = {}

        # Extract sections
        sections = re.split(r'\n\s{2,4}([A-Z][A-Z ]+)\n', part)
        for i in range(1, len(sections) - 1, 2):
            section_name = sections[i].strip()
            section_body = sections[i + 1].rstrip()
            lines = section_body.split("\n")
            cleaned = []
            for line in lines:
                if line.startswith("\t"):
                    line = line[1:]
                cleaned.append(line.rstrip())
            body = "\n".join(cleaned).strip()

            if section_name == "NAME":
                doc["name_desc"] = body
            elif section_name == "SYNOPSIS":
                doc["synopsis"] = body
            elif section_name == "FUNCTION":
                doc["description"] = body
            elif section_name == "INPUTS":
                doc["inputs_text"] = body
            elif section_name in ("RESULTS", "RESULT"):
                doc["results_text"] = body
            elif section_name in ("NOTE", "NOTES"):
                doc["notes"] = body
            elif section_name == "BUGS":
                doc["bugs"] = body
            elif section_name == "SEE ALSO":
                doc["see_also"] = body
            elif section_name == "WARNING":
                doc["warning"] = body

        doc["_lib_prefix"] = lib_prefix
        entries[func_name] = doc

    return entries


# =============================================================================
# Synopsis parser — structured inputs/outputs from autodoc synopsis
# =============================================================================

def parse_synopsis(synopsis: str, arg_names: list, arg_regs: list) -> dict:
    """Parse autodoc SYNOPSIS text into structured input/output data."""
    result = {"inputs": [], "output": None}
    if not synopsis:
        return result

    lines = synopsis.strip().split('\n')
    if not lines:
        return result

    # Parse line 1: return name
    line1 = lines[0].strip()
    ret_match = re.match(r'(\w+)\s*=\s*\w+\s*\(', line1)
    ret_name = ret_match.group(1) if ret_match else None

    # Parse line 2: register assignments
    ret_reg = None
    if len(lines) >= 2:
        reg_line = lines[1]
        reg_tokens = [(m.start(), m.group().upper()) for m in re.finditer(r'[DdAa]\d', reg_line)]
        if ret_name and reg_tokens:
            ret_reg = reg_tokens[0][1]

    # Parse C prototype for types
    c_proto = None
    c_type_decls = []
    for line in lines:
        line_s = line.strip()
        proto_m = re.match(r'(.+?)\s+\*?\s*\w+\s*\((.+)\)\s*;', line_s)
        if proto_m:
            c_proto = line_s
            continue
        decl_m = re.match(r'((?:struct\s+|unsigned\s+)?\w+)\s*(\*?)\s*(\w+)\s*;', line_s)
        if decl_m:
            typ = decl_m.group(1).strip()
            ptr = decl_m.group(2)
            name = decl_m.group(3)
            if ptr:
                typ += " *"
            c_type_decls.append((name, typ))

    type_map = {name: typ for name, typ in c_type_decls}

    # Extract arg types from C prototype
    arg_types_from_proto = []
    if c_proto:
        proto_m = re.match(r'(.+?)\b(\w+)\s*\((.+)\)\s*;', c_proto)
        if proto_m:
            ret_type_str = proto_m.group(1).strip()
            if ret_type_str.endswith('*'):
                ret_type_str = ret_type_str.rstrip('*').strip() + " *"
            arg_str = proto_m.group(3)
            arg_types_from_proto = [a.strip() for a in arg_str.split(',')]
            if ret_name and ret_type_str:
                result["output"] = {
                    "name": ret_name,
                    "reg": ret_reg,
                    "type": ret_type_str,
                }
        elif ret_name:
            result["output"] = {"name": ret_name, "reg": ret_reg}
    elif ret_name:
        ret_type = type_map.get(ret_name)
        result["output"] = {"name": ret_name, "reg": ret_reg}
        if ret_type:
            result["output"]["type"] = ret_type

    # Build structured inputs
    for i, (aname, areg) in enumerate(zip(arg_names, arg_regs)):
        inp = {"name": aname, "reg": areg.upper()}
        if i < len(arg_types_from_proto):
            inp["type"] = arg_types_from_proto[i]
        elif aname in type_map:
            inp["type"] = type_map[aname]
        result["inputs"].append(inp)

    return result


# =============================================================================
# No-return detection
# =============================================================================

def check_no_return(doc: dict) -> bool:
    """Check if autodoc text indicates the function never returns.

    Looks in FUNCTION and NOTES sections for definitive statements that
    THIS function does not return. Must avoid:
    - "does not return until..." (conditional wait)
    - "does not return correct values" (returns wrong thing)
    - "may never return" (conditional)
    - "programs may never return" (about callers, not this function)
    """
    # Patterns that definitively indicate no-return, anchored to
    # "this function" or sentence-final position
    definitive_patterns = [
        # "This function never returns." or "This function never returns"
        re.compile(
            r'\b(?:this\s+(?:function|routine|call))\s+never\s+returns?\s*[.\n]',
            re.IGNORECASE,
        ),
        # "This function does not return." (sentence-final)
        re.compile(
            r'\b(?:this\s+(?:function|routine|call))\s+does\s+not\s+return\s*[.\n]',
            re.IGNORECASE,
        ),
        # Standalone "never returns." at end of sentence (common brief form)
        re.compile(r'^\s*\w+\(?\)?\s+never\s+returns?\s*\.', re.IGNORECASE | re.MULTILINE),
    ]

    for key in ("description", "notes"):
        text = doc.get(key, "")
        if not text:
            continue
        for pat in definitive_patterns:
            if pat.search(text):
                return True
    return False


# =============================================================================
# Include file parser (structs and constants) — with offset computation
# =============================================================================

def parse_asm_include(path: str, type_sizes: dict, all_constants: dict) -> dict:
    """Parse .I (asm) include file for struct definitions and constants.

    Computes byte offsets for struct fields using type_sizes from scan_type_macros.
    """
    structs = {}
    constants = {}
    current_struct = None
    current_fields = []
    current_offset = 0

    # Build regex matching any known type macro with size > 0
    # (excludes STRUCT, LABEL, ALIGNWORD, ALIGNLONG which are handled separately)
    sized_types = sorted(
        (t for t, s in type_sizes.items()
         if s > 0 and t not in ("STRUCT", "ALIGNWORD", "ALIGNLONG")),
        key=len, reverse=True,  # longest first to avoid prefix ambiguity
    )
    if sized_types:
        type_alt = "|".join(re.escape(t) for t in sized_types)
        type_field_re = re.compile(rf'\s+({type_alt})\s+(\w+)')
    else:
        type_field_re = re.compile(r'(?!)')  # never matches

    # Track the source subpath (e.g. "exec/NODES.I")
    rel_parts = path.replace("\\", "/").split("/")
    # Find INCLUDE_I in path
    try:
        idx = [p.upper() for p in rel_parts].index("INCLUDE_I")
        source = "/".join(rel_parts[idx + 1:])
    except ValueError:
        source = os.path.basename(path)

    def finish_struct():
        nonlocal current_struct, current_fields, current_offset
        if current_struct and current_fields:
            structs[current_struct] = {
                "source": source,
                "size": current_offset,
                "fields": current_fields,
            }
        current_struct = None
        current_fields = []
        current_offset = 0

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()

            # STRUCTURE definition start: STRUCTURE Name,InitialOffset
            m = re.match(r'\s+STRUCTURE\s+(\w+),(\w+)', line)
            if m:
                finish_struct()
                current_struct = m.group(1)
                init_offset_str = m.group(2)
                # Initial offset can be a constant name (e.g. LIB_SIZE)
                # or a number
                try:
                    current_offset = int(init_offset_str)
                except ValueError:
                    resolved = resolve_constant_value(init_offset_str, all_constants)
                    if resolved is not None:
                        current_offset = resolved
                    else:
                        print(f"  WARNING: struct {current_struct} initial offset "
                              f"'{init_offset_str}' unresolved, skipping struct",
                              file=sys.stderr)
                        current_struct = None
                        continue
                current_fields = []
                continue

            # Struct field types
            if current_struct is not None:
                # Match any known type macro (from scan_type_macros)
                # that isn't STRUCT/LABEL/ALIGNWORD/ALIGNLONG (handled below)
                fm = type_field_re.match(line)
                if fm:
                    ftype = fm.group(1)
                    fname = fm.group(2)
                    fsize = type_sizes[ftype]
                    current_fields.append({
                        "name": fname,
                        "type": ftype,
                        "offset": current_offset,
                        "size": fsize,
                    })
                    current_offset += fsize
                    continue

                # STRUCT name,size — embedded sub-structure
                sm = re.match(r'\s+STRUCT\s+(\w+),(\w+)', line)
                if sm:
                    fname = sm.group(1)
                    size_str = sm.group(2)
                    try:
                        fsize = int(size_str)
                    except ValueError:
                        resolved = resolve_constant_value(size_str, all_constants)
                        if resolved is not None:
                            fsize = resolved
                        else:
                            print(f"  WARNING: struct {current_struct} field "
                                  f"{fname} STRUCT size '{size_str}' unresolved",
                                  file=sys.stderr)
                            fsize = 0
                    current_fields.append({
                        "name": fname,
                        "type": "STRUCT",
                        "offset": current_offset,
                        "size": fsize,
                    })
                    current_offset += fsize
                    continue

                # LABEL name — zero-size marker
                lm = re.match(r'\s+LABEL\s+(\w+)', line)
                if lm:
                    fname = lm.group(1)
                    current_fields.append({
                        "name": fname,
                        "type": "LABEL",
                        "offset": current_offset,
                        "size": 0,
                    })
                    continue

                # ALIGNWORD
                if re.match(r'\s+ALIGNWORD\b', line):
                    current_offset = (current_offset + 1) & ~1
                    continue

                # ALIGNLONG
                if re.match(r'\s+ALIGNLONG\b', line):
                    current_offset = (current_offset + 3) & ~3
                    continue

                # DS.B / DS.W / DS.L — data storage (rare in structs but possible)
                dm = re.match(r'\s+DS\.\w\s+', line)
                if dm:
                    continue

                # End of struct detection: non-empty, non-comment line that's
                # not a recognized struct directive -> end the struct
                stripped = line.strip()
                if stripped and not stripped.startswith("*") and not stripped.startswith(";"):
                    # But allow blank lines and comments within structs
                    # Check if this line could be part of struct (EQU inside struct, etc.)
                    if not re.match(r'\s+(DS|CNOP)', line):
                        finish_struct()

            # EQU constants
            cm = re.match(r'^(\w+)\s+[Ee][Qq][Uu]\s+(.+?)(?:\s*[;*].*)?$', line)
            if cm:
                name = cm.group(1)
                value = cm.group(2).strip()
                constants[name] = value
                continue

            # SET constants (skip include guards ending in _I)
            cm = re.match(r'^(\w+)\s+SET\s+(.+?)(?:\s*[;*].*)?$', line)
            if cm:
                name = cm.group(1)
                value = cm.group(2).strip()
                if not name.endswith("_I") and name != "SOFFSET" and name != "EOFFSET":
                    constants[name] = value

    finish_struct()
    return {"structs": structs, "constants": constants}


# =============================================================================
# Constant evaluation
# =============================================================================

def resolve_constant_value(expr: str, all_constants: dict, depth: int = 0) -> int | None:
    """Resolve a constant expression to an integer value.

    Handles:
    - Decimal literals
    - Hex ($xxxx or 0x...)
    - Binary (%xxxx)
    - Simple arithmetic: +, -, *, <<, >>, |, &, ~
    - References to other constants
    - Parenthesized expressions
    """
    if depth > 20:
        return None

    expr = expr.strip()
    if not expr:
        return None

    # Direct integer literal
    try:
        return int(expr)
    except ValueError:
        pass

    # Hex: $xxxx
    m = re.match(r'^\$([0-9a-fA-F]+)$', expr)
    if m:
        return int(m.group(1), 16)

    # Hex: 0x...
    m = re.match(r'^0x([0-9a-fA-F]+)$', expr, re.IGNORECASE)
    if m:
        return int(m.group(1), 16)

    # Binary: %xxxx
    m = re.match(r'^%([01]+)$', expr)
    if m:
        return int(m.group(1), 2)

    # Bitwise NOT: ~expr
    m = re.match(r'^~(.+)$', expr)
    if m:
        val = resolve_constant_value(m.group(1), all_constants, depth + 1)
        if val is not None:
            return ~val & 0xFFFFFFFF
        return None

    # Strip outer parens
    if expr.startswith('(') and expr.endswith(')'):
        inner = expr[1:-1]
        # Check balanced
        depth_count = 0
        balanced = True
        for ch in inner:
            if ch == '(':
                depth_count += 1
            elif ch == ')':
                depth_count -= 1
                if depth_count < 0:
                    balanced = False
                    break
        if balanced and depth_count == 0:
            val = resolve_constant_value(inner, all_constants, depth + 1)
            if val is not None:
                return val

    # Binary operators (lowest precedence first): |, &, <<, >>, +, -, *
    # Split on operators respecting parentheses
    for ops in [('|',), ('&',), ('<<', '>>'), ('+', '-'), ('*',)]:
        pos = find_operator(expr, ops)
        if pos is not None:
            op_str, op_pos, op_len = pos
            left = expr[:op_pos].strip()
            right = expr[op_pos + op_len:].strip()
            lval = resolve_constant_value(left, all_constants, depth + 1)
            rval = resolve_constant_value(right, all_constants, depth + 1)
            if lval is not None and rval is not None:
                if op_str == '|':
                    return lval | rval
                elif op_str == '&':
                    return lval & rval
                elif op_str == '<<':
                    return (lval << rval) & 0xFFFFFFFF
                elif op_str == '>>':
                    return lval >> rval
                elif op_str == '+':
                    return lval + rval
                elif op_str == '-':
                    return lval - rval
                elif op_str == '*':
                    return lval * rval
            return None

    # Single identifier — look up in constants
    m = re.match(r'^[A-Za-z_]\w*$', expr)
    if m:
        if expr in all_constants:
            raw = all_constants[expr]
            if isinstance(raw, dict):
                return raw.get("value")
            return resolve_constant_value(str(raw), all_constants, depth + 1)
        return None

    return None


def find_operator(expr: str, ops: tuple) -> tuple | None:
    """Find the rightmost occurrence of any operator in ops, outside parens.

    Returns (op_str, position, op_length) or None.
    For left-to-right evaluation, we want the rightmost split point
    (lowest precedence = split last).
    """
    depth = 0
    best = None
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif depth == 0:
            for op in ops:
                if expr[i:i + len(op)] == op:
                    # For - and +, don't match if it's the first char (unary)
                    if op in ('+', '-') and i == 0:
                        continue
                    # Don't match << when we're looking for < alone, etc.
                    best = (op, i, len(op))
        i += 1
    return best


def evaluate_all_constants(raw_constants: dict) -> dict:
    """Resolve all constants to integer values where possible.

    Returns dict of {name: {"raw": expr_str, "value": int_or_null}}.
    """
    result = {}
    for name, raw_expr in raw_constants.items():
        result[name] = {"raw": str(raw_expr), "value": None}

    # Multiple passes to resolve dependencies
    for _ in range(10):
        changed = False
        for name, entry in result.items():
            if entry["value"] is not None:
                continue
            val = resolve_constant_value(entry["raw"], result)
            if val is not None:
                entry["value"] = val
                changed = True
        if not changed:
            break

    return result


# =============================================================================
# OS_CHANGES parser (integrated)
# =============================================================================

def parse_change_file(path: str) -> dict:
    """Parse a single OS_CHANGES file."""
    result = {"added": {}, "new": {}, "removed": {}}

    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    sections = re.split(r'\n(?=(?:Added|Removed|New functions) in )', content)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        header_m = re.match(r'(Added|Removed|New functions) in ([\d.]+):', section)
        if not header_m:
            continue

        section_type = header_m.group(1).lower()
        if section_type == "added":
            target = result["added"]
        elif section_type == "removed":
            target = result["removed"]
        else:
            target = result["new"]

        current_lib = None
        for line in section.split('\n')[1:]:
            if not line.strip():
                continue
            tabs = len(line) - len(line.lstrip('\t'))
            stripped = line.strip()

            if tabs == 1 and not stripped.endswith('()') and '.' in stripped:
                lib_name = re.match(r'(\S+)', stripped).group(1)
                current_lib = lib_name
                if current_lib not in target:
                    target[current_lib] = []
                continue

            if tabs >= 2 and stripped.endswith('()') and current_lib:
                func_name = stripped.rstrip('()')
                target[current_lib].append(func_name)

    return result


def build_version_map(os_changes_dir: str) -> dict:
    """Build function->version mapping from all change files."""
    change_files = [
        ("1.3_TO_2.04", "2.04"),
        ("2.04_TO_2.1", "2.1"),
        ("2.1_TO_3.0", "3.0"),
        ("3.0_TO_3.1", "3.1"),
    ]

    libraries = {}
    removed = {}

    for filename, version in change_files:
        path = os.path.join(os_changes_dir, filename)
        if not os.path.exists(path):
            print(f"  Warning: {path} not found, skipping")
            continue

        changes = parse_change_file(path)

        for lib_name, funcs in changes["added"].items():
            if lib_name not in libraries:
                libraries[lib_name] = {"added_in": version, "functions": {}}
            else:
                libraries[lib_name]["added_in"] = version
            for func in funcs:
                libraries[lib_name]["functions"][func] = version

        for lib_name, funcs in changes["new"].items():
            if lib_name not in libraries:
                libraries[lib_name] = {"added_in": "pre-existing", "functions": {}}
            for func in funcs:
                libraries[lib_name]["functions"][func] = version

        for lib_name, funcs in changes["removed"].items():
            if lib_name not in removed:
                removed[lib_name] = {"removed_in": version, "functions": funcs}
            else:
                removed[lib_name]["functions"].extend(funcs)

    return {"libraries": libraries, "removed": removed}


# =============================================================================
# FD name -> library name mapping
# =============================================================================

# FD filename stem -> canonical library base name
FD_NAME_MAP = {
    "wb": "workbench",
    "cardres": "card",
}

# Library base name -> suffix override (when not .library)
SUFFIX_MAP = {
    "battclock": ".resource",
    "battmem": ".resource",
    "card": ".resource",
    "cia": ".resource",
    "disk": ".resource",
    "misc": ".resource",
    "potgo": ".resource",
    "console": ".device",
    "input": ".device",
    "timer": ".device",
    "ramdrive": ".device",
    "colorwheel": ".gadget",
    "gradientslider": ".gadget",
}


def fd_stem_to_lib_name(fd_stem: str) -> str:
    """Convert FD filename stem (e.g. 'exec') to full library name (e.g. 'exec.library')."""
    base = FD_NAME_MAP.get(fd_stem, fd_stem)
    suffix = SUFFIX_MAP.get(base, ".library")
    return base + suffix


# =============================================================================
# Autodoc -> library matching
# =============================================================================

def match_autodoc_to_lib(doc_filename: str, lib_names: set) -> str | None:
    """Match an autodoc filename (e.g. 'EXEC.DOC') to a library name.

    Strategy:
    1. Direct match: exec -> exec.library
    2. With suffix variations: .library, .device, .resource
    3. Special cases for gadget classes, datatypes
    4. FD name mapping (wb -> workbench, cardres -> card)
    """
    stem = doc_filename.replace(".DOC", "").lower()

    # Strip common suffixes from doc names
    stem = stem.replace("_gc", "")  # COLORWHEEL_GC.DOC -> colorwheel
    stem = stem.replace("_dtc", "")  # 8SVX_DTC.DOC -> 8svx
    stem = stem.replace("_lib", "")  # DEBUG_LIB.DOC -> debug

    # Apply FD name map (same aliases used for FD files)
    stem = FD_NAME_MAP.get(stem, stem)

    for suffix in (".library", ".device", ".resource", ".gadget", ".datatype"):
        candidate = stem + suffix
        if candidate in lib_names:
            return candidate

    # Try without suffix — some docs match library names directly
    for lib in lib_names:
        lib_base = lib.rsplit(".", 1)[0]
        if lib_base == stem:
            return lib

    return None


# =============================================================================
# Main: combine all sources
# =============================================================================

# Parser-asserted: Kickstart version to OS version mapping.
# ROM Kernel Reference Manual, Libraries 3rd Ed, Introduction.
# Kickstart internal version numbers correspond to marketed OS versions.
# V30=1.0, V33=1.2 derived from NDK 1.3 FD file version markers.
VERSION_MAP = {
    "30": "1.0", "33": "1.2", "34": "1.3",
    "36": "2.0", "37": "2.04", "39": "3.0", "40": "3.1", "44": "3.5",
}


def main():
    parser = argparse.ArgumentParser(
        description="Parse Amiga NDK 3.1 + OS_CHANGES into structured JSON"
    )
    parser.add_argument("ndk_root", help="Path to NDK root directory")
    parser.add_argument("--os-changes", help="Path to OS_CHANGES directory")
    parser.add_argument("--outfile", default="knowledge/amiga_os_reference.json")
    args = parser.parse_args()

    ndk_root = args.ndk_root
    fd_dir = os.path.join(ndk_root, "INCLUDES&LIBS", "FD")
    autodoc_dir = os.path.join(ndk_root, "DOCS", "DOC")
    include_dir = os.path.join(ndk_root, "INCLUDES&LIBS", "INCLUDE_I")

    print(f"NDK 3.1 at {ndk_root}")

    # ========================================================================
    # 1. Parse TYPES.I for type sizes
    # ========================================================================
    print("Scanning all .I files for type macros...")
    type_sizes = scan_type_macros(include_dir)
    print(f"  {len(type_sizes)} type macros: {dict(sorted(type_sizes.items()))}")

    # ========================================================================
    # 2. Parse all .I include files (ALL subdirectories)
    # ========================================================================
    print("Parsing include files...")
    raw_constants = {}  # name -> raw expression string
    raw_structs = {}    # name -> struct dict

    include_subdirs = sorted([
        d for d in os.listdir(include_dir)
        if os.path.isdir(os.path.join(include_dir, d))
    ])
    print(f"  Subdirectories: {', '.join(include_subdirs)}")

    # Build regex for struct field type matching from discovered type macros
    _sized_types = sorted(
        (t for t, s in type_sizes.items()
         if s > 0 and t not in ("STRUCT", "ALIGNWORD", "ALIGNLONG")),
        key=len, reverse=True,
    )
    _type_alt = "|".join(re.escape(t) for t in _sized_types)
    sim_type_re = re.compile(rf'\s+({_type_alt})\s+(\w+)') if _sized_types else None

    # First pass: collect all constants (needed for struct offset resolution).
    # This also simulates STRUCTURE macros to extract field-name constants
    # (e.g. LN_SUCC EQU 0, LN_SIZE EQU 14) which are generated at assembly
    # time by the macros in TYPES.I.
    # We run two iterations because struct initial offsets may reference
    # constants from other files (e.g. EXECBASE.I uses LIB_SIZE from
    # LIBRARIES.I, but is alphabetically first).
    for _pass_num in range(2):
      for subdir in include_subdirs:
        subdir_path = os.path.join(include_dir, subdir)
        for fname in sorted(os.listdir(subdir_path)):
            if fname.upper().endswith(".I"):
                fpath = os.path.join(subdir_path, fname)
                eoffset = 0
                soffset = 0  # simulates SOFFSET for struct field constants
                in_struct = False
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.rstrip()

                        # EQU constants
                        cm = re.match(r'^(\w+)\s+[Ee][Qq][Uu]\s+(.+?)(?:\s*[;*].*)?$', line)
                        if cm:
                            raw_constants[cm.group(1)] = cm.group(2).strip()
                            continue

                        # SET constants
                        cm = re.match(r'^(\w+)\s+SET\s+(.+?)(?:\s*[;*].*)?$', line)
                        if cm and not cm.group(1).endswith("_I") and cm.group(1) not in ("SOFFSET", "EOFFSET"):
                            raw_constants[cm.group(1)] = cm.group(2).strip()
                            continue

                        # BITDEF prefix,name,bitnum
                        bm = re.match(r'\s+BITDEF\s+(\w+),(\w+),(\d+)', line)
                        if bm:
                            prefix = bm.group(1)
                            name = bm.group(2)
                            bitnum = bm.group(3)
                            raw_constants[f"{prefix}B_{name}"] = bitnum
                            raw_constants[f"{prefix}F_{name}"] = f"(1<<{bitnum})"
                            continue

                        # ENUM [base]
                        enm = re.match(r'\s+ENUM\s*(?:(\S+))?\s*$', line)
                        if enm:
                            base_str = enm.group(1)
                            if base_str:
                                try:
                                    eoffset = int(base_str)
                                except ValueError:
                                    hm = re.match(r'^\$([0-9a-fA-F]+)$', base_str)
                                    if hm:
                                        eoffset = int(hm.group(1), 16)
                                    else:
                                        eoffset = 0
                            else:
                                eoffset = 0
                            continue

                        # EITEM label
                        em = re.match(r'\s+EITEM\s+(\w+)', line)
                        if em:
                            raw_constants[em.group(1)] = str(eoffset)
                            eoffset += 1
                            continue

                        # --- Struct macro simulation ---
                        # STRUCTURE Name,InitOffset -> sets SOFFSET, emits Name EQU 0
                        sm = re.match(r'\s+STRUCTURE\s+(\w+),(\w+)', line)
                        if sm:
                            struct_name = sm.group(1)
                            init_str = sm.group(2)
                            raw_constants[struct_name] = "0"
                            try:
                                soffset = int(init_str)
                            except ValueError:
                                # Try resolving from already-collected constants
                                if init_str in raw_constants:
                                    try:
                                        soffset = int(raw_constants[init_str])
                                    except (ValueError, TypeError):
                                        soffset = None
                                else:
                                    soffset = None
                            in_struct = True
                            continue

                        if in_struct and soffset is not None and sim_type_re:
                            # Type macros: NAME EQU SOFFSET; SOFFSET += size
                            tm = sim_type_re.match(line)
                            if tm:
                                raw_constants[tm.group(2)] = str(soffset)
                                soffset += type_sizes[tm.group(1)]
                                continue

                            # STRUCT name,size
                            ssm = re.match(r'\s+STRUCT\s+(\w+),(\w+)', line)
                            if ssm:
                                raw_constants[ssm.group(1)] = str(soffset)
                                size_str = ssm.group(2)
                                try:
                                    soffset += int(size_str)
                                except ValueError:
                                    # Try resolving from already-collected constants
                                    if size_str in raw_constants:
                                        try:
                                            soffset += int(raw_constants[size_str])
                                        except (ValueError, TypeError):
                                            in_struct = False
                                    else:
                                        in_struct = False
                                continue

                            # LABEL name
                            lm = re.match(r'\s+LABEL\s+(\w+)', line)
                            if lm:
                                raw_constants[lm.group(1)] = str(soffset)
                                continue

                            # ALIGNWORD
                            if re.match(r'\s+ALIGNWORD\b', line):
                                soffset = (soffset + 1) & ~1
                                continue

                            # ALIGNLONG
                            if re.match(r'\s+ALIGNLONG\b', line):
                                soffset = (soffset + 3) & ~3
                                continue

    print(f"  Raw constants collected: {len(raw_constants)}")

    # Evaluate constants
    evaluated_constants = evaluate_all_constants(raw_constants)
    resolved_count = sum(1 for v in evaluated_constants.values() if v["value"] is not None)
    print(f"  Constants resolved: {resolved_count}/{len(evaluated_constants)}")

    # Build a lookup for struct offset resolution (constant name -> int value)
    const_lookup = {}
    for name, entry in evaluated_constants.items():
        if entry["value"] is not None:
            const_lookup[name] = entry["value"]

    # Second pass: parse structs with offset computation
    for subdir in include_subdirs:
        subdir_path = os.path.join(include_dir, subdir)
        for fname in sorted(os.listdir(subdir_path)):
            if fname.upper().endswith(".I"):
                fpath = os.path.join(subdir_path, fname)
                result = parse_asm_include(fpath, type_sizes, const_lookup)
                for sname, sdata in result["structs"].items():
                    raw_structs[sname] = sdata

    print(f"  Structs: {len(raw_structs)}")

    # ========================================================================
    # 3. Parse FD files
    # ========================================================================
    print("Parsing FD files...")
    fd_data = {}  # lib_name -> {base, functions}
    if os.path.isdir(fd_dir):
        for fname in sorted(os.listdir(fd_dir)):
            if fname.endswith(".FD"):
                result = parse_fd_file(os.path.join(fd_dir, fname))
                raw_name = fname.replace("_LIB.FD", "").lower()
                lib_name = fd_stem_to_lib_name(raw_name)
                fd_data[lib_name] = result
    print(f"  {len(fd_data)} FD files parsed")

    # ========================================================================
    # 4. Parse autodocs
    # ========================================================================
    print("Parsing autodocs...")
    autodoc_data = {}  # lib_name -> {func_name: doc}
    autodoc_unmatched = {}
    lib_names_set = set(fd_data.keys())

    if os.path.isdir(autodoc_dir):
        for fname in sorted(os.listdir(autodoc_dir)):
            if fname.endswith(".DOC"):
                entries = parse_autodoc(os.path.join(autodoc_dir, fname))
                if not entries:
                    continue

                # Match to library
                lib_match = match_autodoc_to_lib(fname, lib_names_set)
                if lib_match:
                    if lib_match not in autodoc_data:
                        autodoc_data[lib_match] = {}
                    autodoc_data[lib_match].update(entries)
                else:
                    # Try matching via the _lib_prefix in the entries
                    for func_name, doc in entries.items():
                        prefix = doc.get("_lib_prefix", "")
                        if prefix:
                            prefix_lower = prefix.lower()
                            for ln in lib_names_set:
                                if prefix_lower == ln:
                                    if ln not in autodoc_data:
                                        autodoc_data[ln] = {}
                                    autodoc_data[ln][func_name] = doc
                                    break
                            else:
                                autodoc_unmatched[func_name] = doc
                        else:
                            autodoc_unmatched[func_name] = doc

    matched_funcs = sum(len(v) for v in autodoc_data.values())
    print(f"  {len(autodoc_data)} libraries matched, {matched_funcs} functions documented")
    if autodoc_unmatched:
        print(f"  {len(autodoc_unmatched)} unmatched autodoc entries")

    # ========================================================================
    # 5. Parse OS_CHANGES (if provided)
    # ========================================================================
    os_version_map = None
    if args.os_changes and os.path.isdir(args.os_changes):
        print(f"Parsing OS_CHANGES at {args.os_changes}...")
        os_version_map = build_version_map(args.os_changes)
        total_versioned = sum(len(v["functions"]) for v in os_version_map["libraries"].values())
        print(f"  {len(os_version_map['libraries'])} libraries, {total_versioned} versioned functions")

    # ========================================================================
    # 6. Build output
    # ========================================================================
    print("Building output...")

    output = {
        "_meta": {
            "source": "NDK 3.1 + OS_CHANGES",
            "ndk_path": ndk_root,
            "type_sizes": dict(sorted(type_sizes.items())),
            "calling_convention": {
                "scratch_regs": ["D0", "D1", "A0", "A1"],
                "preserved_regs": ["D2", "D3", "D4", "D5", "D6", "D7",
                                   "A2", "A3", "A4", "A5", "A6"],
                "base_reg": "A6",
                "return_reg": "D0",
                "note": (
                    "Parser-asserted: Amiga library calling convention from "
                    "ROM Kernel Reference Manual, Libraries 3rd Ed, Ch7. "
                    "D0-D1/A0-A1 are scratch (caller-saved). "
                    "D2-D7/A2-A5 are preserved (callee-saved). "
                    "A6 holds library base on entry, must be preserved. "
                    "A7(SP) is stack pointer."
                ),
            },
            "exec_base_addr": {
                "address": 4,
                "library": "exec.library",
                "note": (
                    "Parser-asserted: ExecBase pointer stored at absolute "
                    "address $4. ROM Kernel Reference Manual, Exec chapter. "
                    "All Amiga programs load ExecBase via MOVEA.L ($0004).W,A6. "
                    "The pointer is to the exec.library base structure."
                ),
            },
            "version_map": VERSION_MAP,
            "lvo_slot_size": LVO_SLOT_SIZE,
            "since_default_note": (
                "Functions without version markers default to since='1.0'. "
                "NDK 1.3 FD files lack pre-1.3 version granularity (1.0/1.1/1.2), "
                "so all pre-existing functions are tagged 1.0 as a lower bound."
            ),
        },
        "libraries": {},
        "structs": {},
        "constants": {},
    }

    # --- Build libraries ---
    for lib_name, fd_info in sorted(fd_data.items()):
        lib_entry = {
            "base": fd_info["base"],
            "functions": {},
            "lvo_index": {},
        }

        # Get OS_CHANGES version info for this library
        oc_lib = None
        if os_version_map:
            oc_lib = os_version_map["libraries"].get(lib_name)

        autodocs = autodoc_data.get(lib_name, {})

        for func_name, fd_func in fd_info["functions"].items():
            entry = {
                "lvo": fd_func["lvo"],
            }

            # Build inputs from FD args/regs
            if fd_func["args"]:
                entry["inputs"] = [
                    {"name": a, "reg": r}
                    for a, r in zip(fd_func["args"], fd_func["regs"])
                ]

            # Enrich from autodoc
            if func_name in autodocs:
                doc = autodocs[func_name]

                # Parse synopsis for typed inputs/outputs
                if "synopsis" in doc and fd_func["args"]:
                    parsed = parse_synopsis(
                        doc["synopsis"], fd_func["args"], fd_func["regs"]
                    )
                    if parsed["inputs"]:
                        entry["inputs"] = parsed["inputs"]
                    if parsed["output"]:
                        entry["output"] = parsed["output"]

                if "description" in doc:
                    entry["description"] = doc["description"]
                if "notes" in doc:
                    entry["notes"] = doc["notes"]
                if "bugs" in doc:
                    entry["bugs"] = doc["bugs"]
                if "warning" in doc:
                    entry["warning"] = doc["warning"]

                # No-return detection
                if check_no_return(doc):
                    entry["no_return"] = True

            # Detect functions that return a library/device/resource base.
            # Criteria (from autodoc-parsed output type + input signature):
            # - Output type contains "Library *" and output name suggests base
            # - OR output name is "resource" (OpenResource returns APTR)
            # - AND there's a name-string input (STRPTR or APTR with "name"
            #   in the parameter name)
            # Parser-asserted: ROM Kernel Reference Manual, Exec chapter.
            # OpenLibrary/OldOpenLibrary return library base in D0,
            # OpenResource returns resource base in D0. The name string
            # input tells us which library/resource is being opened.
            func_output = entry.get("output", {})
            out_type = func_output.get("type", "")
            out_name = func_output.get("name", "")
            out_reg = func_output.get("reg")
            if out_reg and (
                "Library *" in out_type
                or (out_name == "resource" and out_type in ("APTR", "void *"))
            ):
                # Find the name-string input register
                name_inputs = [
                    inp for inp in entry.get("inputs", [])
                    if "name" in inp.get("name", "").lower()
                    and inp.get("type") in ("STRPTR", "APTR", "char *",
                                            "UBYTE *", "void *")
                ]
                if name_inputs:
                    entry["returns_base"] = {
                        "name_reg": name_inputs[0]["reg"],
                        "base_reg": out_reg,
                    }

            # Version info
            since = fd_func.get("since")

            # OS_CHANGES overrides FD version markers
            if oc_lib and func_name in oc_lib["functions"]:
                since = oc_lib["functions"][func_name]

            # Normalize version numbers
            if since:
                since = VERSION_MAP.get(since, since)
            else:
                # Default: if not in OS_CHANGES, it existed from the start
                since = "1.0"

            entry["since"] = since

            # Private flag (only if true)
            if fd_func.get("private"):
                entry["private"] = True

            lib_entry["functions"][func_name] = entry
            lib_entry["lvo_index"][str(fd_func["lvo"])] = func_name

        output["libraries"][lib_name] = lib_entry

    # Add functions from OS_CHANGES that are in libraries we have but not in our FD
    if os_version_map:
        for oc_lib_name, oc_lib_info in os_version_map["libraries"].items():
            if oc_lib_name in output["libraries"]:
                lib = output["libraries"][oc_lib_name]
                for func_name, ver in oc_lib_info["functions"].items():
                    if func_name not in lib["functions"]:
                        lib["functions"][func_name] = {
                            "lvo": None,
                            "since": ver,
                        }

    # --- Build structs ---
    output["structs"] = raw_structs

    # --- Build constants ---
    output["constants"] = evaluated_constants

    # ========================================================================
    # 7. Summary
    # ========================================================================
    total_funcs = sum(len(v["functions"]) for v in output["libraries"].values())
    documented = sum(
        1 for lib in output["libraries"].values()
        for f in lib["functions"].values()
        if "description" in f
    )
    no_return_count = sum(
        1 for lib in output["libraries"].values()
        for f in lib["functions"].values()
        if f.get("no_return")
    )
    with_types = sum(
        1 for lib in output["libraries"].values()
        for f in lib["functions"].values()
        if any("type" in inp for inp in f.get("inputs", []))
    )
    structs_with_offsets = sum(
        1 for s in output["structs"].values()
        if s.get("fields") and any("offset" in field for field in s["fields"])
    )
    constants_resolved = sum(1 for v in output["constants"].values() if v["value"] is not None)

    print(f"\n{'=' * 60}")
    print(f"Libraries/devices/resources: {len(output['libraries'])}")
    print(f"Total functions:             {total_funcs}")
    print(f"  With documentation:        {documented}")
    print(f"  With typed inputs:         {with_types}")
    print(f"  No-return functions:       {no_return_count}")
    print(f"Structs:                     {len(output['structs'])}")
    print(f"  With computed offsets:      {structs_with_offsets}")
    print(f"Constants:                   {len(output['constants'])}")
    print(f"  Resolved to values:        {constants_resolved}")

    # ========================================================================
    # 8. Write output
    # ========================================================================
    outdir = os.path.dirname(args.outfile)
    if outdir and not os.path.isdir(outdir):
        os.makedirs(outdir, exist_ok=True)

    with open(args.outfile, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    fsize = os.path.getsize(args.outfile)
    print(f"\nWrote {args.outfile} ({fsize:,} bytes)")


if __name__ == "__main__":
    main()
