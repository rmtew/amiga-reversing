from __future__ import annotations

import ctypes
import json
from pathlib import Path

from src.tests._build_helpers import prepare_test_dll

ROOT = Path(__file__).resolve().parents[2]
DISK_DLL = ROOT / "src" / "build" / "platform_disk_lib.dll"


class PlatformDiskTestCaseMixin:
    @classmethod
    def setUpClass(cls) -> None:
        cls.library = ctypes.CDLL(str(prepare_test_dll(DISK_DLL)))
        cls.library.platform_disk_inspect_buffer_json.argtypes = [
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_char_p,
            ctypes.c_size_t,
        ]
        cls.library.platform_disk_inspect_buffer_json.restype = ctypes.c_int
        cls.library.platform_disk_free_json.argtypes = [ctypes.c_void_p]
        cls.library.platform_disk_free_json.restype = None

    def inspect_disk_buffer(self, platform_name: str, image: bytes) -> dict[str, object]:
        json_ptr = ctypes.c_void_p()
        error_buf = ctypes.create_string_buffer(256)
        data_array = (ctypes.c_ubyte * len(image)).from_buffer_copy(image if image else b"\0")
        result = self.library.platform_disk_inspect_buffer_json(
            platform_name.encode("utf-8"),
            data_array,
            len(image),
            ctypes.byref(json_ptr),
            error_buf,
            len(error_buf),
        )
        self.assertEqual(result, 0, error_buf.value.decode("utf-8"))
        try:
            return json.loads(ctypes.string_at(json_ptr).decode("utf-8"))
        finally:
            self.library.platform_disk_free_json(json_ptr)
