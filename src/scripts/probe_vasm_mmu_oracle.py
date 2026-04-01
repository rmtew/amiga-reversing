from __future__ import annotations

import ctypes
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VASM = ROOT / "ext" / "vasm" / "vasmm68k_mot.exe"
ASM_DLL = ROOT / "src" / "build" / "m68k_assembler_lib.dll"
DISASM_DLL = ROOT / "src" / "build" / "m68k_disassembler_lib.dll"

CPU_CODES = {
    "68000": 0,
    "68010": 1,
    "68020": 2,
    "68030": 3,
    "68040": 4,
    "68060": 5,
}

REMAINING_MNEMONICS = {
    "PBcc",
    "PDBcc",
    "PFLUSH",
    "PFLUSH PFLUSHA",
    "PFLUSHR",
    "PLOAD",
    "PMOVE",
    "PRESTORE",
    "PSAVE",
    "PScc",
    "PTEST",
    "PTRAPcc",
    "PVALID",
    "cpBcc",
    "cpDBcc",
    "cpGEN",
    "cpRESTORE",
    "cpSAVE",
    "cpScc",
    "cpTRAPcc",
    "FRESTORE",
    "FSAVE",
}

PROBE_CASES = (
    {"mnemonic": "FSAVE", "cpu": "68040", "asm": "fsave (a0)"},
    {"mnemonic": "FRESTORE", "cpu": "68040", "asm": "frestore (a0)"},
    {"mnemonic": "PRESTORE", "cpu": "68020", "vasm_cpu": "68851", "asm": "prestore (a0)"},
    {"mnemonic": "PSAVE", "cpu": "68020", "vasm_cpu": "68851", "asm": "psave (a0)"},
    {"mnemonic": "PFLUSH PFLUSHA", "cpu": "68030", "asm": "pflusha"},
    {"mnemonic": "PFLUSH PFLUSHA", "cpu": "68040", "asm": "pflusha"},
    {"mnemonic": "PFLUSH", "cpu": "68030", "asm": "pflush sfc,#0"},
    {"mnemonic": "PFLUSH", "cpu": "68030", "asm": "pflush sfc,#0,(a0)"},
    {"mnemonic": "PFLUSH", "cpu": "68040", "asm": "pflush (a0)"},
    {"mnemonic": "PFLUSHR", "cpu": "68020", "vasm_cpu": "68851", "asm": "pflushr (a0)"},
    {"mnemonic": "PLOAD", "cpu": "68030", "asm": "ploadr sfc,(a0)"},
    {"mnemonic": "PLOAD", "cpu": "68030", "asm": "ploadw sfc,(a0)"},
    {"mnemonic": "PTEST", "cpu": "68030", "asm": "ptestw sfc,(a0),#0"},
    {"mnemonic": "PTEST", "cpu": "68030", "asm": "ptestr sfc,(a0),#0"},
    {"mnemonic": "PTEST", "cpu": "68030", "asm": "ptestw sfc,(a0),#0,a0"},
    {"mnemonic": "PTEST", "cpu": "68030", "asm": "ptestr sfc,(a0),#0,a0"},
    {"mnemonic": "PTEST", "cpu": "68040", "asm": "ptestw (a0)"},
    {"mnemonic": "PTEST", "cpu": "68040", "asm": "ptestr (a0)"},
    {"mnemonic": "PMOVE", "cpu": "68030", "asm": "pmove tc,(a0)"},
    {"mnemonic": "PMOVE", "cpu": "68030", "asm": "pmove (a0),tc"},
    {"mnemonic": "PMOVE", "cpu": "68030", "asm": "pmove psr,(a0)"},
    {"mnemonic": "PMOVE", "cpu": "68030", "asm": "pmove (a0),psr"},
    {"mnemonic": "PMOVE", "cpu": "68030", "asm": "pmove tt0,(a0)"},
    {"mnemonic": "PMOVE", "cpu": "68030", "asm": "pmove (a0),tt0"},
    {
        "mnemonic": "PBcc",
        "cpu": "68030",
        "vasm_cpu": "68851",
        "asm": "pbcc.w label\nlabel:",
        "expected_disassembly": "pbcc.w target",
        "reassembly_suffix": "target:",
    },
    {
        "mnemonic": "PDBcc",
        "cpu": "68030",
        "vasm_cpu": "68851",
        "asm": "pdbcc d0,label\nlabel:",
        "expected_disassembly": "pdbcc d0,target",
        "reassembly_suffix": "target:",
    },
    {"mnemonic": "PScc", "cpu": "68030", "vasm_cpu": "68851", "asm": "pscc (a0)"},
    {"mnemonic": "PTRAPcc", "cpu": "68030", "vasm_cpu": "68851", "asm": "ptrapcc"},
    {"mnemonic": "PTRAPcc", "cpu": "68030", "vasm_cpu": "68851", "asm": "ptrapcc #1", "expected_disassembly": "ptrapcc.w #1"},
    {"mnemonic": "PVALID", "cpu": "68030", "vasm_cpu": "68851", "asm": "pvalid val,(a0)"},
    {"mnemonic": "PVALID", "cpu": "68030", "vasm_cpu": "68851", "asm": "pvalid a0,(a1)"},
)


def _require_paths() -> None:
    missing = [path for path in (VASM, ASM_DLL, DISASM_DLL) if not path.exists()]
    if missing:
        raise SystemExit("Missing required paths:\n" + "\n".join(str(path) for path in missing))


def _assembler_lib():
    lib = ctypes.CDLL(str(ASM_DLL))

    class M68kAsmOptions(ctypes.Structure):
        _fields_ = [("target_cpu", ctypes.c_uint8), ("input_mode", ctypes.c_uint8)]

    lib._m68k_asm_options_type = M68kAsmOptions
    lib.m68k_assemble.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(M68kAsmOptions),
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_char_p,
        ctypes.c_size_t,
    ]
    lib.m68k_assemble.restype = ctypes.c_int
    return lib


def _disassembler_lib():
    lib = ctypes.CDLL(str(DISASM_DLL))
    lib.m68k_disassemble_one_text_for_cpu.argtypes = [
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
        ctypes.c_uint8,
        ctypes.c_char_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_char_p,
        ctypes.c_size_t,
    ]
    lib.m68k_disassemble_one_text_for_cpu.restype = ctypes.c_int
    return lib


def _probe_vasm(cpu_name: str, asm_text: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as temp_dir:
        src_path = Path(temp_dir) / "probe.s"
        out_path = Path(temp_dir) / "probe.bin"
        src_path.write_text("\t" + asm_text.replace("\n", "\n\t") + "\n", encoding="ascii")
        result = subprocess.run(
            [str(VASM), f"-m{cpu_name}", "-Fbin", "-o", str(out_path), str(src_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout).strip().splitlines()
            error_text = message[0] if message else "vasm failed"
            if "\":" in error_text:
                error_text = error_text.split("\":", 1)[1].strip()
            return {"accepted": False, "error": error_text}
        return {"accepted": True, "bytes_hex": out_path.read_bytes().hex()}


def _probe_ours_assemble(lib, cpu_name: str, asm_text: str) -> dict[str, object]:
    options = lib._m68k_asm_options_type(CPU_CODES[cpu_name], 1 if "\n" in asm_text else 0)
    out_buf = (ctypes.c_ubyte * 256)()
    error_buf = ctypes.create_string_buffer(256)
    byte_count = ctypes.c_size_t()
    result = lib.m68k_assemble(
        asm_text.encode("ascii"),
        ctypes.byref(options),
        out_buf,
        len(out_buf),
        ctypes.byref(byte_count),
        error_buf,
        len(error_buf),
    )
    if result != 0:
        return {"accepted": False, "error": error_buf.value.decode("utf-8")}
    return {"accepted": True, "bytes_hex": bytes(out_buf[:byte_count.value]).hex()}


def _probe_ours_disassemble(lib, cpu_name: str, bytes_hex: str) -> dict[str, object]:
    data = bytes.fromhex(bytes_hex)
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    text_buf = ctypes.create_string_buffer(256)
    error_buf = ctypes.create_string_buffer(256)
    byte_count = ctypes.c_size_t()
    result = lib.m68k_disassemble_one_text_for_cpu(
        buffer,
        len(data),
        CPU_CODES[cpu_name],
        text_buf,
        len(text_buf),
        ctypes.byref(byte_count),
        error_buf,
        len(error_buf),
    )
    if result != 0:
        return {"accepted": False, "error": error_buf.value.decode("utf-8")}
    return {"accepted": True, "text": text_buf.value.decode("utf-8"), "byte_count": int(byte_count.value)}


def _probe_ours_reassemble_disassembly(
    lib,
    cpu_name: str,
    rendered_text: str,
    original_asm_text: str,
    reassembly_suffix: str | None,
) -> dict[str, object]:
    if "\n" not in original_asm_text and not reassembly_suffix:
        return _probe_ours_assemble(lib, cpu_name, rendered_text)
    lines = original_asm_text.splitlines()
    rebuilt_source = rendered_text + "\n"
    trailing_lines = lines[1:] if len(lines) > 1 else []
    if reassembly_suffix is not None:
        rebuilt_source += reassembly_suffix + "\n"
        trailing_lines = [line for line in trailing_lines if line != reassembly_suffix]
    if trailing_lines:
        rebuilt_source += "\n".join(trailing_lines) + "\n"
    return _probe_ours_assemble(lib, cpu_name, rebuilt_source)


def build_matrix() -> dict[str, object]:
    _require_paths()
    asm_lib = _assembler_lib()
    disasm_lib = _disassembler_lib()
    cases: list[dict[str, object]] = []
    probed = {case["mnemonic"] for case in PROBE_CASES}

    for case in PROBE_CASES:
        entry = dict(case)
        entry["vasm"] = _probe_vasm(str(case.get("vasm_cpu", case["cpu"])), str(case["asm"]))
        entry["ours_assemble"] = _probe_ours_assemble(asm_lib, str(case["cpu"]), str(case["asm"]))
        if entry["vasm"]["accepted"]:
            entry["ours_disassemble"] = _probe_ours_disassemble(disasm_lib, str(case["cpu"]), str(entry["vasm"]["bytes_hex"]))
            if entry["ours_disassemble"]["accepted"]:
                entry["ours_reassemble_disassembly"] = _probe_ours_reassemble_disassembly(
                    asm_lib,
                    str(case["cpu"]),
                    str(entry["ours_disassemble"]["text"]),
                    str(case["asm"]),
                    case.get("reassembly_suffix"),
                )
            entry["ours_matches_oracle"] = (
                entry["ours_assemble"]["accepted"]
                and entry["ours_assemble"]["bytes_hex"] == entry["vasm"]["bytes_hex"]
                and entry["ours_disassemble"]["accepted"]
                and entry["ours_reassemble_disassembly"]["accepted"]
                and entry["ours_reassemble_disassembly"]["bytes_hex"] == entry["vasm"]["bytes_hex"]
            )
        cases.append(entry)

    accepted = [case for case in cases if case["vasm"]["accepted"]]
    covered = sorted({str(case["mnemonic"]) for case in accepted})
    return {
        "matrix_version": 2,
        "remaining_mnemonics": sorted(REMAINING_MNEMONICS),
        "probed_mnemonics": sorted(probed),
        "oracle_backed_mnemonics": covered,
        "unprobed_mnemonics": sorted(REMAINING_MNEMONICS - probed),
        "accepted_case_count": len(accepted),
        "accepted_by_ours_count": sum(1 for case in accepted if case.get("ours_matches_oracle")),
        "cases": cases,
    }


def main() -> None:
    output_path = ROOT / "src" / "tests" / "generated" / "vasm_mmu_oracle_matrix.json"
    output_path.write_text(json.dumps(build_matrix(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
