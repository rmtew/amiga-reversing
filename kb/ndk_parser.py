#!/usr/bin/env py.exe
"""Parse Amiga NDK 3.1 + OS_CHANGES into structured JSON knowledge base.

Parses:
- FD files: function names, register args, LVO offsets, private flags
- Autodocs: full function documentation (synopsis, description, inputs, results)
- Include files (.I): struct definitions with computed offsets, constants with evaluation
- TYPES.I: type size macros (parsed, not hardcoded)
- OS_CHANGES: version tagging (1.3 -> 2.04 -> 2.1 -> 3.0 -> 3.1 transitions)

Outputs:
- knowledge/amiga_os_reference.json
- knowledge/amiga_hw_symbols.json
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from typing import Any, cast

from kb.paths import (
    AMIGA_HW_REGISTERS_JSON,
    AMIGA_HW_SYMBOLS_JSON,
    AMIGA_OS_REFERENCE_JSON,
)
from kb.runtime_builder import build_runtime_artifacts

JsonDict = dict[str, Any]


# =============================================================================
# TYPES.I parser ? extract type sizes from macro definitions
# =============================================================================

def scan_type_macros(include_dir: str) -> dict[str, int]:
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
    direct_sizes: dict[str, int] = {}
    delegates: dict[str, str] = {}

    for dirpath, _dirnames, filenames in os.walk(include_dir):
        for fname in sorted(filenames):
            if not fname.upper().endswith(".I"):
                continue
            fpath = os.path.join(dirpath, fname)
            current_macro = None
            macro_body: list[str] = []

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


def resolve_include_i_dir(ndk_root: str) -> str:
    candidates = [
        os.path.join(ndk_root, "INCLUDES&LIBS", "INCLUDE_I"),
        os.path.join(ndk_root, "Include", "include_i"),
    ]
    existing = [path for path in candidates if os.path.isdir(path)]
    if not existing:
        raise ValueError(
            f"Could not find NDK include_i directory under {ndk_root!r}"
        )
    if len(existing) > 1:
        raise ValueError(
            f"Ambiguous NDK include_i directories under {ndk_root!r}: {existing}"
        )
    return existing[0]


_HEX_EQU_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s+EQU\s+\$([0-9A-Fa-f]+)\b")


def _parse_ver_line(line: str) -> str | None:
    match = re.search(r"\$VER:\s*([^\r\n*]+)", line)
    if not match:
        return None
    return match.group(1).strip()


def _load_hw_manual_base_address() -> int:
    with open(AMIGA_HW_REGISTERS_JSON, encoding="utf-8") as handle:
        canonical = json.load(handle)
    return int(canonical["base_address"], 16)


def _collect_equ_offsets(path: str,
                         *,
                         stop_before_comments: tuple[str, ...] = (),
                         ignored_prefixes: tuple[str, ...] = (),
                         ignored_ranges: tuple[tuple[str, str], ...] = (),
                         ) -> tuple[dict[int, list[str]], str | None]:
    offsets: dict[int, list[str]] = defaultdict(list)
    version = None
    active_ignored_end = None

    with open(path, encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip()
            if version is None:
                version = _parse_ver_line(line)
            stripped = line.strip()
            if active_ignored_end is not None:
                match = _HEX_EQU_RE.match(line)
                if match and match.group(1) == active_ignored_end:
                    active_ignored_end = None
                continue
            if stripped.startswith("*"):
                comment = stripped.lstrip("*").strip()
                if comment in stop_before_comments:
                    break
                for start_comment, end_name in ignored_ranges:
                    if comment == start_comment:
                        active_ignored_end = end_name
                        break
                continue
            match = _HEX_EQU_RE.match(line)
            if not match:
                continue
            name = match.group(1)
            if any(name.startswith(prefix) for prefix in ignored_prefixes):
                continue
            offsets[int(match.group(2), 16)].append(name)

    return dict(offsets), version


def build_hardware_symbols_kb(include_dir: str) -> JsonDict:
    hardware_dir = os.path.join(include_dir, "hardware")
    custom_path = os.path.join(hardware_dir, "custom.i")
    cia_path = os.path.join(hardware_dir, "cia.i")
    if not os.path.isfile(custom_path):
        raise ValueError(f"Missing NDK hardware include {custom_path}")
    if not os.path.isfile(cia_path):
        raise ValueError(f"Missing NDK hardware include {cia_path}")

    custom_offsets, custom_ver = _collect_equ_offsets(
        custom_path,
        ignored_ranges=(("AudChannel", "ac_SIZEOF"), ("SpriteDef", "sd_SIZEOF")),
    )
    cia_offsets, cia_ver = _collect_equ_offsets(
        cia_path,
        stop_before_comments=(
            "interrupt control register bit numbers",
            "Port definitions -- what each bit in a cia peripheral register is tied to",
        ),
    )

    ciaa_base = None
    ciab_base = None
    with open(cia_path, encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip()
            match_a = re.search(r"_ciaa.*--\s*\$(?P<hex>[0-9A-Fa-f]+)", line)
            if match_a:
                ciaa_base = int(match_a.group("hex"), 16)
            match_b = re.search(r"_ciab.*--\s*\$(?P<hex>[0-9A-Fa-f]+)", line)
            if match_b:
                ciab_base = int(match_b.group("hex"), 16)
    if ciaa_base is None or ciab_base is None:
        raise ValueError(f"Missing CIA base address comments in {cia_path}")

    custom_base = _load_hw_manual_base_address()
    entries = []
    for offset, names in sorted(custom_offsets.items()):
        sorted_names = sorted(set(names), key=lambda item: (-len(item), item))
        entries.append({
            "family": "custom",
            "cpu_address": f"0x{custom_base + offset:06X}",
            "offset": f"0x{offset:03X}",
            "include": "hardware/custom.i",
            "base_symbol": "_custom",
            "symbols": sorted_names,
        })
    for family, base_addr, base_symbol in (
        ("ciaa", ciaa_base, "_ciaa"),
        ("ciab", ciab_base, "_ciab"),
    ):
        for offset, names in sorted(cia_offsets.items()):
            sorted_names = sorted(set(names))
            entries.append({
                "family": family,
                "cpu_address": f"0x{base_addr + offset:06X}",
                "offset": f"0x{offset:04X}",
                "include": "hardware/cia.i",
                "base_symbol": base_symbol,
                "symbols": sorted_names,
            })
    return {
        "_meta": {
            "source": "NDK hardware includes",
            "include_dir": "hardware/",
            "files": {
                "custom": {
                    "path": "hardware/custom.i",
                    "version": custom_ver,
                },
                "cia": {
                    "path": "hardware/cia.i",
                    "version": cia_ver,
                },
            },
        },
        "registers": entries,
    }


# =============================================================================
# FD file parser
# =============================================================================

LVO_SLOT_SIZE = 6  # Each library vector slot is a JMP.L instruction (6 bytes).
# Parser-asserted: ROM Kernel Reference Manual, Libraries 3rd Ed, Ch28
# "Library Vectors". Each vector entry is JMP absolute.long = 2 opword + 4 addr.


def parse_fd_file(path: str) -> JsonDict:
    """Parse a .FD file to extract function definitions with LVO offsets."""
    functions: dict[str, JsonDict] = {}
    base_name = ""
    bias = 0
    public = True
    block_fd_version = None
    block_os_since = None

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()
            if not line:
                continue

            # Track version markers in comments
            if line.startswith("*"):
                release_marker = re.search(r'[Rr]elease\s+(\d[\d.]*)', line)
                if release_marker:
                    block_os_since = release_marker.group(1)
                fd_version_marker = re.search(
                    r'functions?\s+in\s+[Vv](\d[\d.]*)\s+or\s+higher',
                    line
                )
                if fd_version_marker:
                    block_fd_version = fd_version_marker.group(1)
                os_since_marker = re.search(
                    r'(?:[Nn]ew|[Aa]dded)\s+(?:functions?\s+)?(?:for|as of)\s+'
                    r'[Rr]elease\s+(\d[\d.]*)',
                    line
                )
                if os_since_marker:
                    block_os_since = os_since_marker.group(1)
                short_os_since_marker = re.match(r'\*[-\s]*(\d\.\d)\s+[Nn]ew\b', line)
                if short_os_since_marker:
                    block_os_since = short_os_since_marker.group(1)
                explicit_fd_version = re.search(
                    r'(?:[Nn]ew|[Aa]dded)\s+(?:functions?\s+)?(?:for|as of)\s+'
                    r'(?:[Vv]ersion\s+|[Vv])(\d[\d.]*)',
                    line
                )
                if explicit_fd_version:
                    block_fd_version = explicit_fd_version.group(1)
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
                if block_fd_version:
                    entry["fd_version"] = block_fd_version
                if block_os_since:
                    entry["os_since"] = block_os_since
                functions[name] = entry
                bias += LVO_SLOT_SIZE

    return {"base": base_name, "functions": functions}


# =============================================================================
# Autodoc parser
# =============================================================================

def parse_autodoc(path: str) -> dict[str, JsonDict]:
    """Parse an autodoc file to extract function documentation.

    Format: entries separated by form feed (0x0C), each starting with
    library.type/FuncName header.
    """
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    entries: dict[str, JsonDict] = {}
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
        doc: JsonDict = {}

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
# Synopsis parser ? structured inputs/outputs from autodoc synopsis
# =============================================================================

def parse_synopsis(synopsis: str, arg_names: list[str], arg_regs: list[str]) -> JsonDict:
    """Parse autodoc SYNOPSIS text into structured input/output data."""
    result: JsonDict = {"inputs": [], "output": None}
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
    c_type_decls: list[tuple[str, str]] = []
    for line in lines:
        line_s = line.strip()
        proto_m = re.match(r'(.+?)\s+\*?\s*\w+\s*\((.+)\)\s*;?$', line_s)
        if proto_m:
            c_proto = line_s
            continue
        decl_m = re.match(
            r'(?P<type>(?:struct\s+\w+|unsigned\s+\w+|\w+))(?:\s*(?P<ptr>\*))?\s+(?P<name>\w+)\s*;$',
            line_s,
        )
        if decl_m:
            typ = decl_m.group("type").strip()
            if decl_m.group("ptr"):
                typ += " *"
            c_type_decls.append((decl_m.group("name"), typ))

    type_map = dict(c_type_decls)

    # Extract arg types from C prototype
    arg_types_from_proto: list[str] = []
    if c_proto:
        proto_m = re.match(r'(.+?)\b(\w+)\s*\((.+)\)\s*;?$', c_proto)
        if proto_m:
            ret_type_str = proto_m.group(1).strip()
            if ret_type_str.endswith('*'):
                ret_type_str = ret_type_str.rstrip('*').strip() + " *"
            arg_str = proto_m.group(3)
            arg_types_from_proto = [a.strip() for a in arg_str.split(',')]
            if ret_name and ret_type_str:
                output: JsonDict = {
                    "name": ret_name,
                    "reg": ret_reg,
                    "type": ret_type_str,
                }
                result["output"] = output
        elif ret_name:
            result["output"] = {"name": ret_name, "reg": ret_reg}
    elif ret_name:
        ret_type = type_map.get(ret_name)
        output = {"name": ret_name, "reg": ret_reg}
        if ret_type:
            output["type"] = ret_type
        result["output"] = output

    # Build structured inputs
    inputs = cast(list[JsonDict], result["inputs"])
    for i, (aname, areg) in enumerate(zip(arg_names, arg_regs, strict=True)):
        inp: JsonDict = {"name": aname, "reg": areg.upper()}
        if i < len(arg_types_from_proto):
            inp["type"] = arg_types_from_proto[i]
        elif aname in type_map:
            inp["type"] = type_map[aname]
        inputs.append(inp)

    return result


def _normalized_type_string(type_str: str | None) -> str | None:
    if type_str is None:
        return None
    normalized = " ".join(type_str.strip().split())
    return normalized or None


def _infer_input_semantic_kind(type_str: str | None) -> str | None:
    normalized = _normalized_type_string(type_str)
    if normalized is None:
        return None
    compact = normalized.replace(" ", "")
    if "(*)" in compact:
        return "code_ptr"
    if normalized == "struct Hook *":
        return "hook_ptr"
    if normalized == "STRPTR":
        return "string_ptr"
    return None


def _split_c_args(arg_str: str) -> list[str]:
    args: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in arg_str:
        if ch == "," and depth == 0:
            part = "".join(current).strip()
            if part:
                args.append(part)
            current = []
            continue
        current.append(ch)
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise ValueError(f"Unbalanced C argument list {arg_str!r}")
    part = "".join(current).strip()
    if part:
        args.append(part)
    return args


def _iter_c_header_statements(path: str) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    statements: list[str] = []
    current: list[str] = []
    in_preprocessor_continuation = False
    for raw_line in text.splitlines():
        stripped_raw = raw_line.rstrip()
        line = stripped_raw.strip()
        if in_preprocessor_continuation:
            if not stripped_raw.endswith("\\"):
                in_preprocessor_continuation = False
            continue
        if not line:
            continue
        if line.startswith("#"):
            in_preprocessor_continuation = stripped_raw.endswith("\\")
            continue
        current.append(line)
        if line.endswith(";"):
            statements.append(" ".join(current).rstrip(";").strip())
            current = []
    if current:
        raise ValueError(f"Unterminated declaration in {path}")
    return statements


def parse_callback_typedefs(include_h_dir: str) -> dict[str, str]:
    callback_types: dict[str, str] = {}
    aliases: dict[str, str] = {}
    for dirpath, _dirnames, filenames in os.walk(include_h_dir):
        for fname in sorted(filenames):
            if not fname.lower().endswith(".h"):
                continue
            path = os.path.join(dirpath, fname)
            for statement in _iter_c_header_statements(path):
                if not statement.startswith("typedef "):
                    continue
                direct = re.match(
                    r"^typedef\s+(?P<rtype>.+?)\(\s*\*\s*(?P<name>\w+)\s*\)\s*\((?P<inner>.*)\)$",
                    statement,
                )
                if direct is not None:
                    callback_types[direct.group("name")] = (
                        f"{direct.group('rtype').strip()} (*)({direct.group('inner').strip()})"
                    )
                    continue
                alias = re.match(r"^typedef\s+(?P<target>\w+)\s+(?P<name>\w+)$", statement)
                if alias is not None:
                    aliases[alias.group("name")] = alias.group("target")
    unresolved = dict(aliases)
    for _ in range(len(unresolved) + 1):
        if not unresolved:
            break
        changed = False
        for name, target in list(unresolved.items()):
            resolved = callback_types.get(target)
            if resolved is None:
                continue
            callback_types[name] = resolved
            unresolved.pop(name)
            changed = True
        if not changed:
            break
    return callback_types


def _parse_c_prototype_arg(arg: str, callback_typedefs: dict[str, str]) -> dict[str, str] | None:
    normalized = " ".join(arg.strip().split())
    if not normalized or normalized == "void" or normalized == "...":
        return None
    fn_ptr = re.match(r"^(?P<rtype>.+?)\(\s*\*\s*(?P<name>\w+)\s*\)\s*\((?P<inner>.*)\)$", normalized)
    if fn_ptr:
        return {
            "name": fn_ptr.group("name"),
            "type": f"{fn_ptr.group('rtype').strip()} (*)({fn_ptr.group('inner').strip()})",
        }
    plain = re.match(r"^(?P<type>.+?)\b(?P<name>\w+)$", normalized)
    if plain is None:
        if re.match(r"^(struct\s+\w+|[A-Za-z_]\w*)(\s*\*)+$", normalized):
            return None
        raise ValueError(f"Unsupported C prototype argument {arg!r}")
    plain_type = plain.group("type").strip()
    plain_type = callback_typedefs.get(plain_type, plain_type)
    return {
        "name": plain.group("name"),
        "type": plain_type,
    }


def parse_clib_prototypes(include_h_dir: str) -> dict[str, dict[str, list[dict[str, str]]]]:
    clib_dir = os.path.join(include_h_dir, "clib")
    if not os.path.isdir(clib_dir):
        raise ValueError(f"Missing clib include directory {clib_dir}")
    callback_typedefs = parse_callback_typedefs(include_h_dir)
    parsed: dict[str, dict[str, list[dict[str, str]]]] = {}
    for fname in sorted(os.listdir(clib_dir)):
        if not fname.lower().endswith("_protos.h"):
            continue
        stem = fname[:-len("_protos.h")].lower()
        path = os.path.join(clib_dir, fname)
        functions: dict[str, list[dict[str, str]]] = {}
        for statement in _iter_c_header_statements(path):
            if statement.startswith("typedef "):
                continue
            proto = re.match(r"^(?P<ret>.+?)\b(?P<name>\w+)\s*\((?P<args>.*)\)$", statement)
            if proto is None:
                continue
            args = []
            for arg in _split_c_args(proto.group("args")):
                parsed_arg = _parse_c_prototype_arg(arg, callback_typedefs)
                if parsed_arg is not None:
                    args.append(parsed_arg)
            functions[proto.group("name")] = args
        parsed[stem] = functions
    return parsed


def _resolve_clib_library_name(stem: str, library_names: set[str]) -> str | None:
    candidates = [
        name for name in library_names
        if name in {f"{stem}.library", f"{stem}.device", f"{stem}.resource"}
    ]
    if not candidates:
        return None
    if len(candidates) != 1:
        raise ValueError(f"Ambiguous clib stem {stem!r}: {candidates}")
    return candidates[0]


def reconcile_clib_callback_types(output: JsonDict, include_h_dir: str) -> int:
    clib = parse_clib_prototypes(include_h_dir)
    library_names = set(output["libraries"])
    updates = 0
    for stem, functions in clib.items():
        lib_name = _resolve_clib_library_name(stem, library_names)
        if lib_name is None:
            continue
        library = output["libraries"][lib_name]
        for func_name, args in functions.items():
            if func_name not in library["functions"]:
                continue
            inputs = library["functions"][func_name].get("inputs", [])
            if not inputs or not args:
                continue
            by_name = {arg["name"]: arg for arg in args}
            for inp in inputs:
                parsed_arg = by_name.get(inp["name"])
                if parsed_arg is None:
                    continue
                parsed_type = _normalized_type_string(parsed_arg["type"])
                current_type = _normalized_type_string(inp.get("type"))
                if parsed_type is not None and parsed_type != current_type:
                    inp["type"] = parsed_type
                    updates += 1
                semantic_kind = _infer_input_semantic_kind(inp.get("type"))
                if semantic_kind is not None:
                    if inp.get("semantic_kind") != semantic_kind:
                        inp["semantic_kind"] = semantic_kind
                        updates += 1
                    if "semantic_note" in inp:
                        inp.pop("semantic_note", None)
                        updates += 1
    return updates


_INPUT_SEMANTIC_ASSERTIONS: dict[tuple[str, str, str], dict[str, str]] = {
    ("exec.library", "AddTask", "initPC"): {
        "semantic_kind": "code_ptr",
        "semantic_note": (
            "Parser-authored: exec.library/AddTask uses initPC as the new task "
            "entry point. NDK synopsis types it as APTR, so direct parse cannot "
            "distinguish code from generic pointer data."
        ),
    },
    ("exec.library", "AddTask", "finalPC"): {
        "semantic_kind": "code_ptr",
        "semantic_note": (
            "Parser-authored: exec.library/AddTask uses finalPC as the task exit "
            "handler entry point. NDK synopsis types it as APTR, so direct parse "
            "cannot preserve callback semantics."
        ),
    },
    ("exec.library", "ObtainQuickVector", "interruptCode"): {
        "semantic_kind": "code_ptr",
        "semantic_note": (
            "Parser-authored: exec.library/ObtainQuickVector autodoc says the "
            "function installs the code pointer into a quick interrupt vector. "
            "NDK synopsis types it as APTR, so direct parse loses callback semantics."
        ),
    },
    ("lowlevel.library", "AddKBInt", "intRoutine"): {
        "semantic_kind": "code_ptr",
        "semantic_note": (
            "Parser-authored: lowlevel.library/AddKBInt autodoc says intRoutine is "
            "called from the keyboard interrupt context. NDK synopsis types it as APTR, "
            "so direct parse cannot preserve callback semantics."
        ),
    },
    ("lowlevel.library", "AddTimerInt", "intRoutine"): {
        "semantic_kind": "code_ptr",
        "semantic_note": (
            "Parser-authored: lowlevel.library/AddTimerInt autodoc says intRoutine is "
            "called from timer interrupt context. NDK synopsis types it as APTR, "
            "so direct parse cannot preserve callback semantics."
        ),
    },
    ("lowlevel.library", "AddVBlankInt", "intRoutine"): {
        "semantic_kind": "code_ptr",
        "semantic_note": (
            "Parser-authored: lowlevel.library/AddVBlankInt autodoc says intRoutine is "
            "called from vertical blank interrupt context. NDK synopsis types it as APTR, "
            "so direct parse cannot preserve callback semantics."
        ),
    },
}


def _apply_input_semantics(lib_name: str, func_name: str, entry: JsonDict) -> None:
    for inp in entry.get("inputs", []):
        semantic_kind = _infer_input_semantic_kind(inp.get("type"))
        if semantic_kind is not None:
            inp["semantic_kind"] = semantic_kind
        assertion = _INPUT_SEMANTIC_ASSERTIONS.get((lib_name, func_name, inp["name"]))
        if assertion is not None:
            inp["semantic_kind"] = assertion["semantic_kind"]
            inp["semantic_note"] = assertion["semantic_note"]


# =============================================================================
# No-return detection
# =============================================================================

def _resolve_struct_ref(type_str: str, c_to_i: dict[str, str],
                        i_names: set[str]) -> str | None:
    """Extract .I struct name from a C type string like 'struct Foo *'.

    Tries the c_to_i mapping first, then direct/case-insensitive match
    against known .I struct names.
    """
    if "struct " not in type_str:
        return None
    # Extract C struct name: "struct Foo *" -> "Foo"
    c_name = type_str.replace("*", "").strip()
    if c_name.startswith("struct "):
        c_name = c_name[7:].strip()
    c_name = c_name.split()[0] if " " in c_name else c_name
    if not c_name:
        return None
    # Try c_to_i mapping
    if c_name in c_to_i:
        return c_to_i[c_name]
    # Try direct match
    if c_name in i_names:
        return c_name
    # Try case-insensitive
    upper_map = {k.upper(): k for k in i_names}
    if c_name.upper() in upper_map:
        return upper_map[c_name.upper()]
    return None


def parse_structure_offsets(path: str) -> dict[str, dict[str, object]]:
    c_structs: dict[str, dict[str, object]] = {}
    current_c: str | None = None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            if line[0] != " " and line.endswith(":"):
                current_c = line[:-1]
                c_structs[current_c] = {"size": None, "fields": []}
                continue
            if current_c is None or not line.startswith("  "):
                continue
            parts = line.split()
            if "sizeof" in line:
                c_structs[current_c]["size"] = int(parts[1])
                continue
            if len(parts) < 4:
                continue
            field_name = parts[3]
            if "." in field_name:
                continue
            cast(list[JsonDict], c_structs[current_c]["fields"]).append({
                "offset": int(parts[1]),
                "size": int(parts[2]),
                "name": field_name,
            })
    return c_structs


def _parse_c_struct_declaration(decl: str) -> list[tuple[str, str]]:
    decl = " ".join(decl.strip().rstrip(";").split())
    if not decl or "(" in decl or ")" in decl or ":" in decl:
        return []
    m = re.match(
        r'^(?P<base>(?:const\s+)?(?:struct\s+\w+|unsigned\s+\w+|\w+))\s+(?P<decls>.+)$',
        decl,
    )
    if m is None:
        return []
    base_type = m.group("base")
    tail = m.group("decls")
    result = []
    for raw_decl in tail.split(","):
        raw_decl = raw_decl.strip()
        decl_m = re.match(r'^(?P<stars>\*+)?\s*(?P<name>\w+)(?:\[[^\]]*\])?$', raw_decl)
        if decl_m is None:
            return []
        stars = decl_m.group("stars") or ""
        name = decl_m.group("name")
        raw_type = base_type + (" " + stars if stars else "")
        result.append((name, raw_type))
    return result


def parse_c_struct_field_types(include_h_dir: str) -> dict[str, dict[str, str]]:
    c_structs: dict[str, dict[str, str]] = {}
    for dirpath, _dirnames, filenames in os.walk(include_h_dir):
        for fname in sorted(filenames):
            if not fname.upper().endswith(".H"):
                continue
            fpath = os.path.join(dirpath, fname)
            with open(fpath, encoding="utf-8", errors="replace") as f:
                text = f.read()
            text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
            current_struct: str | None = None
            brace_depth = 0
            decl_parts: list[str] = []
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if current_struct is None:
                    m = re.match(r"struct\s+(\w+)\s*\{", line)
                    if m:
                        current_struct = m.group(1)
                        if current_struct in c_structs:
                            raise ValueError(f"Duplicate C struct definition {current_struct}")
                        c_structs[current_struct] = {}
                        brace_depth = line.count("{") - line.count("}")
                    continue
                if brace_depth == 1 and "{" not in line and "}" not in line:
                    decl_parts.append(line)
                    if line.endswith(";"):
                        for field_name, field_type in _parse_c_struct_declaration(
                                " ".join(decl_parts)):
                            existing = c_structs[current_struct].get(field_name)
                            if existing is not None and existing != field_type:
                                raise ValueError(
                                    f"Conflicting C field type for {current_struct}.{field_name}: "
                                    f"{existing} vs {field_type}")
                            c_structs[current_struct][field_name] = field_type
                        decl_parts = []
                else:
                    decl_parts = []
                brace_depth += line.count("{") - line.count("}")
                if brace_depth == 0:
                    current_struct = None
                    decl_parts = []
    return c_structs


def _extract_named_base_struct(comment_lines: list[str],
                               struct_name: str) -> tuple[str, str] | None:
    if not comment_lines:
        return None
    comment_text = " ".join(comment_lines)
    explicit = re.search(
        r'\(\s*STRUCT\s+(\w+)\s*\*\s*\)\s*Open(Library|Device|Resource)\(\s*"([^"]+)"',
        comment_text,
        re.IGNORECASE,
    )
    if explicit is not None:
        mapped_struct = explicit.group(1)
        if mapped_struct != struct_name:
            raise ValueError(
                f"Comment-based base struct mismatch: comment says {mapped_struct}, "
                f"structure is {struct_name}")
        return explicit.group(3), struct_name
    implicit = re.search(
        r'Open(Library|Device|Resource)\(\s*"([^"]+)"[^)]*\)\s+returns\s+a\s+pointer\s+to\s+this\s+structure',
        comment_text,
        re.IGNORECASE,
    )
    if implicit is not None:
        return implicit.group(2), struct_name
    return None


def annotate_c_struct_field_types(structs: dict[str, JsonDict],
                                  c_structs_so: dict[str, dict[str, object]],
                                  c_field_types: dict[str, dict[str, str]],
                                  c_to_i: dict[str, str]) -> None:
    i_names = set(structs)
    candidates_by_i: dict[str, list[dict[str, object]]] = {}
    for c_name, struct_info in c_structs_so.items():
        i_name = c_to_i.get(c_name)
        if i_name is None or c_name not in c_field_types:
            continue
        candidates_by_i.setdefault(i_name, []).append(struct_info | {"c_name": c_name})

    for i_name, struct_def in structs.items():
        candidates = [
            candidate
            for candidate in candidates_by_i.get(i_name, ())
            if candidate["size"] == struct_def["size"]
        ]
        for field in cast(list[JsonDict], struct_def["fields"]):
            if field["type"] == "LABEL":
                continue
            matches: list[tuple[str, JsonDict]] = []
            for candidate in candidates:
                for c_field in cast(list[JsonDict], candidate["fields"]):
                    if c_field["offset"] == field["offset"]:
                        matches.append((cast(str, candidate["c_name"]), c_field))
            if not matches:
                continue
            c_name, c_field = matches[0]
            for other_c_name, other_field in matches[1:]:
                if other_field != c_field:
                    raise ValueError(
                        f"Conflicting C field mapping for {i_name}.{field['name']} at "
                        f"offset {field['offset']}: {c_name}.{c_field['name']} vs "
                        f"{other_c_name}.{other_field['name']}")
            c_type = c_field_types[c_name].get(c_field["name"])
            if c_type is None:
                continue
            field["c_type"] = c_type
            i_ref = _resolve_struct_ref(c_type, c_to_i, i_names)
            if i_ref is None:
                continue
            if "*" in c_type:
                field["pointer_struct"] = i_ref
                continue
            if field["type"] != "STRUCT":
                raise ValueError(
                    f"C struct field {c_name}.{c_field['name']} is inline struct {c_type} "
                    f"but asm field {i_name}.{field['name']} is {field['type']}")
            existing_struct = field.get("struct")
            if existing_struct is not None and existing_struct != i_ref:
                raise ValueError(
                    f"Conflicting embedded struct for {i_name}.{field['name']}: "
                    f"{existing_struct} vs {i_ref}")
            field["struct"] = i_ref


def check_no_return(doc: JsonDict) -> bool:
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
            r'\b(?:this\s+(?:function|routine|call))\s+never\s+returns\b\s*[.\n]',
            re.IGNORECASE,
        ),
        # "This function does not return." (sentence-final)
        re.compile(
            r'\b(?:this\s+(?:function|routine|call))\s+does\s+not\s+return\b\s*[.\n]',
            re.IGNORECASE,
        ),
        # Standalone "never returns." at end of sentence (common brief form)
        re.compile(r'^\s*\w+\(\)\s+never\s+returns\b\s*\.', re.IGNORECASE | re.MULTILINE),
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
# Include file parser (structs and constants) ? with offset computation
# =============================================================================

def parse_asm_include(path: str, type_sizes: dict[str, int], all_constants: dict[str, object]) -> JsonDict:
    """Parse .I (asm) include file for struct definitions and constants.

    Computes byte offsets for struct fields using type_sizes from scan_type_macros.
    """
    structs: dict[str, JsonDict] = {}
    constants: dict[str, object] = {}
    named_base_structs: dict[str, str] = {}
    current_struct = None
    current_fields: list[JsonDict] = []
    current_offset = 0
    current_base_offset = 0
    current_base_offset_symbol = None
    comment_lines: list[str] = []

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
        type_field_re = re.compile(r'(-!)')  # never matches

    # Track the source subpath (e.g. "exec/NODES.I")
    rel_parts = path.replace("\\", "/").split("/")
    # Find INCLUDE_I in path
    try:
        idx = [p.upper() for p in rel_parts].index("INCLUDE_I")
        source = "/".join(rel_parts[idx + 1:])
    except ValueError:
        source = os.path.basename(path)

    def finish_struct() -> None:
        nonlocal current_struct, current_fields, current_offset
        nonlocal current_base_offset, current_base_offset_symbol
        if current_struct and current_fields:
            structs[current_struct] = {
                "source": source,
                "base_offset": current_base_offset,
                "base_offset_symbol": current_base_offset_symbol,
                "size": current_offset,
                "fields": current_fields,
            }
        current_struct = None
        current_fields = []
        current_offset = 0
        current_base_offset = 0
        current_base_offset_symbol = None

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()
            stripped = line.strip()

            if stripped.startswith((";", "*")):
                comment_lines.append(stripped.lstrip(";*").strip())
                continue
            if not stripped:
                continue

            # STRUCTURE definition start: STRUCTURE Name,InitialOffset
            m = re.match(r'\s+STRUCTURE\s+(\w+),(\w+)', line)
            if m:
                finish_struct()
                current_struct = m.group(1)
                named_base_struct = _extract_named_base_struct(comment_lines, current_struct)
                if named_base_struct is not None:
                    base_name, mapped_struct = named_base_struct
                    existing = named_base_structs.get(base_name)
                    if existing is not None and existing != mapped_struct:
                        raise ValueError(
                            f"Conflicting named base struct for {base_name}: "
                            f"{existing} vs {mapped_struct}")
                    named_base_structs[base_name] = mapped_struct
                comment_lines = []
                init_offset_str = m.group(2)
                # Initial offset can be a constant name (e.g. LIB_SIZE)
                # or a number
                try:
                    current_offset = int(init_offset_str)
                except ValueError:
                    resolved = resolve_constant_value(init_offset_str, all_constants)
                    if resolved is not None:
                        current_offset = resolved
                        current_base_offset_symbol = init_offset_str
                    else:
                        print(f"  WARNING: struct {current_struct} initial offset "
                              f"'{init_offset_str}' unresolved, skipping struct",
                              file=sys.stderr)
                        current_struct = None
                        continue
                else:
                    current_base_offset_symbol = None
                current_base_offset = current_offset
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
                    comment_lines = []
                    continue

                # STRUCT name,size ? embedded sub-structure
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
                        "size_symbol": None if size_str.isdigit() else size_str,
                    })
                    current_offset += fsize
                    comment_lines = []
                    continue

                # LABEL name ? zero-size marker
                lm = re.match(r'\s+LABEL\s+(\w+)', line)
                if lm:
                    fname = lm.group(1)
                    current_fields.append({
                        "name": fname,
                        "type": "LABEL",
                        "offset": current_offset,
                        "size": 0,
                    })
                    comment_lines = []
                    continue

                # ALIGNWORD
                if re.match(r'\s+ALIGNWORD\b', line):
                    current_offset = (current_offset + 1) & ~1
                    comment_lines = []
                    continue

                # ALIGNLONG
                if re.match(r'\s+ALIGNLONG\b', line):
                    current_offset = (current_offset + 3) & ~3
                    comment_lines = []
                    continue

                # DS.B / DS.W / DS.L ? data storage (rare in structs but possible)
                dm = re.match(r'\s+DS\.\w\s+', line)
                if dm:
                    continue

                # End of struct detection: non-empty, non-comment line that's
                # not a recognized struct directive -> end the struct
                stripped = line.strip()
                if (
                    stripped
                    and not stripped.startswith("*")
                    and not stripped.startswith(";")
                    and not re.match(r"\s+(DS|CNOP)", line)
                ):
                    finish_struct()

            # EQU constants
            cm = re.match(r'^(\w+)\s+[Ee][Qq][Uu]\s+(.+?)(?:\s*[;*].*)?$', line)
            if cm:
                name = cm.group(1)
                value = cm.group(2).strip()
                constants[name] = value
                comment_lines = []
                continue

            # SET constants (skip include guards ending in _I)
            cm = re.match(r'^(\w+)\s+SET\s+(.+?)(?:\s*[;*].*)?$', line)
            if cm:
                name = cm.group(1)
                value = cm.group(2).strip()
                if not name.endswith("_I") and name != "SOFFSET" and name != "EOFFSET":
                    constants[name] = value
                comment_lines = []

    finish_struct()
    return {
        "structs": structs,
        "constants": constants,
        "named_base_structs": named_base_structs,
    }


def _build_size_symbol_to_slice(structs: dict[str, JsonDict]) -> dict[str, JsonDict]:
    symbol_to_slice: dict[str, dict[str, object]] = {}
    for struct_name, struct_def in structs.items():
        for field in cast(list[JsonDict], struct_def["fields"]):
            if field["type"] != "LABEL":
                continue
            entry = {"struct": struct_name, "size": field["offset"]}
            existing = symbol_to_slice.get(field["name"])
            if existing is not None and existing != entry:
                raise ValueError(
                    f"Conflicting struct slice label {field['name']}: "
                    f"{existing} vs {entry}")
            symbol_to_slice[field["name"]] = entry
    return symbol_to_slice


def annotate_embedded_structs(structs: dict[str, JsonDict]) -> None:
    """Resolve embedded struct references and struct-prefix slices."""
    symbol_to_slice = _build_size_symbol_to_slice(structs)

    for _struct_name, struct_def in structs.items():
        base_offset_symbol = struct_def.get("base_offset_symbol")
        if base_offset_symbol:
            base_slice = symbol_to_slice.get(base_offset_symbol)
            if base_slice is not None:
                if base_slice["size"] != struct_def["base_offset"]:
                    raise ValueError(
                        f"Struct base offset mismatch for {base_offset_symbol}: "
                        f"expected {base_slice['size']}, got {struct_def['base_offset']}")
                struct_def["base_struct"] = base_slice["struct"]

        for field in cast(list[JsonDict], struct_def["fields"]):
            if field["type"] != "STRUCT":
                continue
            size_symbol = field.get("size_symbol")
            if not size_symbol:
                continue
            embedded_slice = symbol_to_slice.get(size_symbol)
            if embedded_slice is None:
                continue
            if embedded_slice["size"] != field["size"]:
                raise ValueError(
                    f"Embedded struct size mismatch for {size_symbol}: "
                    f"expected {embedded_slice['size']}, got {field['size']}")
            field["struct"] = embedded_slice["struct"]


def derive_named_base_structs(fd_data: dict[str, JsonDict],
                              structs: dict[str, JsonDict],
                              explicit_mappings: dict[str, str]) -> dict[str, str]:
    result = dict(explicit_mappings)
    for lib_name, fd_info in fd_data.items():
        base_name = fd_info["base"]
        if base_name not in structs:
            continue
        existing = result.get(lib_name)
        if existing is not None and existing != base_name:
            raise ValueError(
                f"Conflicting named base struct for {lib_name}: "
                f"{existing} vs {base_name}")
        result[lib_name] = base_name
    return dict(sorted(result.items()))


# =============================================================================
# Constant evaluation
# =============================================================================

def resolve_constant_value(expr: str, all_constants: dict[str, object], depth: int = 0) -> int | None:
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
                if op_str == '&':
                    return lval & rval
                if op_str == '<<':
                    return (lval << rval) & 0xFFFFFFFF
                if op_str == '>>':
                    return lval >> rval
                if op_str == '+':
                    return lval + rval
                if op_str == '-':
                    return lval - rval
                if op_str == '*':
                    return lval * rval
            return None

    # Single identifier ? look up in constants
    m = re.match(r'^[A-Za-z_]\w*$', expr)
    if m:
        if expr in all_constants:
            raw = all_constants[expr]
            if isinstance(raw, dict):
                return raw.get("value")
            return resolve_constant_value(str(raw), all_constants, depth + 1)
        return None

    return None


def find_operator(expr: str, ops: tuple[str, ...]) -> tuple[str, int, int] | None:
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


def evaluate_all_constants(raw_constants: dict[str, object]) -> dict[str, JsonDict]:
    """Resolve all constants to integer values where possible.

    Returns dict of {name: {"raw": expr_str, "value": int_or_null}}.
    """
    result: dict[str, JsonDict] = {}
    for name, raw_expr in raw_constants.items():
        result[name] = {"raw": str(raw_expr), "value": None}

    # Multiple passes to resolve dependencies
    for _ in range(10):
        changed = False
        for _name, entry in result.items():
            if entry["value"] is not None:
                continue
            val = resolve_constant_value(cast(str, entry["raw"]), cast(dict[str, object], result))
            if val is not None:
                entry["value"] = val
                changed = True
        if not changed:
            break

    return result


# =============================================================================
# OS_CHANGES parser (integrated)
# =============================================================================

def parse_change_file(path: str) -> JsonDict:
    """Parse a single OS_CHANGES file."""
    result: JsonDict = {"added": {}, "new": {}, "removed": {}}

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
                lib_match = re.match(r'(\S+)', stripped)
                if lib_match is None:
                    continue
                lib_name = lib_match.group(1)
                current_lib = lib_name
                target_map = cast(dict[str, list[str]], target)
                if current_lib not in target_map:
                    target_map[current_lib] = []
                continue

            if tabs >= 2 and stripped.endswith('()') and current_lib:
                func_name = stripped.rstrip('()')
                cast(dict[str, list[str]], target)[current_lib].append(func_name)

    return result


def build_version_map(os_changes_dir: str) -> JsonDict:
    """Build function->version mapping from all change files."""
    change_files = [
        ("1.3_TO_2.04", "2.04"),
        ("2.04_TO_2.1", "2.1"),
        ("2.1_TO_3.0", "3.0"),
        ("3.0_TO_3.1", "3.1"),
    ]

    libraries: dict[str, JsonDict] = {}
    removed: dict[str, JsonDict] = {}

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

def match_autodoc_to_lib(doc_filename: str, lib_names: set[str]) -> str | None:
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

    # Try without suffix ? some docs match library names directly
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse Amiga NDK 3.1 + OS_CHANGES into structured JSON"
    )
    parser.add_argument("ndk_root", help="Path to NDK root directory")
    parser.add_argument("--os-changes", help="Path to OS_CHANGES directory")
    parser.add_argument("--outfile", default=str(AMIGA_OS_REFERENCE_JSON))
    parser.add_argument("--hardware-outfile", default=str(AMIGA_HW_SYMBOLS_JSON))
    parser.add_argument("--hardware-only", action="store_true")
    args = parser.parse_args()

    ndk_root = args.ndk_root
    include_dir = resolve_include_i_dir(ndk_root)

    hardware_outdir = os.path.dirname(args.hardware_outfile)
    if hardware_outdir and not os.path.isdir(hardware_outdir):
        os.makedirs(hardware_outdir, exist_ok=True)
    hardware_output = build_hardware_symbols_kb(include_dir)
    with open(args.hardware_outfile, "w", encoding="utf-8") as handle:
        json.dump(hardware_output, handle, indent=2, ensure_ascii=False)
    print(f"Wrote {args.hardware_outfile} ({os.path.getsize(args.hardware_outfile):,} bytes)")

    if args.hardware_only:
        for runtime_out in build_runtime_artifacts():
            print(f"Wrote {runtime_out}")
        return

    fd_dir = os.path.join(ndk_root, "INCLUDES&LIBS", "FD")
    autodoc_dir = os.path.join(ndk_root, "DOCS", "DOC")

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
    raw_constants: dict[str, object] = {}
    raw_structs: dict[str, JsonDict] = {}
    raw_named_base_structs: dict[str, str] = {}

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
                soffset: int | None = 0  # simulates SOFFSET for struct field constants
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
                        enm = re.match(r'\s+ENUM(?:\s+(\S+))?\s*$', line)
                        if enm:
                            base_str = enm.group(1)
                            if base_str:
                                try:
                                    eoffset = int(base_str)
                                except ValueError:
                                    hm = re.match(r'^\$([0-9a-fA-F]+)$', base_str)
                                    eoffset = int(hm.group(1), 16) if hm else 0
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
                                        soffset = int(cast(str, raw_constants[init_str]))
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
                                            soffset += int(cast(str, raw_constants[size_str]))
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
                for base_name, struct_name in result["named_base_structs"].items():
                    existing = raw_named_base_structs.get(base_name)
                    if existing is not None and existing != struct_name:
                        raise ValueError(
                            f"Conflicting named base struct for {base_name}: "
                            f"{existing} vs {struct_name}")
                    raw_named_base_structs[base_name] = struct_name

    annotate_embedded_structs(raw_structs)

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
    named_base_structs = derive_named_base_structs(
        fd_data,
        raw_structs,
        raw_named_base_structs,
    )

    # ========================================================================
    # 4. Parse autodocs
    # ========================================================================
    print("Parsing autodocs...")
    autodoc_data: dict[str, dict[str, JsonDict]] = {}
    autodoc_unmatched: dict[str, JsonDict] = {}
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
            "absolute_symbols": [
                {
                    "address": 4,
                    "name": "AbsExecBase",
                    "note": (
                        "Parser-asserted: ExecBase pointer stored at absolute "
                        "address $4. ROM Kernel Reference Manual, Exec chapter. "
                        "All Amiga programs load ExecBase via MOVEA.L ($0004).W,A6. "
                        "The pointer is to the exec.library base structure."
                    ),
                },
            ],
            "version_map": VERSION_MAP,
            "lvo_slot_size": LVO_SLOT_SIZE,
            "named_base_structs": named_base_structs,
            "version_fields_note": (
                "Function version data is split: os_since is first known OS release, "
                "while fd_version is the interface/library version marker from FD comments. "
                "They must not be conflated."
            ),
            "os_since_default_note": (
                "Functions without OS release markers default to os_since='1.0' as a lower bound. "
                "NDK 1.3 FD files lack reliable pre-1.3 OS granularity."
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
                    for a, r in zip(fd_func["args"], fd_func["regs"], strict=True)
                ]

            # Enrich from autodoc
            if func_name in autodocs:
                doc = autodocs[func_name]

                # Parse synopsis for typed inputs/outputs
                if "synopsis" in doc:
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

            _apply_input_semantics(lib_name, func_name, entry)

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

            # Detect functions that return allocated memory.
            # Criteria (from NDK autodocs): output type is a pointer
            # (void *, APTR) and output name contains "memory" or "block"
            # or function name starts with "Alloc" and returns a pointer.
            # Parser-asserted: ROM Kernel Manual, Memory Allocation chapter.
            # AllocMem returns memory block in D0, AllocVec likewise.
            # The size input register carries the allocation size.
            if out_reg and not entry.get("returns_base"):
                is_alloc_return = False
                if func_name.startswith("Alloc") and out_type in (
                        "void *", "APTR", "UBYTE *", "BYTE *",
                        "struct MemList *") or ("memory" in out_name.lower()
                      or "block" in out_name.lower()) and out_type in (
                        "void *", "APTR"):
                    is_alloc_return = True
                if is_alloc_return:
                    # Find the size input register (byteSize, memSize, etc.)
                    size_inputs = [
                        inp for inp in entry.get("inputs", [])
                        if "size" in inp.get("name", "").lower()
                        or "bytesize" in inp.get("name", "").lower()
                    ]
                    entry["returns_memory"] = {
                        "result_reg": out_reg,
                    }
                    if size_inputs:
                        entry["returns_memory"]["size_reg"] = \
                            size_inputs[0]["reg"]

            os_since = fd_func.get("os_since")
            if oc_lib and func_name in oc_lib["functions"]:
                os_since = oc_lib["functions"][func_name]

            if os_since:
                entry["os_since"] = os_since
            else:
                entry["os_since"] = "1.0"
            if fd_func.get("fd_version"):
                entry["fd_version"] = fd_func["fd_version"]

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
                            "os_since": ver,
                        }

    # --- Build structs ---
    output["structs"] = raw_structs

    # --- Build constants ---
    output["constants"] = evaluated_constants

    # ========================================================================
    # 6a. Constant domains ? map functions to relevant constants
    # ========================================================================
    # Scan autodoc text (description, inputs, results, notes) for
    # references to known constants.  Data-driven from NDK autodocs
    # and the parsed constants dict.
    print("Building constant domains...")
    resolved_consts = {name for name, c in evaluated_constants.items()
                       if c.get("value") is not None
                       and re.match(r'^[A-Z][A-Z0-9_]+$', name)}
    constant_domains: dict[str, list[str]] = {}
    if resolved_consts:
        # Build regex pattern (process in batches for regex size limits)
        sorted_names = sorted(resolved_consts, key=len, reverse=True)
        batch_size = 500
        # Scan all autodocs for constant references
        for _lib_name, lib_autodocs in autodoc_data.items():
            for func_name, doc in lib_autodocs.items():
                text_parts = []
                for key in ("description", "inputs_text", "results_text",
                             "notes"):
                    val = doc.get(key)
                    if val:
                        text_parts.append(val)
                if not text_parts:
                    continue
                full_text = "\n".join(text_parts)
                found = set()
                for i in range(0, len(sorted_names), batch_size):
                    batch = sorted_names[i:i + batch_size]
                    pattern = (r'\b(' + '|'.join(re.escape(n) for n in batch)
                               + r')\b')
                    for m in re.finditer(pattern, full_text):
                        found.add(m.group(1))
                if found:
                    constant_domains[func_name] = sorted(found)
    output["_meta"]["constant_domains"] = constant_domains
    cd_count = sum(len(v) for v in constant_domains.values())
    print(f"  {len(constant_domains)} functions with "
          f"{cd_count} constant references")

    # ========================================================================
    # 6b. Build C-to-I struct name mapping
    # ========================================================================
    # Source: NDK STRUCTURE.OFFSETS file lists C struct names with C field
    # names.  Amiga convention: C field names share a lowercase prefix
    # (e.g., is_Code, is_Data) whose uppercase form is the .I struct name
    # (IS).  We parse the file, derive prefixes, and verify against the
    # KB structs extracted from .I files.
    struct_offsets_path = os.path.join(
        ndk_root, "INCLUDES&LIBS", "STRUCTOFFSETS", "STRUCTURE.OFFSETS")
    include_h_dir = os.path.join(ndk_root, "INCLUDES&LIBS", "INCLUDE_H")
    c_to_i_map: dict[str, str] = {}
    if os.path.isfile(struct_offsets_path):
        print("Building C-to-I struct name mapping...")
        c_structs_so = parse_structure_offsets(struct_offsets_path)
        i_names = set(raw_structs.keys())
        i_names_upper = {k.upper(): k for k in i_names}

        for c_name, c_struct in c_structs_so.items():
            c_fields = tuple(field["name"] for field in cast(list[JsonDict], c_struct["fields"]))
            # Strategy 1: direct match (case-sensitive)
            if c_name in i_names:
                c_to_i_map[c_name] = c_name
                continue
            # Strategy 2: case-insensitive match
            if c_name.upper() in i_names_upper:
                c_to_i_map[c_name] = i_names_upper[c_name.upper()]
                continue
            # Strategy 3: derive from field name prefix
            # C field "is_Code" -> prefix "IS" -> I struct name
            prefixes = set()
            for fname in c_fields:
                if "_" in fname:
                    prefixes.add(fname.split("_")[0].upper())
            for prefix in sorted(prefixes, key=len, reverse=True):
                if prefix in i_names:
                    c_to_i_map[c_name] = prefix
                    break

        print(f"  {len(c_to_i_map)}/{len(c_structs_so)} C structs mapped")

        print("Parsing C header struct field types...")
        c_field_types = parse_c_struct_field_types(include_h_dir)
        print(f"  {len(c_field_types)} C struct declarations parsed")

        annotate_c_struct_field_types(
            raw_structs, c_structs_so, c_field_types, c_to_i_map)

        # Enrich function signature types with i_struct references.
        # When a function input/output type is "struct Foo *", add
        # "i_struct": "BAR" if Foo -> BAR is in the mapping.
        enriched = 0
        for lib in output["libraries"].values():
            for func in lib["functions"].values():
                for inp in func.get("inputs", []):
                    i_ref = _resolve_struct_ref(
                        inp.get("type", ""), c_to_i_map, i_names)
                    if i_ref:
                        inp["i_struct"] = i_ref
                        enriched += 1
                out = func.get("output")
                if out:
                    i_ref = _resolve_struct_ref(
                        out.get("type", ""), c_to_i_map, i_names)
                    if i_ref:
                        out["i_struct"] = i_ref
                        enriched += 1
        print(f"  {enriched} function signature types enriched with i_struct")

        callback_updates = reconcile_clib_callback_types(output, include_h_dir)
        print(f"  {callback_updates} callback input types reconciled from clib headers")

    output["_meta"]["struct_name_map"] = c_to_i_map

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
    for runtime_out in build_runtime_artifacts():
        print(f"Wrote {runtime_out}")


if __name__ == "__main__":
    main()
