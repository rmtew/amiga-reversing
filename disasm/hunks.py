from __future__ import annotations
"""Hunk preparation helpers for disassembly session assembly."""

from pathlib import Path

from disasm.types import DisassemblySession, HunkDisassemblySession


def prepare_hunk_code(code: bytes, relocated_segments: list[dict]
                      ) -> tuple[bytes, int, list[dict], int, int]:
    code_size = len(code)
    reloc_file_offset = 0
    reloc_base_addr = 0
    if relocated_segments:
        seg = relocated_segments[0]
        reloc_file_offset = seg["file_offset"]
        reloc_base_addr = seg["base_addr"]
        payload_size = code_size - reloc_file_offset
        runtime_size = reloc_base_addr + payload_size
        runtime_code = bytearray(runtime_size)
        runtime_code[:reloc_file_offset] = code[:reloc_file_offset]
        runtime_code[reloc_base_addr:] = code[reloc_file_offset:]
        code = bytes(runtime_code)
        code_size = runtime_size
    return code, code_size, relocated_segments, reloc_file_offset, reloc_base_addr


def build_session_object(*, target_name: str | None, binary_path: str | Path,
                         entities_path: str | Path, output_path: str | Path | None,
                         entities: list[dict], hunk_sessions: list,
                         profile_stages: bool) -> DisassemblySession:
    binary_path = Path(binary_path)
    return DisassemblySession(
        target_name=target_name,
        binary_path=binary_path,
        entities_path=Path(entities_path),
        analysis_cache_path=binary_path.with_suffix(".analysis"),
        output_path=Path(output_path) if output_path else None,
        entities=entities,
        hunk_sessions=hunk_sessions,
        profile_stages=profile_stages,
    )


def build_hunk_session(**kwargs) -> HunkDisassemblySession:
    return HunkDisassemblySession(**kwargs)
