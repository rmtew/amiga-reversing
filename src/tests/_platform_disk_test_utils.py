from __future__ import annotations

import ctypes
import json
from pathlib import Path

from src.tests._build_helpers import prepare_test_dll

ROOT = Path(__file__).resolve().parents[2]
DISK_DLL = ROOT / "src" / "build" / "platform_disk_lib.dll"
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


class PlatformDiskTextResult(ctypes.Structure):
    _fields_ = [
        ("text", ctypes.c_void_p),
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


class PlatformDiskTestCaseMixin:
    @classmethod
    def setUpClass(cls) -> None:
        cls.library = ctypes.CDLL(str(prepare_test_dll(DISK_DLL)))
        cls.library.platform_disk_inspect_buffer_json.argtypes = [
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_size_t,
        ]
        cls.library.platform_disk_inspect_buffer_json.restype = PlatformDiskTextResult
        cls.library.platform_disk_inspect_path_json_alloc.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        cls.library.platform_disk_inspect_path_json_alloc.restype = ctypes.c_int
        cls.library.platform_disk_extract_entry_path_bytes_alloc.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(ctypes.c_void_p),
        ]
        cls.library.platform_disk_extract_entry_path_bytes_alloc.restype = ctypes.c_int
        cls.library.platform_disk_free_text.argtypes = [ctypes.c_void_p]
        cls.library.platform_disk_free_text.restype = None
        cls.library.platform_disk_free_bytes.argtypes = [ctypes.c_void_p]
        cls.library.platform_disk_free_bytes.restype = None

    def inspect_disk_buffer(self, platform_name: str, image: bytes) -> dict[str, object]:
        data_array = (ctypes.c_ubyte * len(image)).from_buffer_copy(image if image else b"\0")
        result = self.library.platform_disk_inspect_buffer_json(
            platform_name.encode("utf-8"),
            data_array,
            len(image),
        )
        self.assertFalse(_diag_has_errors(result.diagnostics), _diag_message(result.diagnostics))
        try:
            return json.loads(ctypes.string_at(result.text).decode("utf-8"))
        finally:
            self.library.platform_disk_free_text(result.text)

    def inspect_disk_path_alloc(self, platform_name: str, image_path: Path) -> dict[str, object]:
        out_text = ctypes.c_void_p()
        result = self.library.platform_disk_inspect_path_json_alloc(
            platform_name.encode("utf-8"),
            str(image_path).encode("utf-8"),
            ctypes.byref(out_text),
        )
        self.assertEqual(result, 0)
        try:
            return json.loads(ctypes.string_at(out_text).decode("utf-8"))
        finally:
            self.library.platform_disk_free_text(out_text)

    def extract_disk_entry_path_alloc(self, platform_name: str, image_path: Path, entry_path: str) -> bytes:
        out_data = ctypes.c_void_p()
        out_size = ctypes.c_size_t()
        out_error = ctypes.c_void_p()
        result = self.library.platform_disk_extract_entry_path_bytes_alloc(
            platform_name.encode("utf-8"),
            str(image_path).encode("utf-8"),
            entry_path.encode("utf-8"),
            ctypes.byref(out_data),
            ctypes.byref(out_size),
            ctypes.byref(out_error),
        )
        try:
            error = ctypes.string_at(out_error).decode("utf-8") if out_error.value else ""
            self.assertEqual(result, 0, error)
            return bytes(ctypes.string_at(out_data, out_size.value))
        finally:
            if out_error.value:
                self.library.platform_disk_free_text(out_error)
            if out_data.value:
                self.library.platform_disk_free_bytes(out_data)

    def extract_disk_entry_path_alloc_error(self, platform_name: str, image_path: Path, entry_path: str) -> str:
        out_data = ctypes.c_void_p()
        out_size = ctypes.c_size_t()
        out_error = ctypes.c_void_p()
        result = self.library.platform_disk_extract_entry_path_bytes_alloc(
            platform_name.encode("utf-8"),
            str(image_path).encode("utf-8"),
            entry_path.encode("utf-8"),
            ctypes.byref(out_data),
            ctypes.byref(out_size),
            ctypes.byref(out_error),
        )
        try:
            self.assertNotEqual(result, 0)
            self.assertFalse(out_data.value)
            return ctypes.string_at(out_error).decode("utf-8") if out_error.value else ""
        finally:
            if out_error.value:
                self.library.platform_disk_free_text(out_error)
            if out_data.value:
                self.library.platform_disk_free_bytes(out_data)
