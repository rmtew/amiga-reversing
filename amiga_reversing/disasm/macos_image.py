"""Classic Mac OS disk-image normalization helpers."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

DEFAULT_NDIF2RAW_PATH = Path("ext/tools/ndif2raw/ndif2raw.exe")


def read_macos_hfs_image_bytes(
    image_path: Path,
    *,
    ndif2raw_path: Path = DEFAULT_NDIF2RAW_PATH,
) -> bytes:
    data = image_path.read_bytes()
    if data[1024:1026] == b"BD":
        return data
    if not ndif2raw_path.exists():
        raise FileNotFoundError(f"NDIF provider is required for non-raw image: {ndif2raw_path}")
    with tempfile.TemporaryDirectory(prefix="macos-asm-import-") as temp_dir:
        output = Path(temp_dir) / "image.raw"
        subprocess.run(
            [str(ndif2raw_path), "--format=macbinary", str(image_path), str(output)],
            check=True,
            capture_output=True,
        )
        return output.read_bytes()
