#!/usr/bin/env py.exe
"""Sync vendored Amiga includes from an original NDK tree.

Copies original include files into ext/amiga_includes with:
- lowercase relative paths
- LF-only line endings
- generated *_lib.i files derived from original raw includes + FD files
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import Any, cast

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kb.ndk_parser import fd_stem_to_lib_name, parse_fd_file, resolve_include_i_dir

FUNCDEF_RE = re.compile(r"^\s*FUNCDEF\s+([A-Za-z_]\w*)\b")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def _write_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8", newline="\n")


def _find_fd_dir(ndk_root: Path) -> Path:
    for candidate in (
        ndk_root / "INCLUDES&LIBS" / "FD",
        ndk_root / "FD",
        ndk_root / "LIBS" / "FD",
    ):
        if candidate.is_dir():
            return candidate
    matches = sorted(path for path in ndk_root.rglob("*.FD") if path.is_file())
    if not matches:
        raise ValueError(f"Could not find FD directory under {ndk_root}")
    return matches[0].parent


def _scan_funcdef_names(path: Path) -> list[str]:
    names: list[str] = []
    for line in _read_text(path).splitlines():
        match = FUNCDEF_RE.match(line)
        if match is not None:
            names.append(match.group(1))
    return names


def _infer_devpac_lib_relpath(include_dir: Path, fd_stem: str, lib_name: str) -> str:
    stem_lower = fd_stem.lower()
    base_name, kind = lib_name.rsplit(".", 1)
    if kind == "device":
        return f"devices/{stem_lower}_lib.i"
    if kind == "resource":
        return f"resources/{stem_lower}_lib.i"
    if kind == "gadget":
        return f"gadgets/{stem_lower}_lib.i"
    if kind == "datatype":
        return f"datatypes/{stem_lower}_lib.i"
    if (include_dir / base_name.upper()).is_dir() or (include_dir / base_name.lower()).is_dir():
        return f"{base_name.lower()}/{stem_lower}_lib.i"
    return f"libraries/{stem_lower}_lib.i"


def _generate_devpac_lvo_lines(raw_names: list[str], fd_functions: dict[str, dict[str, object]]) -> list[str]:
    if not fd_functions:
        raise ValueError("FD data has no functions")
    fd_lvos = {
        name: int(cast(Any, entry["lvo"]))
        for name, entry in fd_functions.items()
        if "lvo" in entry
    }
    if raw_names:
        anchors = [(index, name, fd_lvos[name]) for index, name in enumerate(raw_names) if name in fd_lvos]
        if not anchors:
            raise ValueError("raw _lib.i has no names matching FD functions")
        start_lvo = anchors[0][2] + 6 * anchors[0][0]
        for index, name, lvo in anchors:
            expected = start_lvo - 6 * index
            if expected != lvo:
                raise ValueError(
                    f"raw _lib.i / FD mismatch for {name}: expected {expected}, FD says {lvo}"
                )
        names = raw_names
    else:
        start_lvo = max(fd_lvos.values())
        names = [name for name, _lvo in sorted(fd_lvos.items(), key=lambda item: item[1], reverse=True)]
    return [f"_LVO{name}\tEQU\t{start_lvo - 6 * index}" for index, name in enumerate(names)]


def sync_amiga_includes(ndk_root: Path, dest_root: Path) -> None:
    include_dir = Path(resolve_include_i_dir(str(ndk_root)))
    fd_dir = _find_fd_dir(ndk_root)
    include_dest = dest_root / "include"
    if dest_root.exists():
        shutil.rmtree(dest_root)
    include_dest.mkdir(parents=True, exist_ok=True)

    raw_lib_paths: dict[str, str] = {}
    for source_path in sorted(path for path in include_dir.rglob("*") if path.is_file()):
        relpath = source_path.relative_to(include_dir).as_posix().lower()
        if source_path.suffix.lower() != ".i":
            continue
        _write_lf(include_dest / relpath, _read_text(source_path))
        if relpath.endswith("_lib.i"):
            raw_lib_paths[Path(relpath).stem.lower()] = relpath

    for fd_path in sorted(fd_dir.glob("*_LIB.FD")):
        fd_stem = fd_path.stem.removesuffix("_LIB").lower()
        fd_data = parse_fd_file(str(fd_path))
        lib_name = fd_stem_to_lib_name(fd_stem)
        dest_relpath = raw_lib_paths.get(
            f"{fd_stem}_lib",
            _infer_devpac_lib_relpath(include_dir, fd_stem, lib_name),
        )
        source_raw = include_dir / Path(dest_relpath.upper())
        raw_names = _scan_funcdef_names(source_raw) if source_raw.is_file() else []
        lines = _generate_devpac_lvo_lines(raw_names, fd_data["functions"])
        _write_lf(include_dest / dest_relpath, "\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ndk_root", help="Original NDK root, e.g. D:\\NDK\\NDK_2.0")
    parser.add_argument(
        "--dest-root",
        default="ext/amiga_includes/ndk_2.0",
        help="Destination root containing include/",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sync_amiga_includes(Path(args.ndk_root), Path(args.dest_root))


if __name__ == "__main__":
    main()
