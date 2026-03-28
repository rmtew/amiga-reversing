#!/usr/bin/env py.exe
"""Parse Amiga NDK 3.1 + OS_CHANGES into structured JSON knowledge base.

Parses:
- FD files: function names, register args, LVO offsets, private flags
- Autodocs: full function documentation (synopsis, description, inputs, results)
- Include files (.I): struct definitions with computed offsets, constants with evaluation
- TYPES.I: type size macros (parsed, not hardcoded)
- OS_CHANGES: version tagging (1.3 -> 2.04 -> 2.1 -> 3.0 -> 3.1 transitions)

Outputs:
- knowledge/amiga_ndk_includes_parsed.json
- knowledge/amiga_ndk_other_parsed.json
- knowledge/amiga_hw_symbols.json
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

from kb.paths import (
    AMIGA_HW_REGISTERS_JSON,
    AMIGA_HW_SYMBOLS_JSON,
    AMIGA_OS_REFERENCE_INCLUDES_PARSED_JSON,
    AMIGA_OS_REFERENCE_OTHER_PARSED_JSON,
)
from kb.runtime_builder import build_runtime_artifacts

JsonDict = dict[str, Any]


def canonicalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: canonicalize_json(value[key])
            for key in sorted(value)
        }
    if isinstance(value, list):
        return [canonicalize_json(item) for item in value]
    return value


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
        os.path.join(ndk_root, "INCLUDES1.3", "INCLUDE.I"),
        os.path.join(ndk_root, "NDK2.0-4", "INCLUDE"),
        os.path.join(ndk_root, "INCLUDES&LIBS", "INCLUDE_I"),
        os.path.join(ndk_root, "Include", "include_i"),
    ]
    existing = [path for path in candidates if os.path.isdir(path)]
    if not existing:
        recursive = [
            str(path)
            for path in Path(ndk_root).rglob("*")
            if path.is_dir()
            and path.name.lower() in {"include.i", "include_i", "include"}
            and ((path / "exec").is_dir() or (path / "EXEC").is_dir())
        ]
        existing = sorted(set(recursive))
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
                reg_text = m.group(3).strip()
                comma_groups = [
                    [reg.strip().upper() for reg in group.split("/") if reg.strip()]
                    for group in reg_text.split(",")
                    if group.strip()
                ]
                if not args:
                    if comma_groups:
                        raise ValueError(
                            f"{path}: {name} has register spec {reg_text!r} but no arguments"
                        )
                    reg_groups = []
                elif not comma_groups:
                    raise ValueError(
                        f"{path}: {name} has {len(args)} args but no register spec"
                    )
                elif len(comma_groups) == len(args):
                    reg_groups = comma_groups
                else:
                    flat_regs = [reg.strip().upper() for reg in re.split(r"[,/]", reg_text) if reg.strip()]
                    if not flat_regs:
                        raise ValueError(
                            f"{path}: {name} has {len(args)} args but no registers after parsing {reg_text!r}"
                        )
                    if len(flat_regs) % len(args) == 0:
                        group_size = len(flat_regs) // len(args)
                        reg_groups = [
                            flat_regs[index:index + group_size]
                            for index in range(0, len(flat_regs), group_size)
                        ]
                    else:
                        raise ValueError(
                            f"{path}: {name} has {len(args)} args but register spec {reg_text!r} "
                            f"cannot be aligned to arguments"
                        )
                entry = {
                    "lvo": -bias,
                    "args": args,
                    "regs": reg_groups,
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
            elif section_name in ("EXAMPLE", "EXAMPLES"):
                doc["examples"] = body
            elif section_name == "SEE ALSO":
                doc["see_also"] = body
            elif section_name == "WARNING":
                doc["warning"] = body

        doc["_lib_prefix"] = lib_prefix
        entries[func_name] = doc

    return entries


def _split_autodoc_input_sections(inputs_text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_name = None
    current_lines: list[str] = []
    for raw_line in inputs_text.splitlines():
        line = raw_line.rstrip()
        match = None
        if raw_line[:1] not in (" ", "\t"):
            match = re.match(r"^([A-Za-z_]\w*)\s+-\s*(.*)$", line)
        if match:
            if current_name is not None:
                sections[current_name] = current_lines
            current_name = match.group(1)
            current_lines = [match.group(2).strip()]
            continue
        if current_name is None:
            continue
        current_lines.append(line.strip())
    if current_name is not None:
        sections[current_name] = current_lines
    return {
        name: "\n".join(line for line in lines if line).strip()
        for name, lines in sections.items()
    }


def _api_input_value_binding(
    library: str,
    function: str,
    input_name: str,
    domain: str,
    *,
    available_since: str = "1.0",
) -> JsonDict:
    return {
        "library": library,
        "function": function,
        "input": input_name,
        "domain": domain,
        "available_since": available_since,
    }


def _struct_field_value_binding(
    owner_struct: str,
    field_name: str,
    domain: str,
    *,
    context_name: str | None = None,
    available_since: str = "1.0",
) -> JsonDict:
    binding: JsonDict = {
        "struct": owner_struct,
        "field": field_name,
        "domain": domain,
        "available_since": available_since,
    }
    if context_name is not None:
        binding["context_name"] = context_name
    return binding


def _enum_value_domain(members: list[str]) -> JsonDict:
    return {
        "kind": "enum",
        "members": members,
        "exact_match_policy": "error",
    }


def _flags_value_domain(
    members: list[str],
) -> JsonDict:
    return {
        "kind": "flags",
        "members": members,
        "exact_match_policy": "error",
        "composition": "bit_or",
        "remainder_policy": "error",
    }


# =============================================================================
# Synopsis parser ? structured inputs/outputs from autodoc synopsis
# =============================================================================

def parse_synopsis(synopsis: str, arg_names: list[str], arg_regs: list[list[str]]) -> JsonDict:
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
    synopsis_arg_names = None
    sig_arg_text = _extract_synopsis_signature_arg_text(line1)
    if sig_arg_text is not None:
        raw_arg_names = [part.strip() for part in _split_c_args(sig_arg_text)]
        if len(raw_arg_names) == len(arg_names):
            synopsis_arg_names = raw_arg_names

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
    effective_arg_names = synopsis_arg_names or arg_names
    for i, (aname, aregs) in enumerate(zip(effective_arg_names, arg_regs, strict=True)):
        inp: JsonDict = {"name": aname, "regs": [reg.upper() for reg in aregs]}
        if i < len(arg_types_from_proto):
            inp["type"] = arg_types_from_proto[i]
        elif aname in type_map:
            inp["type"] = type_map[aname]
        inputs.append(inp)

    return result


def _extract_synopsis_signature_arg_text(line: str) -> str | None:
    match = re.match(r'.+?=\s*\w+\s*\(', line)
    if match is None:
        return None
    start = match.end()
    depth = 1
    current: list[str] = []
    for ch in line[start:]:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return "".join(current).strip()
        if depth > 0:
            current.append(ch)
    return None


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


def _map_clib_args_to_inputs(
    inputs: list[JsonDict],
    args: list[dict[str, str]],
) -> dict[int, dict[str, str]]:
    mapped: dict[int, dict[str, str]] = {}
    used_arg_indexes: set[int] = set()

    by_name = {arg["name"]: idx for idx, arg in enumerate(args)}
    for index, inp in enumerate(inputs):
        arg_index = by_name.get(cast(str, inp["name"]))
        if arg_index is None:
            continue
        mapped[index] = args[arg_index]
        used_arg_indexes.add(arg_index)

    if len(inputs) != len(args):
        return mapped

    unmatched_input_indexes = [index for index in range(len(inputs)) if index not in mapped]
    unmatched_arg_indexes = [index for index in range(len(args)) if index not in used_arg_indexes]
    if len(unmatched_input_indexes) != 1 or len(unmatched_arg_indexes) != 1:
        return mapped

    unmatched_input_index = unmatched_input_indexes[0]
    unmatched_arg_index = unmatched_arg_indexes[0]
    positional_arg = args[unmatched_arg_index]
    positional_type = _normalized_type_string(positional_arg["type"])
    if _infer_input_semantic_kind(positional_type) != "code_ptr":
        return mapped

    mapped[unmatched_input_index] = positional_arg
    used_arg_indexes.add(unmatched_arg_index)

    return mapped


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
            mapped_args = _map_clib_args_to_inputs(inputs, args)
            for index, inp in enumerate(inputs):
                parsed_arg = mapped_args.get(index)
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


def _apply_input_semantics(entry: JsonDict) -> None:
    for inp in entry.get("inputs", []):
        semantic_kind = _infer_input_semantic_kind(inp.get("type"))
        if semantic_kind is not None:
            inp["semantic_kind"] = semantic_kind


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
    # Find INCLUDE_I / INCLUDE.I / INCLUDE in path
    try:
        path_parts_upper = [p.upper() for p in rel_parts]
        idx = next(
            index
            for index, part in enumerate(path_parts_upper)
            if part in {"INCLUDE_I", "INCLUDE.I", "INCLUDE"}
        )
        source = "/".join(rel_parts[idx + 1:])
    except StopIteration:
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
    - Simple arithmetic: +, -, *, <<, >>, |, !, &, ~
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

    # Binary operators (lowest precedence first): |/!, &, <<, >>, +, -, *
    # Split on operators respecting parentheses
    for ops in [('|', '!'), ('&',), ('<<', '>>'), ('+', '-'), ('*',)]:
        pos = find_operator(expr, ops)
        if pos is not None:
            op_str, op_pos, op_len = pos
            left = expr[:op_pos].strip()
            right = expr[op_pos + op_len:].strip()
            lval = resolve_constant_value(left, all_constants, depth + 1)
            rval = resolve_constant_value(right, all_constants, depth + 1)
            if lval is not None and rval is not None:
                if op_str in {'|', '!'}:
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


def collect_raw_constants_from_include_dir(
    include_dir: str,
    type_sizes: dict[str, int],
) -> tuple[dict[str, object], list[str]]:
    raw_constants: dict[str, object] = {}
    parsed_include_paths: list[str] = []
    include_subdirs = sorted([
        d for d in os.listdir(include_dir)
        if os.path.isdir(os.path.join(include_dir, d))
    ])
    sized_types = sorted(
        (t for t, s in type_sizes.items()
         if s > 0 and t not in ("STRUCT", "ALIGNWORD", "ALIGNLONG")),
        key=len,
        reverse=True,
    )
    type_alt = "|".join(re.escape(t) for t in sized_types)
    sim_type_re = re.compile(rf'\s+({type_alt})\s+(\w+)') if sized_types else None

    for pass_num in range(2):
        for subdir in include_subdirs:
            subdir_path = os.path.join(include_dir, subdir)
            for fname in sorted(os.listdir(subdir_path)):
                if not fname.upper().endswith(".I"):
                    continue
                fpath = os.path.join(subdir_path, fname)
                if pass_num == 0:
                    parsed_include_paths.append(fpath)
                eoffset = 0
                soffset: int | None = 0
                cmd_count: int | None = None
                in_struct = False
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.rstrip()

                        cm = re.match(r'^(\w+)\s+[Ee][Qq][Uu]\s+(.+?)(?:\s*[;*].*)?$', line)
                        if cm:
                            raw_constants[cm.group(1)] = cm.group(2).strip()
                            continue

                        cm = re.match(r'^(\w+)\s+SET\s+(.+?)(?:\s*[;*].*)?$', line)
                        if cm and not cm.group(1).endswith("_I") and cm.group(1) not in ("SOFFSET", "EOFFSET"):
                            raw_constants[cm.group(1)] = cm.group(2).strip()
                            continue

                        bm = re.match(r'\s+BITDEF\s+(\w+),(\w+),(\d+)', line)
                        if bm:
                            prefix = bm.group(1)
                            name = bm.group(2)
                            bitnum = bm.group(3)
                            raw_constants[f"{prefix}B_{name}"] = bitnum
                            raw_constants[f"{prefix}F_{name}"] = f"(1<<{bitnum})"
                            continue

                        dm = re.match(r'\s+DEVINIT(?:\s+(\S+))?\s*$', line)
                        if dm:
                            base_expr = dm.group(1) or "CMD_NONSTD"
                            cmd_count = resolve_constant_value(base_expr, raw_constants)
                            continue

                        dm = re.match(r'\s+DEVCMD\s+(\w+)', line)
                        if dm:
                            if cmd_count is None:
                                continue
                            raw_constants[dm.group(1)] = str(cmd_count)
                            cmd_count += 1
                            continue

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

                        em = re.match(r'\s+EITEM\s+(\w+)', line)
                        if em:
                            raw_constants[em.group(1)] = str(eoffset)
                            eoffset += 1
                            continue

                        sm = re.match(r'\s+STRUCTURE\s+(\w+),(\w+)', line)
                        if sm:
                            struct_name = sm.group(1)
                            init_str = sm.group(2)
                            raw_constants[struct_name] = "0"
                            try:
                                soffset = int(init_str)
                            except ValueError:
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
                            tm = sim_type_re.match(line)
                            if tm:
                                raw_constants[tm.group(2)] = str(soffset)
                                soffset += type_sizes[tm.group(1)]
                                continue

                            ssm = re.match(r'\s+STRUCT\s+(\w+),(\w+)', line)
                            if ssm:
                                raw_constants[ssm.group(1)] = str(soffset)
                                size_str = ssm.group(2)
                                try:
                                    soffset += int(size_str)
                                except ValueError:
                                    if size_str in raw_constants:
                                        try:
                                            soffset += int(cast(str, raw_constants[size_str]))
                                        except (ValueError, TypeError):
                                            in_struct = False
                                    else:
                                        in_struct = False
                                continue

                            lm = re.match(r'\s+LABEL\s+(\w+)', line)
                            if lm:
                                raw_constants[lm.group(1)] = str(soffset)
                                continue

                            if re.match(r'\s+ALIGNWORD\b', line):
                                soffset = (soffset + 1) & ~1
                                continue

                            if re.match(r'\s+ALIGNLONG\b', line):
                                soffset = (soffset + 3) & ~3
                                continue

    return raw_constants, parsed_include_paths


def _field_key(struct_name: str, field_name: str) -> str:
    return f"{struct_name}.{field_name}"


def _include_source_from_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    marker = "/Include_I/"
    idx = normalized.lower().find(marker.lower())
    if idx == -1:
        raise ValueError(f"Unable to derive include source from {path}")
    return normalized[idx + len(marker):].upper()


def _parse_bitdef_constants(
        lines: list[str], evaluated_constants: dict[str, JsonDict]
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    prefix_constants: dict[str, list[str]] = defaultdict(list)
    io_flags_prefix_constants: dict[str, list[str]] = defaultdict(list)
    recent_comments: list[str] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.startswith(("*", ";")):
            comment = stripped.lstrip("*;").strip()
            if comment:
                recent_comments.append(comment)
                if len(recent_comments) > 4:
                    recent_comments.pop(0)
            continue
        match = re.match(r"\s+BITDEF\s+(\w+),(\w+),(\d+)", raw_line)
        if not match:
            recent_comments.clear()
            continue
        prefix = match.group(1)
        name = match.group(2)
        flag_name = f"{prefix}F_{name}"
        if evaluated_constants[flag_name]["value"] is None:
            raise ValueError(f"Unresolved BITDEF flag constant {flag_name}")
        prefix_constants[prefix].append(flag_name)
        if "IO_FLAGS" in " ".join(recent_comments):
            io_flags_prefix_constants[prefix].append(flag_name)
        recent_comments.clear()
    return dict(prefix_constants), dict(io_flags_prefix_constants)


def _parse_devcmd_constants(
        lines: list[str], evaluated_constants: dict[str, JsonDict]
) -> list[str]:
    command_names: list[str] = []
    for raw_line in lines:
        match = re.match(r"\s+DEVCMD\s+(\w+)", raw_line)
        if not match:
            continue
        command_name = match.group(1)
        if evaluated_constants[command_name]["value"] is None:
            raise ValueError(f"Unresolved DEVCMD constant {command_name}")
        command_names.append(command_name)
    return command_names


def _parse_prefixed_constant_names(
        lines: list[str], evaluated_constants: dict[str, JsonDict], prefix: str
) -> list[str]:
    result: list[str] = []
    pattern = re.compile(rf"^\s*({re.escape(prefix)}\w*)\s+EQU\b")
    for raw_line in lines:
        match = pattern.match(raw_line)
        if not match:
            continue
        constant_name = match.group(1)
        if evaluated_constants[constant_name]["value"] is None:
            raise ValueError(f"Unresolved constant {constant_name}")
        result.append(constant_name)
    return result


def _parse_device_name(path: str, source: str, lines: list[str]) -> str | None:
    candidates = {
        match.group(1)
        for line in lines
        for match in [re.search(r"'([^']+\.device)'", line)]
        if match is not None
    }
    if not candidates:
        # Parser-asserted from NDK device include layout: DEVICES/<NAME>.I is the
        # canonical include for <name>.device even when the file only carries a
        # prose header ("clipboard.device structure definitions") and no literal
        # '*.device' string.
        if source.upper().startswith("DEVICES/"):
            return f"{Path(path).stem.lower()}.device"
        return None
    if len(candidates) != 1:
        raise ValueError(f"Ambiguous device names in include: {sorted(candidates)}")
    return next(iter(candidates))


def parse_include_value_bindings(
        path: str, evaluated_constants: dict[str, JsonDict]
) -> tuple[dict[str, JsonDict], list[JsonDict]]:
    source = _include_source_from_path(path)
    with open(path, encoding="utf-8", errors="replace") as handle:
        lines = [line.rstrip() for line in handle]

    value_domains: dict[str, JsonDict] = {}
    field_bindings: list[JsonDict] = []
    prefix_constants, io_flags_prefix_constants = _parse_bitdef_constants(lines, evaluated_constants)

    if source == "EXEC/IO.I":
        command_domain_name = "exec.io.command"
        command_names = _parse_devcmd_constants(lines, evaluated_constants)
        if not command_names:
            raise ValueError("EXEC/IO.I is missing standard device commands")
        value_domains[command_domain_name] = _enum_value_domain(command_names)
        field_bindings.append(_struct_field_value_binding("IO", "IO_COMMAND", command_domain_name))

        io_flag_names = prefix_constants.get("IO")
        if not io_flag_names:
            raise ValueError("EXEC/IO.I is missing IO flag bit definitions")
        flag_domain_name = "exec.io.flags"
        value_domains[flag_domain_name] = _flags_value_domain(io_flag_names)
        field_bindings.append(_struct_field_value_binding("IO", "IO_FLAGS", flag_domain_name))
        return value_domains, field_bindings

    source_upper = source.upper()
    if not source_upper.startswith("DEVICES/"):
        return value_domains, field_bindings
    device_commands = _parse_devcmd_constants(lines, evaluated_constants)
    if not device_commands:
        return value_domains, field_bindings

    # Parser-asserted from exec/io.i DEVINIT/DEVCMD semantics:
    # device include DEVCMD values populate IO.IO_COMMAND for that device context.
    device_name = _parse_device_name(path, source, lines)
    if device_name is None:
        raise ValueError(f"Device include {source} defines DEVCMD values but no '*.device' name string")

    command_domain_name = f"{device_name}.io_command"
    etd_commands = _parse_prefixed_constant_names(lines, evaluated_constants, "ETD_")
    value_domains[command_domain_name] = _enum_value_domain(device_commands + etd_commands)
    field_bindings.append(
        _struct_field_value_binding(
            "IO",
            "IO_COMMAND",
            command_domain_name,
            context_name=device_name,
        )
    )

    io_flag_prefixes = sorted(io_flags_prefix_constants)
    if io_flag_prefixes:
        if len(io_flag_prefixes) != 1:
            raise ValueError(
                f"Ambiguous IO flag prefixes for {device_name}: {io_flag_prefixes}"
            )
        flag_domain_name = f"{device_name}.io_flags"
        value_domains[flag_domain_name] = _flags_value_domain(
            io_flags_prefix_constants[io_flag_prefixes[0]]
        )
        field_bindings.append(
            _struct_field_value_binding(
                "IO",
                "IO_FLAGS",
                flag_domain_name,
                context_name=device_name,
            )
        )

    return value_domains, field_bindings


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


def lib_name_to_fd_stem(lib_name: str) -> str:
    """Convert canonical library/device/resource name back to FD stem."""
    base_name = lib_name.rsplit(".", 1)[0]
    for alias, canonical in FD_NAME_MAP.items():
        if canonical == base_name:
            return alias
    return base_name


def _canonical_include_relpath(lib_name: str, fd_stem: str) -> str:
    base_name, kind = lib_name.rsplit(".", 1)
    stem_lower = fd_stem.lower()
    if kind == "device":
        return f"devices/{base_name.lower()}.i"
    if kind == "resource":
        return f"resources/{base_name.lower()}.i"
    if kind == "gadget":
        return f"gadgets/{base_name.lower()}.i"
    if kind == "datatype":
        return f"datatypes/{base_name.lower()}.i"
    return f"{base_name.lower()}/{stem_lower}_lib.i"


def _native_include_candidates(include_dir: str, lib_name: str, fd_stem: str) -> list[tuple[str, str]]:
    base_name, kind = lib_name.rsplit(".", 1)
    stem_upper = fd_stem.upper()
    if kind == "device":
        return [(os.path.join(include_dir, "DEVICES", f"{base_name.upper()}.I"), f"devices/{base_name.lower()}.i")]
    if kind == "resource":
        return [(os.path.join(include_dir, "RESOURCES", f"{base_name.upper()}.I"), f"resources/{base_name.lower()}.i")]
    if kind == "gadget":
        return [(os.path.join(include_dir, "GADGETS", f"{base_name.upper()}.I"), f"gadgets/{base_name.lower()}.i")]
    if kind == "datatype":
        return [(os.path.join(include_dir, "DATATYPES", f"{base_name.upper()}.I"), f"datatypes/{base_name.lower()}.i")]
    return [
        (os.path.join(include_dir, base_name.upper(), f"{stem_upper}_LIB.I"), f"{base_name.lower()}/{fd_stem.lower()}_lib.i"),
        (os.path.join(include_dir, "LIBRARIES", f"{stem_upper}_LIB.I"), f"{base_name.lower()}/{fd_stem.lower()}_lib.i"),
    ]


def build_os_include_kb(
    include_dir: str,
    fd_dir: str,
    fd_data: dict[str, JsonDict],
) -> JsonDict:
    library_lvo_owners: dict[str, JsonDict] = {}
    sources: list[JsonDict] = []

    for lib_name in sorted(fd_data):
        fd_stem = lib_name_to_fd_stem(lib_name)
        native_match = None
        for candidate_path, candidate_relpath in _native_include_candidates(include_dir, lib_name, fd_stem):
            if os.path.isfile(candidate_path):
                native_match = (candidate_path, candidate_relpath)
                break
        if native_match is not None:
            source_path, include_path = native_match
            source_file = source_path.replace(os.sep, "/")
            library_lvo_owners[lib_name] = {
                "kind": "native_include",
                "include_path": include_path,
                "comment_include_path": include_path,
                "source_file": source_file,
            }
            sources.append({
                "type": "official",
                "file": source_file,
                "description": f"Native Amiga NDK include file for {lib_name}",
            })
            continue

        fd_path = os.path.join(fd_dir, f"{fd_stem.upper()}_LIB.FD")
        if not os.path.isfile(fd_path):
            raise ValueError(f"Missing FD file for library include ownership: {fd_path}")
        library_lvo_owners[lib_name] = {
            "kind": "fd_only",
            "include_path": None,
            "comment_include_path": _canonical_include_relpath(lib_name, fd_stem),
            "source_file": fd_path.replace(os.sep, "/"),
        }
        sources.append({
            "type": "official",
            "file": fd_path.replace(os.sep, "/"),
            "description": f"FD-derived LVO ownership for {lib_name}",
        })

    return {
        "sources": sources,
        "library_lvo_owners": library_lvo_owners,
    }


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

COMPATIBILITY_VERSIONS = ("1.3", "2.0", "3.1", "3.5")


def _compatibility_version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _normalize_include_relpath(path: str) -> str:
    return path.replace("\\", "/").lower()


def _canonical_ndk_root_version(path: str) -> str | None:
    base = os.path.basename(os.path.normpath(path)).upper()
    if base == "NDK_1.3":
        return "1.3"
    if base == "NDK_2.0":
        return "2.0"
    if base == "NDK_3.1":
        return "3.1"
    if base == "NDK_3.5":
        return "3.5"
    return None


def discover_compatibility_ndk_roots(primary_ndk_root: str) -> dict[str, str]:
    parent = os.path.dirname(os.path.normpath(primary_ndk_root))
    discovered: dict[str, str] = {}
    for entry in sorted(os.listdir(parent)):
        full_path = os.path.join(parent, entry)
        if not os.path.isdir(full_path):
            continue
        version = _canonical_ndk_root_version(full_path)
        if version is None:
            continue
        discovered[version] = full_path
    return {
        version: discovered[version]
        for version in COMPATIBILITY_VERSIONS
        if version in discovered
    }


def _find_fd_dir(root: str) -> str | None:
    root_path = Path(root)
    for candidate in (
        root_path / "INCLUDES&LIBS" / "FD",
        root_path / "FD",
        root_path / "LIBS" / "FD",
    ):
        if candidate.is_dir():
            return str(candidate)
    matches = [path for path in root_path.rglob("*.FD") if path.is_file()]
    if not matches:
        return None
    return str(matches[0].parent)


def build_fd_function_min_versions(ndk_roots: dict[str, str]) -> dict[tuple[str, str], str]:
    function_min_versions: dict[tuple[str, str], str] = {}
    for version in COMPATIBILITY_VERSIONS:
        root = ndk_roots.get(version)
        if root is None:
            continue
        fd_dir = _find_fd_dir(root)
        if fd_dir is None:
            continue
        for fd_path in sorted(Path(fd_dir).glob("*_LIB.FD")):
            fd_stem = fd_path.stem.removesuffix("_LIB").lower()
            lib_name = fd_stem_to_lib_name(fd_stem)
            for function_name in scan_fd_function_names(str(fd_path)):
                function_min_versions.setdefault((lib_name, function_name), version)
    return function_min_versions


def scan_fd_function_names(path: str) -> list[str]:
    names: list[str] = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith(("*", "##")):
                continue
            match = re.match(r"^([A-Za-z_]\w*)", line)
            if match is None:
                continue
            names.append(match.group(1))
    return names


def _find_include_source_file(root: str, rel_source: str) -> str | None:
    norm_rel = _normalize_include_relpath(rel_source)
    rel_parts = tuple(part for part in norm_rel.split("/") if part)
    basename = rel_parts[-1]
    candidates: list[str] = []
    for candidate in Path(root).rglob(basename):
        candidate_parts = tuple(part.lower() for part in candidate.parts)
        if len(candidate_parts) < len(rel_parts):
            continue
        if candidate_parts[-len(rel_parts):] != rel_parts:
            continue
        if "include-strip" in str(candidate).lower():
            continue
        candidates.append(str(candidate))
    if not candidates:
        return None
    candidates.sort(key=lambda value: (len(value), value.lower()))
    return candidates[0]


def _find_exec_autodoc_file(root: str) -> str | None:
    for candidate in Path(root).rglob("EXEC.DOC"):
        candidate_str = str(candidate).lower()
        if "autodocs" not in candidate_str and "\\doc" not in candidate_str and "/doc" not in candidate_str:
            continue
        return str(candidate)
    return None


def _scan_libdef_symbols(path: str) -> list[str]:
    symbols: list[str] = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"\s+LIBDEF\s+(\w+)", line)
        if match is not None:
            symbols.append(match.group(1))
    return symbols


def _build_resident_autoinit_contract(ndk_roots: dict[str, str]) -> JsonDict:
    doc_path = None
    for version in ("2.0", "3.1", "3.5", "1.3"):
        root = ndk_roots.get(version)
        if root is None:
            continue
        candidate = _find_exec_autodoc_file(root)
        if candidate is not None:
            doc_path = candidate
            break
    if doc_path is None:
        raise ValueError("Missing primary-source EXEC.DOC for resident autoinit contract")
    exec_doc = Path(doc_path).read_text(encoding="utf-8", errors="replace")
    exec_doc_lower = exec_doc.lower()
    required_phrases = (
        "rt_init pointer which points",
        "four longwords",
        "specific function offsets, terminated with -1l",
        "pointer to data table in exec/initstruct format",
    )
    for phrase in required_phrases:
        if phrase not in exec_doc_lower:
            raise ValueError(f"EXEC.DOC is missing required resident autoinit phrase: {phrase!r}")
    if (
        "pointer to library initialization function, or null" not in exec_doc_lower
        and "pointer to library initialization routine, or null" not in exec_doc_lower
        and "pointer to library initialization routine, which will receive" not in exec_doc_lower
    ):
        raise ValueError("EXEC.DOC is missing resident autoinit init-function description")

    library_prefixes: list[str] = []
    device_prefixes: list[str] = []
    for version in COMPATIBILITY_VERSIONS:
        root = ndk_roots.get(version)
        if root is None:
            continue
        libraries_path = _find_include_source_file(root, "exec/libraries.i")
        io_path = _find_include_source_file(root, "exec/io.i")
        if libraries_path is not None and not library_prefixes:
            library_prefixes = _scan_libdef_symbols(libraries_path)
        if libraries_path is not None and io_path is not None and not device_prefixes:
            device_prefixes = library_prefixes + _scan_libdef_symbols(io_path)
        if library_prefixes and device_prefixes:
            break
    if not library_prefixes:
        raise ValueError("Missing primary-source exec/libraries.i standard vector definitions")
    if not device_prefixes:
        raise ValueError("Missing primary-source exec/io.i device vector definitions")
    return {
        "resident_autoinit_words": [
            "base_size",
            "vectors",
            "structure_init",
            "init_func",
        ],
        "resident_autoinit_supports_short_vectors": "(short format offsets are also acceptable)" in exec_doc_lower,
        "resident_vector_prefixes": {
            "library": library_prefixes,
            "device": device_prefixes,
        },
    }


def _scan_struct_layouts_from_include(
    path: str,
    type_sizes: dict[str, int],
    all_constants: dict[str, object],
) -> dict[str, list[dict[str, int | str]]]:
    parsed = parse_asm_include(path, type_sizes, all_constants)
    layouts: dict[str, list[dict[str, int | str]]] = {}
    for struct_name, struct_def in cast(dict[str, JsonDict], parsed["structs"]).items():
        offset_slots: dict[int, int] = {}
        fields: list[dict[str, int | str]] = []
        for field in cast(list[JsonDict], struct_def["fields"]):
            offset = cast(int, field["offset"])
            slot = offset_slots.get(offset, 0)
            offset_slots[offset] = slot + 1
            fields.append({
                "name": cast(str, field["name"]),
                "type": cast(str, field["type"]),
                "offset": offset,
                "slot": slot,
            })
        layouts[struct_name] = fields
    return layouts


def build_os_compatibility_kb(
    ndk_roots: dict[str, str],
    include_kb: JsonDict,
    structs: dict[str, JsonDict],
    all_constants: dict[str, object],
) -> JsonDict:
    include_min_versions: dict[str, str] = {}
    function_min_versions = build_fd_function_min_versions(ndk_roots)
    constant_min_versions: dict[str, str] = {}
    struct_min_versions: dict[str, str] = {}
    field_min_versions: dict[tuple[str, str], str] = {}
    field_names_by_version: dict[tuple[str, str], dict[str, str]] = {}

    include_paths = {
        _normalize_include_relpath(cast(str, owner["include_path"]))
        for owner in cast(dict[str, JsonDict], include_kb["library_lvo_owners"]).values()
        if owner["include_path"] is not None
    }
    include_paths.update(
        _normalize_include_relpath(cast(str, struct_def["source"]))
        for struct_def in structs.values()
    )

    scanned_structs: dict[tuple[str, str], dict[str, list[dict[str, int | str]]]] = {}
    for version, root in ndk_roots.items():
        version_include_dir = resolve_include_i_dir(root)
        version_type_sizes = scan_type_macros(version_include_dir)
        version_raw_constants, _ = collect_raw_constants_from_include_dir(
            version_include_dir,
            version_type_sizes,
        )
        for constant_name in sorted(version_raw_constants):
            if constant_name in all_constants:
                constant_min_versions.setdefault(constant_name, version)
        for include_rel in include_paths:
            include_path = _find_include_source_file(root, include_rel)
            if include_path is None:
                continue
            include_min_versions.setdefault(include_rel, version)
            scanned_structs[(version, include_rel)] = _scan_struct_layouts_from_include(
                include_path,
                version_type_sizes,
                all_constants,
            )

    for struct_name, struct_def in structs.items():
        source = _normalize_include_relpath(cast(str, struct_def["source"]))
        struct_versions = [
            version
            for version in COMPATIBILITY_VERSIONS
            if (version, source) in scanned_structs
            and struct_name in scanned_structs[(version, source)]
        ]
        if not struct_versions:
            raise ValueError(f"Missing compatibility availability for struct {struct_name} from {source}")
        struct_min_versions[struct_name] = struct_versions[0]
        field_slots: dict[int, int] = {}
        for field in cast(list[JsonDict], struct_def["fields"]):
            field_name = cast(str, field["name"])
            field_offset = cast(int, field["offset"])
            field_type = cast(str, field["type"])
            field_slot = field_slots.get(field_offset, 0)
            field_slots[field_offset] = field_slot + 1
            names_by_version = {
                version: cast(str, matches[0]["name"])
                for version in COMPATIBILITY_VERSIONS
                if (version, source) in scanned_structs
                for matches in [[
                    entry for entry in scanned_structs[(version, source)].get(struct_name, [])
                    if entry["offset"] == field_offset
                    and entry["slot"] == field_slot
                    and entry["type"] == field_type
                ]]
                if matches
            }
            if not names_by_version:
                raise ValueError(
                    f"Missing compatibility availability for struct field {struct_name}.{field_name} from {source}"
                )
            first_version = min(names_by_version, key=_compatibility_version_key)
            field_min_versions[(struct_name, field_name)] = first_version
            field_names_by_version[(struct_name, field_name)] = names_by_version

    for owner in cast(dict[str, JsonDict], include_kb["library_lvo_owners"]).values():
        include_path = owner["include_path"]
        owner["available_since"] = None if include_path is None else include_min_versions[_normalize_include_relpath(cast(str, include_path))]

    for struct_name, struct_def in structs.items():
        struct_def["available_since"] = struct_min_versions[struct_name]
        for field in cast(list[JsonDict], struct_def["fields"]):
            field["available_since"] = field_min_versions[(struct_name, cast(str, field["name"]))]
            names_by_version = field_names_by_version[(struct_name, cast(str, field["name"]))]
            if len(set(names_by_version.values())) > 1:
                field["names_by_version"] = names_by_version
            else:
                field.pop("names_by_version", None)

    resident_autoinit_contract = _build_resident_autoinit_contract(ndk_roots)
    return {
        "compatibility_versions": [version for version in COMPATIBILITY_VERSIONS if version in ndk_roots],
        "include_min_versions": include_min_versions,
        "resident_autoinit_words": resident_autoinit_contract["resident_autoinit_words"],
        "resident_autoinit_supports_short_vectors": resident_autoinit_contract["resident_autoinit_supports_short_vectors"],
        "resident_vector_prefixes": resident_autoinit_contract["resident_vector_prefixes"],
        "_function_min_versions": {
            f"{library}/{function}": version
            for (library, function), version in sorted(function_min_versions.items())
        },
        "_constant_min_versions": dict(sorted(constant_min_versions.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse Amiga NDK 3.1 + OS_CHANGES into structured JSON"
    )
    parser.add_argument("ndk_root", help="Path to NDK root directory")
    parser.add_argument("--os-changes", help="Path to OS_CHANGES directory")
    parser.add_argument(
        "--includes-parsed-outfile",
        default=str(AMIGA_OS_REFERENCE_INCLUDES_PARSED_JSON),
    )
    parser.add_argument(
        "--other-parsed-outfile",
        default=str(AMIGA_OS_REFERENCE_OTHER_PARSED_JSON),
    )
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
        json.dump(canonicalize_json(hardware_output), handle, indent=2, ensure_ascii=False)
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
    parsed_include_paths: list[str] = []

    include_subdirs = sorted([
        d for d in os.listdir(include_dir)
        if os.path.isdir(os.path.join(include_dir, d))
    ])
    print(f"  Subdirectories: {', '.join(include_subdirs)}")

    # First pass: collect all constants (needed for struct offset resolution).
    # This also simulates STRUCTURE macros to extract field-name constants
    # (e.g. LN_SUCC EQU 0, LN_SIZE EQU 14) which are generated at assembly
    # time by the macros in TYPES.I.
    raw_constants, parsed_include_paths = collect_raw_constants_from_include_dir(
        include_dir,
        type_sizes,
    )

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
    print("Building OS include ownership KB...")
    include_kb = build_os_include_kb(include_dir, fd_dir, fd_data)
    print(f"  {len(include_kb['library_lvo_owners'])} library include ownership entries")
    compatibility_ndk_roots = discover_compatibility_ndk_roots(ndk_root)
    print("Building compatibility availability KB...")
    compatibility_kb = build_os_compatibility_kb(
        compatibility_ndk_roots,
        include_kb,
        raw_structs,
        raw_constants,
    )
    print(
        f"  {len(compatibility_kb['compatibility_versions'])} NDK versions, "
        f"{len(compatibility_kb['include_min_versions'])} include availability entries"
    )
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

    includes_output = {
        "_meta": {
            "type_sizes": dict(sorted(type_sizes.items())),
            "lvo_slot_size": LVO_SLOT_SIZE,
            "compatibility_versions": compatibility_kb["compatibility_versions"],
            "include_min_versions": compatibility_kb["include_min_versions"],
            "resident_autoinit_words": compatibility_kb["resident_autoinit_words"],
            "resident_autoinit_supports_short_vectors": compatibility_kb["resident_autoinit_supports_short_vectors"],
            "resident_vector_prefixes": compatibility_kb["resident_vector_prefixes"],
            "named_base_structs": named_base_structs,
            "value_domains": {},
            "api_input_value_bindings": [],
            "api_input_semantic_assertions": [],
            "struct_field_value_bindings": [],
            "library_lvo_owners": include_kb["library_lvo_owners"],
        },
        "libraries": {},
        "structs": {},
        "constants": {},
    }
    other_output = {
        "_meta": {
            "source": "NDK autodocs and OS_CHANGES",
            "ndk_path": ndk_root,
            "version_map": VERSION_MAP,
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
        includes_lib_entry = {
            "base": fd_info["base"],
            "functions": {},
            "lvo_index": {},
        }
        other_lib_entry: JsonDict = {
            "functions": {},
        }

        # Get OS_CHANGES version info for this library
        oc_lib = None
        if os_version_map:
            oc_lib = os_version_map["libraries"].get(lib_name)

        autodocs = autodoc_data.get(lib_name, {})

        for func_name, fd_func in fd_info["functions"].items():
            includes_entry = {
                "lvo": fd_func["lvo"],
            }
            other_entry: JsonDict = {}

            # Build inputs from FD args/regs
            if fd_func["args"]:
                includes_entry["inputs"] = [
                    {"name": a, "regs": list(r)}
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
                        other_entry["inputs"] = parsed["inputs"]
                    if parsed["output"]:
                        other_entry["output"] = parsed["output"]

                if "description" in doc:
                    other_entry["description"] = doc["description"]
                if "notes" in doc:
                    other_entry["notes"] = doc["notes"]
                if "bugs" in doc:
                    other_entry["bugs"] = doc["bugs"]
                if "warning" in doc:
                    other_entry["warning"] = doc["warning"]

                # No-return detection
                if check_no_return(doc):
                    other_entry["no_return"] = True

            _apply_input_semantics(includes_entry)
            _apply_input_semantics(other_entry)

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
            func_output = other_entry.get("output", {})
            out_type = func_output.get("type", "")
            out_name = func_output.get("name", "")
            out_reg = func_output.get("reg")
            if out_reg and (
                "Library *" in out_type
                or (out_name == "resource" and out_type in ("APTR", "void *"))
            ):
                # Find the name-string input register
                name_inputs = [
                    inp for inp in other_entry.get("inputs", [])
                    if "name" in inp.get("name", "").lower()
                    and inp.get("type") in ("STRPTR", "APTR", "char *",
                                            "UBYTE *", "void *")
                ]
                if name_inputs:
                    if len(name_inputs[0]["regs"]) != 1:
                        raise ValueError(
                            f"{lib_name}/{func_name}: returns_base name input must use one register"
                        )
                    other_entry["returns_base"] = {
                        "name_reg": name_inputs[0]["regs"][0],
                        "base_reg": out_reg,
                    }

            # Detect functions that return allocated memory.
            # Criteria (from NDK autodocs): output type is a pointer
            # (void *, APTR) and output name contains "memory" or "block"
            # or function name starts with "Alloc" and returns a pointer.
            # Parser-asserted: ROM Kernel Manual, Memory Allocation chapter.
            # AllocMem returns memory block in D0, AllocVec likewise.
            # The size input register carries the allocation size.
            if out_reg and not other_entry.get("returns_base"):
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
                        inp for inp in other_entry.get("inputs", [])
                        if "size" in inp.get("name", "").lower()
                        or "bytesize" in inp.get("name", "").lower()
                    ]
                    other_entry["returns_memory"] = {
                        "result_reg": out_reg,
                    }
                    if size_inputs:
                        if len(size_inputs[0]["regs"]) != 1:
                            raise ValueError(
                                f"{lib_name}/{func_name}: returns_memory size input must use one register"
                            )
                        other_entry["returns_memory"]["size_reg"] = \
                            size_inputs[0]["regs"][0]

            os_since = compatibility_kb["_function_min_versions"].get(f"{lib_name}/{func_name}")
            explicit_fd_os_since = fd_func.get("os_since")
            if explicit_fd_os_since:
                os_since = explicit_fd_os_since
            if oc_lib and func_name in oc_lib["functions"]:
                os_since = oc_lib["functions"][func_name]

            if os_since:
                other_entry["os_since"] = os_since
            else:
                other_entry["os_since"] = "1.0"
            includes_entry["available_since"] = cast(str, other_entry["os_since"])
            if fd_func.get("fd_version"):
                includes_entry["fd_version"] = fd_func["fd_version"]

            # Private flag (only if true)
            if fd_func.get("private"):
                includes_entry["private"] = True

            includes_lib_entry["functions"][func_name] = includes_entry
            if other_entry:
                other_lib_entry["functions"][func_name] = other_entry
            includes_lib_entry["lvo_index"][str(fd_func["lvo"])] = func_name

        includes_output["libraries"][lib_name] = includes_lib_entry
        other_output["libraries"][lib_name] = other_lib_entry

    # Add functions from OS_CHANGES that are in libraries we have but not in our FD
    if os_version_map:
        for oc_lib_name, oc_lib_info in os_version_map["libraries"].items():
            if oc_lib_name in other_output["libraries"]:
                lib = other_output["libraries"][oc_lib_name]
                for func_name, ver in oc_lib_info["functions"].items():
                    if func_name not in lib["functions"]:
                        lib["functions"][func_name] = {
                            "lvo": None,
                            "os_since": ver,
                        }

    # --- Build structs ---
    includes_output["structs"] = raw_structs

    # --- Build constants ---
    includes_output["constants"] = {
        name: {
            "raw": entry["raw"],
            "value": entry["value"],
            "available_since": compatibility_kb["_constant_min_versions"].get(name, "1.0"),
        }
        for name, entry in evaluated_constants.items()
    }

    print("Building value domains and bindings...")
    parsed_value_domains: dict[str, JsonDict] = {}
    struct_field_value_bindings: list[JsonDict] = []
    for include_path in sorted(set(parsed_include_paths)):
        include_value_domains, include_field_bindings = (
            parse_include_value_bindings(include_path, evaluated_constants)
        )
        for domain_name, domain_data in include_value_domains.items():
            existing_domain_data = parsed_value_domains.get(domain_name)
            if existing_domain_data is not None and existing_domain_data != domain_data:
                raise ValueError(
                    f"Conflicting value domain {domain_name}: {existing_domain_data} vs {domain_data}"
                )
            parsed_value_domains[domain_name] = domain_data
        struct_field_value_bindings.extend(include_field_bindings)
    struct_binding_keys: set[tuple[str, str, str | None]] = set()
    for field_binding in struct_field_value_bindings:
        struct_name = cast(str, field_binding["struct"])
        field_name = cast(str, field_binding["field"])
        domain_name = cast(str, field_binding["domain"])
        context_name = cast(str | None, field_binding.get("context_name"))
        struct_def = includes_output["structs"].get(struct_name)
        if struct_def is None:
            raise ValueError(f"Struct field value binding references missing struct {struct_name}")
        if domain_name not in parsed_value_domains:
            raise ValueError(
                f"Struct field value binding references missing value domain {domain_name}"
            )
        if not any(cast(str, field["name"]) == field_name for field in struct_def["fields"]):
            raise ValueError(
                f"Struct field value binding references missing field {struct_name}.{field_name}"
            )
        struct_binding_key = (struct_name, field_name, context_name)
        if struct_binding_key in struct_binding_keys:
            raise ValueError(f"Duplicate struct field value binding for {struct_binding_key}")
        struct_binding_keys.add(struct_binding_key)
    includes_output["_meta"]["value_domains"] = parsed_value_domains
    includes_output["_meta"]["api_input_value_bindings"] = []
    includes_output["_meta"]["struct_field_value_bindings"] = sorted(
        struct_field_value_bindings,
        key=lambda binding: (
            cast(str, binding["struct"]),
            cast(str, binding["field"]),
            cast(str, binding.get("context_name", "")),
        ),
    )
    print(
        f"  {len(parsed_value_domains)} value domains, "
        "0 API input bindings, "
        f"{len(struct_field_value_bindings)} struct field bindings"
    )

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
        for lib in other_output["libraries"].values():
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

        callback_updates = (
            reconcile_clib_callback_types(includes_output, include_h_dir)
            + reconcile_clib_callback_types(other_output, include_h_dir)
        )
        print(f"  {callback_updates} callback input types reconciled from clib headers")

    includes_output["_meta"]["struct_name_map"] = c_to_i_map
    other_output["_meta"]["struct_name_map"] = c_to_i_map

    # ========================================================================
    # 7. Summary
    # ========================================================================
    merged_libraries = json.loads(json.dumps(includes_output["libraries"]))
    for lib_name, other_library in other_output["libraries"].items():
        merged_library = merged_libraries[lib_name]
        for func_name, function_overlay in other_library["functions"].items():
            if func_name not in merged_library["functions"]:
                merged_library["functions"][func_name] = function_overlay
                continue
            merged_library["functions"][func_name].update(function_overlay)

    total_funcs = sum(len(v["functions"]) for v in merged_libraries.values())
    documented = sum(
        1 for lib in merged_libraries.values()
        for f in lib["functions"].values()
        if "description" in f
    )
    no_return_count = sum(
        1 for lib in merged_libraries.values()
        for f in lib["functions"].values()
        if f.get("no_return")
    )
    with_types = sum(
        1 for lib in merged_libraries.values()
        for f in lib["functions"].values()
        if any("type" in inp for inp in f.get("inputs", []))
    )
    structs_with_offsets = sum(
        1 for s in includes_output["structs"].values()
        if s.get("fields") and any("offset" in field for field in s["fields"])
    )
    constants_resolved = sum(1 for v in includes_output["constants"].values() if v["value"] is not None)

    print(f"\n{'=' * 60}")
    print(f"Libraries/devices/resources: {len(merged_libraries)}")
    print(f"Total functions:             {total_funcs}")
    print(f"  With documentation:        {documented}")
    print(f"  With typed inputs:         {with_types}")
    print(f"  No-return functions:       {no_return_count}")
    print(f"Structs:                     {len(includes_output['structs'])}")
    print(f"  With computed offsets:      {structs_with_offsets}")
    print(f"Constants:                   {len(includes_output['constants'])}")
    print(f"  Resolved to values:        {constants_resolved}")

    # ========================================================================
    # 8. Write output
    # ========================================================================
    for outpath in (args.includes_parsed_outfile, args.other_parsed_outfile):
        outdir = os.path.dirname(outpath)
        if outdir and not os.path.isdir(outdir):
            os.makedirs(outdir, exist_ok=True)

    with open(args.includes_parsed_outfile, "w", encoding="utf-8") as f:
        json.dump(canonicalize_json(includes_output), f, indent=2, ensure_ascii=False)
    with open(args.other_parsed_outfile, "w", encoding="utf-8") as f:
        json.dump(canonicalize_json(other_output), f, indent=2, ensure_ascii=False)

    print(f"\nWrote {args.includes_parsed_outfile} ({os.path.getsize(args.includes_parsed_outfile):,} bytes)")
    print(f"Wrote {args.other_parsed_outfile} ({os.path.getsize(args.other_parsed_outfile):,} bytes)")
    for runtime_out in build_runtime_artifacts():
        print(f"Wrote {runtime_out}")


if __name__ == "__main__":
    main()
