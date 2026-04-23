from __future__ import annotations

import ctypes
import gzip
import json
import struct
import subprocess
import textwrap
import zipfile
from functools import lru_cache
from pathlib import Path

from src.tests._build_helpers import require_built_tools

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "src"
BUILD_DIR = SRC_DIR / "build"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "hunk"
FILE_MANIFEST = ROOT / "corpus" / "platform_file_manifest.jsonl"
FILE_DLL = BUILD_DIR / "platform_file_lib.dll"
HARNESS_EXE = BUILD_DIR / "platform_backend_harness.exe"
HARNESS_SOURCE = BUILD_DIR / "platform_backend_harness.c"
HARNESS_COMPILE = BUILD_DIR / "platform_backend_harness_compile.bat"
M68K_DIAG_SEVERITY_ERROR = 3
M68K_DIAG_MESSAGE_SIZE = 160
M68K_DIAG_LIST_CAPACITY = 8


class M68kDiag(ctypes.Structure):
    _fields_ = [
        ("severity", ctypes.c_uint32),
        ("code", ctypes.c_uint32),
        ("message", ctypes.c_char * M68K_DIAG_MESSAGE_SIZE),
    ]


class M68kDiagList(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_size_t),
        ("dropped_count", ctypes.c_size_t),
        ("items", M68kDiag * M68K_DIAG_LIST_CAPACITY),
    ]


class PlatformFileTextResult(ctypes.Structure):
    _fields_ = [
        ("text", ctypes.c_void_p),
        ("diagnostics", M68kDiagList),
    ]


class PlatformFileBufferResult(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.c_void_p),
        ("size", ctypes.c_size_t),
        ("diagnostics", M68kDiagList),
    ]


def _diag_message(diagnostics: M68kDiagList) -> str:
    for index in range(diagnostics.count):
        if diagnostics.items[index].severity == M68K_DIAG_SEVERITY_ERROR:
            return diagnostics.items[index].message.decode("utf-8")
    if diagnostics.count:
        return diagnostics.items[0].message.decode("utf-8")
    return ""


def _diag_has_errors(diagnostics: M68kDiagList) -> bool:
    return any(
        diagnostics.items[index].severity == M68K_DIAG_SEVERITY_ERROR
        for index in range(diagnostics.count)
    )


def u32(value: int) -> bytes:
    return struct.pack(">I", value)


def u16(value: int) -> bytes:
    return struct.pack(">H", value)


def make_bstr(text: str) -> bytes:
    raw = text.encode("latin-1")
    longs = (len(raw) + 3) // 4
    return u32(longs) + raw.ljust(longs * 4, b"\x00")


def make_padded_name(text: str) -> bytes:
    raw = text.encode("latin-1")
    longs = (len(raw) + 3) // 4
    return raw.ljust(longs * 4, b"\x00")


def make_ext_entry(ext_type: int, name: str, *values: int) -> bytes:
    name_longs = (len(name.encode("latin-1")) + 3) // 4
    payload = bytearray()
    payload += u32((ext_type << 24) | name_longs)
    payload += make_padded_name(name)
    for value in values:
        payload += u32(value)
    return bytes(payload)


def make_synthetic_hunkexe(code_data: bytes = b"\x4E\x75\x00\x00", data_data: bytes = b"\x00\x00\x00\x00") -> bytes:
    hunk_header = 1011
    hunk_code = 1001
    hunk_data = 1002
    hunk_reloc32 = 1004
    hunk_symbol = 1008
    hunk_end = 1010

    payload = bytearray()
    payload += u32(hunk_header)
    payload += u32(0)
    payload += u32(2)
    payload += u32(0)
    payload += u32(1)
    payload += u32((len(code_data) + 3) // 4)
    payload += u32((len(data_data) + 3) // 4)

    payload += u32(hunk_code)
    payload += u32((len(code_data) + 3) // 4)
    payload += code_data.ljust(((len(code_data) + 3) // 4) * 4, b"\x00")
    payload += u32(hunk_symbol)
    payload += make_bstr("start")
    payload += u32(0)
    payload += u32(0)
    payload += u32(hunk_end)

    payload += u32(hunk_data)
    payload += u32((len(data_data) + 3) // 4)
    payload += data_data.ljust(((len(data_data) + 3) // 4) * 4, b"\x00")
    payload += u32(hunk_reloc32)
    payload += u32(1)
    payload += u32(0)
    payload += u32(0)
    payload += u32(0)
    payload += u32(hunk_symbol)
    payload += make_bstr("data_ref")
    payload += u32(0)
    payload += u32(0)
    payload += u32(hunk_end)
    return bytes(payload)


def make_synthetic_hunkexe_data_bss_tail_reloc() -> bytes:
    hunk_header = 1011
    hunk_code = 1001
    hunk_data = 1002
    hunk_reloc32 = 1004
    hunk_end = 1010

    code_data = b"\x4E\x75\x00\x00"
    data_data = u32(8)
    payload = bytearray()
    payload += u32(hunk_header)
    payload += u32(0)
    payload += u32(2)
    payload += u32(0)
    payload += u32(1)
    payload += u32(1)
    payload += u32(4)

    payload += u32(hunk_code)
    payload += u32(1)
    payload += code_data
    payload += u32(hunk_end)

    payload += u32(hunk_data)
    payload += u32(1)
    payload += data_data
    payload += u32(hunk_reloc32)
    payload += u32(1)
    payload += u32(1)
    payload += u32(0)
    payload += u32(0)
    payload += u32(hunk_end)
    return bytes(payload)


def make_synthetic_hunkexe_code_to_data_bss_tail_reloc() -> bytes:
    hunk_header = 1011
    hunk_code = 1001
    hunk_data = 1002
    hunk_reloc32 = 1004
    hunk_end = 1010

    code_data = bytes.fromhex("41f9000000084e75")
    data_data = u32(0)
    payload = bytearray()
    payload += u32(hunk_header)
    payload += u32(0)
    payload += u32(2)
    payload += u32(0)
    payload += u32(1)
    payload += u32(2)
    payload += u32(4)

    payload += u32(hunk_code)
    payload += u32(2)
    payload += code_data
    payload += u32(hunk_reloc32)
    payload += u32(1)
    payload += u32(1)
    payload += u32(2)
    payload += u32(0)
    payload += u32(hunk_end)

    payload += u32(hunk_data)
    payload += u32(1)
    payload += data_data
    payload += u32(hunk_end)
    return bytes(payload)


def make_synthetic_hunk_object_with_ext() -> bytes:
    hunk_unit = 999
    hunk_name = 1000
    hunk_code = 1001
    hunk_ext = 1007
    hunk_end = 1010
    ext_def = 1
    ext_ref32 = 129

    payload = bytearray()
    payload += u32(hunk_unit)
    payload += make_bstr("")
    payload += u32(hunk_name)
    payload += make_bstr("CODE")
    payload += u32(hunk_code)
    payload += u32(1)
    payload += b"\x20\x3C\x00\x00"
    payload += u32(hunk_ext)
    payload += make_ext_entry(ext_def, "export", 0)
    payload += make_ext_entry(ext_ref32, "extern", 1, 0)
    payload += u32(0)
    payload += u32(hunk_end)
    return bytes(payload)


def make_synthetic_extended_mem_hunk_object() -> bytes:
    hunk_unit = 999
    hunk_name = 1000
    hunk_code = 1001
    hunk_end = 1010

    payload = bytearray()
    payload += u32(hunk_unit)
    payload += make_bstr("")
    payload += u32(hunk_name)
    payload += make_bstr("CODE")
    payload += u32(hunk_code | (3 << 30))
    payload += u32(0x12345678)
    payload += u32(1)
    payload += b"\x4E\x75\x00\x00"
    payload += u32(hunk_end)
    return bytes(payload)


def make_synthetic_hunk_object_with_extra_relocs() -> bytes:
    hunk_unit = 999
    hunk_name = 1000
    hunk_code = 1001
    hunk_data = 1002
    hunk_reloc16 = 1005
    hunk_reloc8 = 1006
    hunk_drel32 = 1015
    hunk_drel16 = 1016
    hunk_drel8 = 1017
    hunk_relreloc32 = 1021
    hunk_absreloc16 = 1022
    hunk_end = 1010

    payload = bytearray()
    payload += u32(hunk_unit)
    payload += make_bstr("")
    payload += u32(hunk_name)
    payload += make_bstr("CODE")
    payload += u32(hunk_code)
    payload += u32(4)
    payload += b"\x00" * 16
    for hunk_type, offset in (
        (hunk_reloc16, 0),
        (hunk_reloc8, 2),
        (hunk_drel32, 4),
        (hunk_drel16, 8),
        (hunk_drel8, 10),
        (hunk_relreloc32, 12),
        (hunk_absreloc16, 14),
    ):
        payload += u32(hunk_type)
        payload += u32(1)
        payload += u32(1)
        payload += u32(offset)
        payload += u32(0)
    payload += u32(hunk_end)
    payload += u32(hunk_name)
    payload += make_bstr("DATA")
    payload += u32(hunk_data)
    payload += u32(1)
    payload += b"\x00\x00\x00\x00"
    payload += u32(hunk_end)
    return bytes(payload)


def make_synthetic_atari_prg(
    text: bytes,
    data: bytes,
    bss_size: int,
    reloc_offsets: list[int] | None = None,
    *,
    symbol_table: bytes = b"",
    symbol_table_type: int = 0,
    program_flags: int = 0,
    relocation_flag: int = 0,
    terminate_relocation_stream: bool = True,
) -> bytes:
    payload = bytearray()
    payload += u16(0x601A)
    payload += u32(len(text))
    payload += u32(len(data))
    payload += u32(bss_size)
    payload += u32(len(symbol_table))
    payload += u32(symbol_table_type)
    payload += u32(program_flags)
    payload += u16(relocation_flag)
    payload += text
    payload += data
    payload += symbol_table
    if reloc_offsets:
        sorted_offsets = sorted(reloc_offsets)
        payload += u32(sorted_offsets[0])
        previous = sorted_offsets[0]
        for offset in sorted_offsets[1:]:
            delta = offset - previous
            while delta > 254:
                payload.append(1)
                delta -= 254
            payload.append(delta)
            previous = offset
        if terminate_relocation_stream:
            payload.append(0)
    return bytes(payload)


@lru_cache(maxsize=1)
def load_file_manifest() -> list[dict[str, object]]:
    return [json.loads(line) for line in FILE_MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]


@lru_cache(maxsize=None)
def _read_corpus_disk_bytes_cached(
    source_relpath: str,
    container_relpath: str | None,
    member_name: str | None,
) -> bytes:
    if container_relpath is None:
        return (ROOT / source_relpath).read_bytes()
    container_path = ROOT / container_relpath
    assert member_name is not None
    with zipfile.ZipFile(container_path) as archive:
        data = archive.read(member_name)
    if member_name.lower().endswith(".adz"):
        return gzip.decompress(data)
    return data


def read_corpus_disk_bytes(entry: dict[str, object]) -> bytes:
    origin = entry["origin"]
    return _read_corpus_disk_bytes_cached(
        str(origin["source_relpath"]),
        origin["container_relpath"],
        origin["member_name"],
    )


@lru_cache(maxsize=None)
def _reconstruct_corpus_file_bytes_cached(entry_json: str) -> bytes:
    entry = json.loads(entry_json)
    image_bytes = read_corpus_disk_bytes(entry)
    extents = entry["file_ref"]["extents"]
    payload = bytearray()
    for extent in extents:
        start = extent["image_offset"]
        end = start + extent["byte_size"]
        payload.extend(image_bytes[start:end])
    return bytes(payload[: entry["size"]])


def reconstruct_corpus_file_bytes(entry: dict[str, object]) -> bytes:
    return _reconstruct_corpus_file_bytes_cached(json.dumps(entry, sort_keys=True))


@lru_cache(maxsize=None)
def _find_corpus_file_entry_cached(display_name: str, in_image_path: str) -> dict[str, object]:
    for entry in load_file_manifest():
        origin = entry["origin"]
        if (
            entry["platform"] == "amiga-hunk"
            and origin["display_name"] == display_name
            and origin["in_image_path"] == in_image_path
            and entry["expect"]["status"] == "ok"
        ):
            return entry
    raise AssertionError(f"Missing amiga-hunk corpus entry: {display_name} :: {in_image_path}")


def find_corpus_file_entry(display_name: str, in_image_path: str) -> dict[str, object]:
    return _find_corpus_file_entry_cached(display_name, in_image_path)


@lru_cache(maxsize=1)
def all_amiga_hunk_corpus_entries() -> list[dict[str, object]]:
    return [
        entry
        for entry in load_file_manifest()
        if entry["platform"] == "amiga-hunk" and entry["expect"]["status"] == "ok"
    ]


@lru_cache(maxsize=1)
def all_atari_st_corpus_entries() -> list[dict[str, object]]:
    return [
        entry
        for entry in load_file_manifest()
        if entry["platform"] == "atari-st" and entry["expect"]["status"] == "ok"
    ]


class PlatformBackendTestCaseMixin:
    @classmethod
    def setUpClass(cls) -> None:
        require_built_tools()
        cls.library = ctypes.CDLL(str(FILE_DLL))
        cls.library.platform_file_inspect_buffer_json.argtypes = [
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_size_t,
        ]
        cls.library.platform_file_inspect_buffer_json.restype = PlatformFileTextResult
        cls.library.platform_file_roundtrip_buffer.argtypes = [
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_size_t,
        ]
        cls.library.platform_file_roundtrip_buffer.restype = PlatformFileBufferResult
        cls.library.platform_file_free_text.argtypes = [ctypes.c_void_p]
        cls.library.platform_file_free_text.restype = None
        cls.library.platform_file_free_bytes.argtypes = [ctypes.c_void_p]
        cls.library.platform_file_free_bytes.restype = None
        cls.harness = _ensure_platform_backend_harness()

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def run_harness(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.harness), *args],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )

    def inspect_buffer(self, backend_name: str, data: bytes) -> dict[str, object]:
        data_array = (ctypes.c_ubyte * len(data)).from_buffer_copy(data if data else b"\0")
        result = self.library.platform_file_inspect_buffer_json(
            backend_name.encode("utf-8"),
            data_array,
            len(data),
        )
        self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
        try:
            return json.loads(ctypes.string_at(result.text).decode("utf-8"))
        finally:
            self.library.platform_file_free_text(result.text)

    def roundtrip_buffer(self, backend_name: str, data: bytes) -> bytes:
        data_array = (ctypes.c_ubyte * len(data)).from_buffer_copy(data if data else b"\0")
        result = self.library.platform_file_roundtrip_buffer(
            backend_name.encode("utf-8"),
            data_array,
            len(data),
        )
        self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
        try:
            return ctypes.string_at(result.data, result.size)
        finally:
            self.library.platform_file_free_bytes(result.data)


def _platform_backend_harness_source_text() -> str:
    return textwrap.dedent(
        """
        #include <stdio.h>
        #include <stdlib.h>
        #include <string.h>
        #include "m68k_backend.h"
        #include "m68k_object.h"

        static int command_atari_duplicate_sections(void) {
            char error[256];
            M68kObject object;
            M68kSection section;
            m68k_object_init(&object);
            object.platform_file_kind = M68K_PLATFORM_FILE_EXECUTABLE;
            memset(&section, 0, sizeof(section));
            section.name = "TEXT0";
            section.kind = M68K_SECTION_CODE;
            section.size = 4;
            section.data = (uint8_t *)"\\x4e\\x75\\x00\\x00";
            section.data_size = 4;
            if (m68k_object_add_section(&object, &section, NULL) != 0) return 2;
            section.name = "TEXT1";
            if (m68k_object_add_section(&object, &section, NULL) != 0) return 2;
            section.name = "DATA";
            section.kind = M68K_SECTION_DATA;
            section.data = (uint8_t *)"\\x00\\x00\\x00\\x00";
            if (m68k_object_add_section(&object, &section, NULL) != 0) return 2;
            if (M68K_BACKEND_ATARI_ST.write_file("NUL", &object, error, sizeof(error)) == 0) {
                fprintf(stderr, "unexpected success\\n");
                m68k_object_free(&object);
                return 1;
            }
            puts(error);
            m68k_object_free(&object);
            return 0;
        }

        int main(int argc, char **argv) {
            if (argc >= 2 && strcmp(argv[1], "atari-duplicate-sections") == 0) {
                return command_atari_duplicate_sections();
            }
            fprintf(stderr, "usage: %s atari-duplicate-sections\\n", argv[0]);
            return 2;
        }
        """
    )


@lru_cache(maxsize=1)
def _ensure_platform_backend_harness() -> Path:
    source_text = _platform_backend_harness_source_text()
    if not HARNESS_SOURCE.exists() or HARNESS_SOURCE.read_text(encoding="utf-8") != source_text:
        HARNESS_SOURCE.write_text(source_text, encoding="utf-8")
    compile_script = (
        "@echo off\n"
        'call "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Auxiliary\\Build\\vcvars64.bat" >nul || exit /b %errorlevel%\n'
        "cl /nologo /W4 /WX /std:c11 /D_CRT_SECURE_NO_WARNINGS "
        f'/I "{SRC_DIR}" "{HARNESS_SOURCE}" "{SRC_DIR / "m68k_object.c"}" "{SRC_DIR / "util_arena.c"}" '
        f'"{SRC_DIR / "platform_amiga_hunk.c"}" "{SRC_DIR / "platform_atari_st.c"}" '
        f'"{SRC_DIR / "platform_common.c"}" "{SRC_DIR / "platform_binary_io.c"}" '
        f'"{SRC_DIR / "generated" / "amiga_hunk_file_runtime.c"}" "{SRC_DIR / "generated" / "atari_st_prg_file_runtime.c"}" '
        f'/link /OUT:"{HARNESS_EXE}" || exit /b %errorlevel%\n'
    )
    if not HARNESS_COMPILE.exists() or HARNESS_COMPILE.read_text(encoding="utf-8") != compile_script:
        HARNESS_COMPILE.write_text(compile_script, encoding="utf-8")
    if HARNESS_EXE.exists():
        newest_input = max(
            path.stat().st_mtime
            for path in (
                HARNESS_SOURCE,
                SRC_DIR / "m68k_object.c",
                SRC_DIR / "util_arena.c",
                SRC_DIR / "platform_amiga_hunk.c",
                SRC_DIR / "platform_atari_st.c",
                SRC_DIR / "platform_common.c",
                SRC_DIR / "platform_binary_io.c",
                SRC_DIR / "generated" / "amiga_hunk_file_runtime.c",
                SRC_DIR / "generated" / "atari_st_prg_file_runtime.c",
            )
        )
        if HARNESS_EXE.stat().st_mtime >= newest_input:
            return HARNESS_EXE
    compile_result = subprocess.run(
        ["cmd", "/c", str(HARNESS_COMPILE)],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    assert compile_result.returncode == 0, compile_result.stdout + compile_result.stderr
    return HARNESS_EXE
