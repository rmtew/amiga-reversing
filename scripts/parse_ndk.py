#!/usr/bin/env py.exe
"""Parse Amiga NDK 1.3 to extract OS library/device function references.

Parses:
- FD files: function names, register args, LVO offsets
- Autodocs: full function documentation (synopsis, description, inputs, results)
- Include files: struct definitions, constants, flag values

Outputs structured JSON for the knowledge base.
"""

import os
import re
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

NDK_ROOT = None  # Set from command line


# =============================================================================
# FD file parser
# =============================================================================

def parse_fd_file(path: str) -> dict:
    """Parse a .FD file to extract function definitions with LVO offsets.

    FD format:
        ##base _SysBase
        ##bias 30
        ##private
        FuncName(arg1,arg2)(D0/D1)
        ##public
        FuncName2(arg1)(A0)
    """
    functions = []
    base_name = ""
    bias = 0
    public = True
    since_version = None  # tracks "Added for release X.Y" markers

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
                # Also match "1.2 new semaphore support" style
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

            # Parse function: Name(args)(regs)
            m = re.match(r"(\w+)\(([^)]*)\)\(([^)]*)\)", line)
            if m:
                name = m.group(1)
                args = [a.strip() for a in m.group(2).split(",") if a.strip()]
                regs = [r.strip() for r in m.group(3).replace("/", ",").split(",") if r.strip()]
                entry = {
                    "name": name,
                    "lvo": -bias,
                    "bias": bias,
                    "args": args,
                    "regs": regs,
                    "public": public,
                }
                if since_version:
                    entry["since"] = since_version
                functions.append(entry)
                bias += 6
                continue

            # Function with no args: Name()()
            m = re.match(r"(\w+)\(\)\(\)", line)
            if m:
                entry = {
                    "name": m.group(1),
                    "lvo": -bias,
                    "bias": bias,
                    "args": [],
                    "regs": [],
                    "public": public,
                }
                if since_version:
                    entry["since"] = since_version
                functions.append(entry)
                bias += 6
                continue

    return {"base": base_name, "functions": functions}


# =============================================================================
# Autodoc parser
# =============================================================================

def parse_autodoc(path: str) -> dict:
    """Parse an autodoc file to extract function documentation.

    Format: each function starts with 'library/FuncName' at column 0,
    followed by sections: NAME, SYNOPSIS, FUNCTION, INPUTS, RESULTS, BUGS, SEE ALSO
    """
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    entries = {}

    # Entries are separated by form feed characters (0x0C)
    parts = content.split('\x0c')

    for part in parts:
        # Get function name from header
        part = part.strip()
        # Try double-name format first: "exec.library/AllocMem\t\t\texec.library/AllocMem"
        header_m = re.match(r'(\w+\.\w+/)(\w+)\s+\1\2', part)
        if not header_m:
            # Try single-name format: "dos.library/Close"
            header_m = re.match(r'(\w+\.\w+/)(\w+)\s*$', part, re.MULTILINE)
        if not header_m:
            continue

        func_name = header_m.group(2)
        doc = {"name": func_name}

        # Extract sections - headers are like "   NAME" or "    NAME" (3-4 spaces)
        sections = re.split(r'\n\s{2,4}([A-Z][A-Z ]+)\n', part)
        # sections[0] = header, then alternating: section_name, section_content
        for i in range(1, len(sections) - 1, 2):
            section_name = sections[i].strip()
            section_body = sections[i + 1].rstrip()
            # Clean up indentation
            lines = section_body.split("\n")
            cleaned = []
            for line in lines:
                # Remove leading tab
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
                doc["inputs"] = body
            elif section_name in ("RESULTS", "RESULT"):
                doc["results"] = body
            elif section_name == "NOTE" or section_name == "NOTES":
                doc["notes"] = body
            elif section_name == "BUGS":
                doc["bugs"] = body
            elif section_name == "SEE ALSO":
                doc["see_also"] = body
            elif section_name == "WARNING":
                doc["warning"] = body

        entries[func_name] = doc

    return entries


# =============================================================================
# Synopsis parser — extract structured inputs/outputs from autodoc synopsis
# =============================================================================

def parse_synopsis(synopsis: str, arg_names: list, arg_regs: list) -> dict:
    """Parse autodoc SYNOPSIS text into structured input/output data.

    Synopsis format (most common):
        Line 1: returnName = FuncName(arg1, arg2)    [or just FuncName(args)]
        Line 2: D0                    D0    D1       [register assignments]
        Line 3+: C prototype with types

    Returns dict with keys: inputs (list), output (dict or None).
    """
    result = {"inputs": [], "output": None}
    if not synopsis:
        return result

    lines = synopsis.strip().split('\n')
    if not lines:
        return result

    # --- Parse line 1: return name ---
    line1 = lines[0].strip()
    ret_match = re.match(r'(\w+)\s*=\s*\w+\s*\(', line1)
    ret_name = ret_match.group(1) if ret_match else None

    # --- Parse line 2: register assignments (includes return reg and possibly A6) ---
    ret_reg = None
    if len(lines) >= 2:
        reg_line = lines[1]
        # Extract all register tokens with their column positions
        reg_tokens = [(m.start(), m.group().upper()) for m in re.finditer(r'[DdAa]\d', reg_line)]
        # First token on line 2 is typically the return register (aligned under returnName)
        if ret_name and reg_tokens:
            ret_reg = reg_tokens[0][1]

    # --- Parse C prototype for types ---
    # Look for lines like: void *AllocMem(ULONG, ULONG);
    # or: struct FileHandle *file;  char *name;  LONG accessMode;
    c_proto = None
    c_type_decls = []
    for line in lines:
        line_s = line.strip()
        # Full C prototype: RetType *FuncName(ArgType1, ArgType2);
        proto_m = re.match(r'(.+?)\s+\*?\s*\w+\s*\((.+)\)\s*;', line_s)
        if proto_m:
            c_proto = line_s
            continue
        # Individual type declaration: ULONG byteSize; or struct Task *task;
        # Match: "ULONG foo;", "char *name;", "struct Task *task;", "void *ptr;"
        decl_m = re.match(r'((?:struct\s+|unsigned\s+)?\w+)\s*(\*?)\s*(\w+)\s*;', line_s)
        if decl_m:
            typ = decl_m.group(1).strip()
            ptr = decl_m.group(2)
            name = decl_m.group(3)
            if ptr:
                typ += " *"
            c_type_decls.append((name, typ))

    # Build type map from declarations
    type_map = {name: typ for name, typ in c_type_decls}

    # Extract arg types from C prototype
    # Formats: "void *AllocMem(ULONG, ULONG);" or "struct Library *OpenLibrary(char *,ULONG);"
    arg_types_from_proto = []
    if c_proto:
        # Split at the function name + open paren
        proto_m = re.match(r'(.+?)\b(\w+)\s*\((.+)\)\s*;', c_proto)
        if proto_m:
            ret_type_str = proto_m.group(1).strip()
            # Clean up: "void *" stays, "struct Library *" stays
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
        # No C prototype, but we have return name/reg
        ret_type = type_map.get(ret_name)
        result["output"] = {"name": ret_name, "reg": ret_reg}
        if ret_type:
            result["output"]["type"] = ret_type

    # --- Build structured inputs ---
    for i, (aname, areg) in enumerate(zip(arg_names, arg_regs)):
        inp = {"name": aname, "reg": areg.upper()}
        # Try to get type from C prototype args
        if i < len(arg_types_from_proto):
            inp["type"] = arg_types_from_proto[i]
        # Or from individual declarations
        elif aname in type_map:
            inp["type"] = type_map[aname]
        result["inputs"].append(inp)

    return result


# =============================================================================
# Include file parser (structs and constants)
# =============================================================================

def parse_asm_include(path: str) -> dict:
    """Parse .I (asm) include file for struct definitions and constants."""
    structs = {}
    constants = {}
    current_struct = None
    current_fields = []

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()

            # STRUCTURE definition start
            m = re.match(r'\s+STRUCTURE\s+(\w+),(\d+)', line)
            if m:
                if current_struct:
                    structs[current_struct] = current_fields
                current_struct = m.group(1)
                current_fields = []
                continue

            # Struct field: UBYTE, UWORD, ULONG, APTR, BPTR, STRUCT, LABEL
            if current_struct:
                fm = re.match(
                    r'\s+(UBYTE|BYTE|UWORD|WORD|ULONG|LONG|APTR|BPTR|STRUCT|LABEL)\s+(\w+)',
                    line
                )
                if fm:
                    current_fields.append({
                        "type": fm.group(1),
                        "name": fm.group(2),
                    })
                    continue
                # End of struct (next STRUCTURE or blank/comment section)
                if line.strip() and not line.startswith("*") and not line.startswith(";"):
                    if not re.match(r'\s+(DS|ALIGNWORD|ALIGNLONG)', line):
                        if current_struct and current_fields:
                            structs[current_struct] = current_fields
                        current_struct = None
                        current_fields = []

            # EQU constants
            cm = re.match(r'^(\w+)\s+EQU\s+(.+?)(?:\s*;.*)?$', line)
            if cm:
                name = cm.group(1)
                value = cm.group(2).strip()
                constants[name] = value
                continue

            # SET constants
            cm = re.match(r'^(\w+)\s+SET\s+(.+?)(?:\s*;.*)?$', line)
            if cm:
                name = cm.group(1)
                value = cm.group(2).strip()
                # Skip include guards
                if not name.endswith("_I"):
                    constants[name] = value

    if current_struct and current_fields:
        structs[current_struct] = current_fields

    return {"structs": structs, "constants": constants}


def parse_c_include(path: str) -> dict:
    """Parse .H (C) include file for struct definitions and constants."""
    structs = {}
    constants = {}

    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    # #define constants
    for m in re.finditer(r'#define\s+(\w+)\s+(.+?)(?:\s*/\*.*)?$', content, re.MULTILINE):
        name = m.group(1)
        value = m.group(2).strip()
        if not name.startswith("_") and not name.endswith("_H"):
            constants[name] = value

    # Simple struct extraction
    for m in re.finditer(
        r'struct\s+(\w+)\s*\{([^}]+)\}', content, re.DOTALL
    ):
        struct_name = m.group(1)
        body = m.group(2)
        fields = []
        for fm in re.finditer(r'(\w[\w\s*]+?)\s+(\w+)(?:\[(\w+)\])?\s*;', body):
            ftype = fm.group(1).strip()
            fname = fm.group(2)
            farray = fm.group(3)
            entry = {"type": ftype, "name": fname}
            if farray:
                entry["array"] = farray
            fields.append(entry)
        if fields:
            structs[struct_name] = fields

    return {"structs": structs, "constants": constants}


# =============================================================================
# LVO offset parser
# =============================================================================

def parse_lvo_offs(path: str) -> dict:
    """Parse LVO.OFFS for complete offset table across all libraries."""
    libraries = {}
    current_lib = None
    since_version = None

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()

            # Library header: "*** library.name ***"
            m = re.match(r'\*+\s+(\S+)\s+\*+', line)
            if m:
                current_lib = m.group(1)
                libraries[current_lib] = []
                since_version = None
                continue

            # Version markers: "*--- Added as of version 34 ..."
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

            if line.startswith("##"):
                continue

            if current_lib and line.strip():
                # Format: "  30 $ffe2 -$001e FuncName(args)(regs)"
                m = re.match(
                    r'\s*(\d+)\s+\$[0-9a-f]+\s+-\$([0-9a-f]+)\s+(\w+)\(([^)]*)\)\(([^)]*)\)',
                    line
                )
                if m:
                    bias = int(m.group(1))
                    name = m.group(3)
                    args = [a.strip() for a in m.group(4).split(",") if a.strip()]
                    regs = [r.strip() for r in m.group(5).replace("/", ",").split(",") if r.strip()]
                    entry = {
                        "name": name,
                        "lvo": -bias,
                        "bias": bias,
                        "args": args,
                        "regs": regs,
                    }
                    if since_version:
                        entry["since"] = since_version
                    libraries[current_lib].append(entry)

    return libraries


# =============================================================================
# Main: combine all sources
# =============================================================================

def find_ndk_paths(ndk_root: str) -> dict:
    """Auto-detect NDK directory structure (works with 1.3 and 3.1 layouts)."""
    paths = {}

    # FD files
    for candidate in [
        os.path.join(ndk_root, "INCLUDES&LIBS", "FD"),       # NDK 3.1
        os.path.join(ndk_root, "INCLUDE-STRIP1.3", "FD1.3"), # NDK 1.3
    ]:
        if os.path.isdir(candidate):
            paths["fd_dir"] = candidate
            break

    # Autodocs
    autodoc_dirs = []
    for candidate in [
        os.path.join(ndk_root, "DOCS", "DOC"),                  # NDK 3.1 (single dir)
        os.path.join(ndk_root, "AUTODOCS1.3", "LIBRARIESA-K"),  # NDK 1.3
    ]:
        if os.path.isdir(candidate):
            if "DOC" in os.path.basename(candidate):
                autodoc_dirs = [candidate]  # 3.1: single flat dir
            else:
                # 1.3: multiple subdirs
                base = os.path.dirname(candidate)
                for sub in ["LIBRARIESA-K", "LIBRARIESL-Z", "DEVICESA-K",
                            "DEVICESL-Z", "RESOURCES"]:
                    d = os.path.join(base, sub)
                    if os.path.isdir(d):
                        autodoc_dirs.append(d)
            break
    paths["autodoc_dirs"] = autodoc_dirs

    # Include files (asm)
    for candidate in [
        os.path.join(ndk_root, "INCLUDES&LIBS", "INCLUDE_I"),  # NDK 3.1
        os.path.join(ndk_root, "INCLUDES1.3", "INCLUDE.I"),    # NDK 1.3
    ]:
        if os.path.isdir(candidate):
            paths["include_asm_dir"] = candidate
            break

    # LVO.OFFS (1.3 only — 3.1 uses FD files as source of truth)
    lvo_path = os.path.join(ndk_root, "INCLUDE-STRIP1.3", "OFFS1.3", "LVO.OFFS")
    if os.path.exists(lvo_path):
        paths["lvo_path"] = lvo_path

    return paths


def main():
    global NDK_ROOT

    import argparse
    parser = argparse.ArgumentParser(description="Parse Amiga NDK into structured JSON")
    parser.add_argument("ndk_root", nargs="?",
                        default=r"C:\Users\richa\Downloads\Emulation\amiga-misc\NDK_1.3",
                        help="Path to NDK root directory")
    parser.add_argument("--outfile", default="knowledge/amiga_os_reference.json")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--ndk-version", help="Override NDK version label (e.g. 3.1)")
    args = parser.parse_args()

    NDK_ROOT = args.ndk_root
    ndk_paths = find_ndk_paths(NDK_ROOT)

    # Detect NDK version from path
    ndk_version = args.ndk_version
    if not ndk_version:
        for v in ["3.5", "3.1", "3.0", "2.0", "1.3"]:
            if v.replace(".", "") in NDK_ROOT or f"_{v}" in NDK_ROOT:
                ndk_version = v
                break
        if not ndk_version:
            ndk_version = "unknown"

    # Version mapping
    version_info = {
        "1.3": {"kickstart": 34, "os": "1.3"},
        "2.0": {"kickstart": 36, "os": "2.0"},
        "3.0": {"kickstart": 39, "os": "3.0"},
        "3.1": {"kickstart": 40, "os": "3.1"},
        "3.5": {"kickstart": 44, "os": "3.5"},
    }.get(ndk_version, {"kickstart": None, "os": ndk_version})

    print(f"NDK {ndk_version} at {NDK_ROOT}")
    for k, v in ndk_paths.items():
        if isinstance(v, list):
            print(f"  {k}: {len(v)} dirs")
        else:
            print(f"  {k}: {v}")

    fd_dir = ndk_paths.get("fd_dir")
    autodoc_dirs = ndk_paths.get("autodoc_dirs", [])
    include_asm_dir = ndk_paths.get("include_asm_dir")
    lvo_path = ndk_paths.get("lvo_path")

    # ---- Parse LVO offsets (if available — NDK 1.3 only) ----
    lvo_data = {}
    if lvo_path:
        print("Parsing LVO offsets...")
        lvo_data = parse_lvo_offs(lvo_path)
        total_funcs = sum(len(v) for v in lvo_data.values())
        print(f"  {len(lvo_data)} libraries/devices/resources, {total_funcs} functions")

    # ---- Parse FD files (primary source for NDK 3.1+) ----
    print("Parsing FD files...")
    fd_data = {}
    if fd_dir:
        # Map FD filenames to library names
        # EXEC_LIB.FD -> exec, WB_LIB.FD -> wb, CARDRES_LIB.FD -> cardres
        fd_name_map = {
            "wb": "workbench",      # WB_LIB.FD -> workbench.library
            "cardres": "card",      # CARDRES_LIB.FD -> card.resource (runtime name)
        }
        for fname in sorted(os.listdir(fd_dir)):
            if fname.endswith(".FD"):
                result = parse_fd_file(os.path.join(fd_dir, fname))
                raw_name = fname.replace("_LIB.FD", "").lower()
                lib_name = fd_name_map.get(raw_name, raw_name)
                fd_data[lib_name] = result
    print(f"  {len(fd_data)} FD files")

    # If no LVO.OFFS, build lvo_data from FD files
    if not lvo_data and fd_data:
        print("Building LVO data from FD files...")
        for fd_name, fd_info in fd_data.items():
            # Determine full library name
            base = fd_info["base"]
            # Guess library type from base name or FD content
            if "resource" in fd_name or fd_name in ("cia", "battclock", "battmem",
                                                     "card", "misc", "potgo",
                                                     "disk"):
                suffix = ".resource"
            elif fd_name in ("console", "input", "timer", "ramdrive"):
                suffix = ".device"
            elif fd_name in ("colorwheel", "gradientslider"):
                suffix = ".gadget"
            else:
                suffix = ".library"
            lib_key = fd_name + suffix

            lvo_data[lib_key] = [
                {
                    "name": f["name"],
                    "lvo": f["lvo"],
                    "bias": f["bias"],
                    "args": f["args"],
                    "regs": f["regs"],
                }
                for f in fd_info["functions"]
            ]
        total_funcs = sum(len(v) for v in lvo_data.values())
        print(f"  {len(lvo_data)} libraries, {total_funcs} functions")

    # ---- Parse Autodocs ----
    print("Parsing autodocs...")
    autodoc_data = {}
    for doc_dir in autodoc_dirs:
        if not os.path.isdir(doc_dir):
            continue
        for fname in sorted(os.listdir(doc_dir)):
            if fname.endswith(".DOC"):
                entries = parse_autodoc(os.path.join(doc_dir, fname))
                lib_name = fname.replace(".DOC", "").lower()
                autodoc_data[lib_name] = entries
                print(f"  {lib_name}: {len(entries)} functions documented")

    # ---- Parse key include files ----
    print("Parsing include files...")
    includes = {}

    # Key include subdirectories to parse
    key_includes_asm = {
        "exec": ["EXEC.I", "EXECBASE.I", "MEMORY.I", "IO.I", "TASKS.I",
                  "INTERRUPTS.I", "LIBRARIES.I", "PORTS.I", "NODES.I",
                  "LISTS.I", "DEVICES.I", "RESIDENT.I", "ALERTS.I", "ERRORS.I"],
        "hardware": ["CUSTOM.I", "DMABITS.I", "INTBITS.I", "ADKBITS.I",
                      "BLIT.I", "CIA.I"],
        "graphics": [],  # will glob
        "intuition": [],
        "devices": [],
        "libraries": [],
    }

    for subdir in ["EXEC", "HARDWARE", "GRAPHICS", "INTUITION", "DEVICES", "LIBRARIES", "RESOURCES"]:
        asm_path = os.path.join(include_asm_dir, subdir)
        if not os.path.isdir(asm_path):
            continue
        for fname in sorted(os.listdir(asm_path)):
            if fname.endswith(".I"):
                result = parse_asm_include(os.path.join(asm_path, fname))
                key = f"{subdir.lower()}/{fname}"
                if result["structs"] or result["constants"]:
                    includes[key] = result

    print(f"  {len(includes)} include files with structs/constants")

    # Count totals
    total_structs = sum(len(v.get("structs", {})) for v in includes.values())
    total_constants = sum(len(v.get("constants", {})) for v in includes.values())
    print(f"  {total_structs} structs, {total_constants} constants")

    # ---- Build combined output ----
    output = {
        "meta": {
            "source": f"Amiga NDK {ndk_version} (Native Developer Kit)",
            "ndk_version": ndk_version,
            "kickstart_version": version_info["kickstart"],
            "os_version": version_info["os"],
            "description": "AmigaOS library/device function references with LVO offsets, register args, and documentation",
            "version_notes": "Kickstart version mapping: V30=1.0, V33=1.2, V34=1.3, V36=2.0, V37=2.04, V39=3.0, V40=3.1, V44=3.5",
        },
        "libraries": {},
    }

    # Merge LVO data with FD and autodoc data
    for lib_key, funcs in lvo_data.items():
        # Normalize library name for matching
        lib_lower = lib_key.lower().replace(".", "").replace(" ", "")

        # Find matching autodoc
        autodoc_name = None
        for ad_name in autodoc_data:
            if ad_name.replace(".", "").replace(" ", "") == lib_lower or ad_name in lib_lower:
                autodoc_name = ad_name
                break

        # Find matching FD
        fd_name = None
        for fd_key in fd_data:
            if fd_key in lib_lower or lib_lower.startswith(fd_key):
                fd_name = fd_key
                break

        base_name = fd_data[fd_name]["base"] if fd_name else ""

        # All Amiga library/device/resource calls use A6 as base register
        lib_entry = {
            "name": lib_key,
            "base": base_name,
            "base_reg": "A6",
            "functions": [],
        }

        for func in funcs:
            entry = {
                "name": func["name"],
                "lvo": func["lvo"],
            }

            # Add autodoc info if available
            if autodoc_name and func["name"] in autodoc_data[autodoc_name]:
                doc = autodoc_data[autodoc_name][func["name"]]

                # Parse synopsis into structured inputs/outputs
                if "synopsis" in doc:
                    parsed = parse_synopsis(
                        doc["synopsis"], func["args"], func["regs"]
                    )
                    if parsed["inputs"]:
                        entry["inputs"] = parsed["inputs"]
                    if parsed["output"]:
                        entry["output"] = parsed["output"]

                if "description" in doc:
                    desc = doc["description"]
                    if len(desc) > 500:
                        desc = desc[:500] + "..."
                    entry["description"] = desc
                if "notes" in doc:
                    entry["notes"] = doc["notes"]

            # If no autodoc parsed inputs, build from FD args/regs
            if "inputs" not in entry and func["args"]:
                entry["inputs"] = [
                    {"name": a, "reg": r.upper()}
                    for a, r in zip(func["args"], func["regs"])
                ]

            # Add private flag and since version from FD
            if fd_name:
                for fd_func in fd_data[fd_name]["functions"]:
                    if fd_func["name"] == func["name"]:
                        if not fd_func["public"]:
                            entry["private"] = True
                        if "since" in fd_func and "since" not in entry:
                            entry["since"] = fd_func["since"]
                        break

            # Also check LVO data for since version
            if "since" in func and "since" not in entry:
                entry["since"] = func["since"]

            # Normalize version numbers: V30=1.0, V33=1.2, V34=1.3
            version_map = {"30": "1.0", "33": "1.2", "34": "1.3",
                           "36": "2.0", "37": "2.04", "39": "3.0", "40": "3.1"}
            if "since" in entry:
                entry["since"] = version_map.get(entry["since"], entry["since"])

            lib_entry["functions"].append(entry)

        output["libraries"][lib_key] = lib_entry

    # ---- Add key structs and constants ----
    output["structs"] = {}
    output["constants"] = {}

    for inc_key, inc_data in includes.items():
        for sname, sfields in inc_data.get("structs", {}).items():
            output["structs"][sname] = {
                "source": inc_key,
                "fields": sfields,
            }
        for cname, cvalue in inc_data.get("constants", {}).items():
            output["constants"][cname] = cvalue

    # ---- Summary ----
    total_lib_funcs = sum(len(v["functions"]) for v in output["libraries"].values())
    documented = sum(
        1 for lib in output["libraries"].values()
        for f in lib["functions"]
        if "description" in f
    )
    print(f"\n{'='*50}")
    print(f"Libraries/devices/resources: {len(output['libraries'])}")
    print(f"Total functions: {total_lib_funcs}")
    print(f"With documentation: {documented}")
    print(f"Structs: {len(output['structs'])}")
    print(f"Constants: {len(output['constants'])}")

    # ---- Write output ----
    if args.summary:
        for lib_name, lib_data in sorted(output["libraries"].items()):
            n = len(lib_data["functions"])
            doc = sum(1 for f in lib_data["functions"] if "description" in f)
            print(f"  {lib_name}: {n} functions ({doc} documented)")
        return

    with open(args.outfile, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Wrote {args.outfile}")


if __name__ == "__main__":
    main()
