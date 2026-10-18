"""Exercise the real metadata boundary through policy export and both assemblers."""
from __future__ import annotations

import ctypes
import json
import re
import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from tests.test_c_backend import _requires_c_backend_dlls

pytestmark = pytest.mark.c_backend


def _vasm(tmp_path: Path, name: str, text: str) -> bytes:
    source = tmp_path / f'{name}.s'
    output = tmp_path / f'{name}.bin'
    source.write_text(text, encoding='utf-8')
    result = subprocess.run([str(PROJECT_ROOT / 'tools/vasmm68k_mot.exe'), '-Fbin', '-quiet',
                             '-o', str(output), str(source)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return output.read_bytes()


def _source(tmp_path: Path) -> RawBinarySource:
    _requires_c_backend_dlls()
    path = tmp_path / 'boundary.bin'
    path.write_bytes(_vasm(tmp_path, 'original', '    SECTION code,code\n    move.w #1023,d0\n    rts\n'))
    return RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=path,
                           address_model=RawAddressModel.LOCAL_OFFSET, load_address=0,
                           entrypoint=0, code_start_offset=0, display_path=str(path),
                           analysis_cache_path=tmp_path / "boundary.analysis")


def _metadata(tmp_path: Path, count: int, *, duplicate: bool = False) -> Path:
    equates = [{'name': f'BOUND_EQ_{index:04d}', 'value': index, 'value_representation': 'hex'}
               for index in range(count)]
    if duplicate:
        equates.append({'name': f'BOUND_EQ_{count-1:04d}', 'value': 600, 'value_representation': 'decimal'})
    path = tmp_path / 'metadata.json'
    path.write_text(json.dumps({'target_type': 'raw_binary', 'target_equates': equates}), encoding='utf-8')
    return path


@pytest.mark.parametrize('count', [526, 1024])
def test_real_equate_capacity_exports_and_reassembles_last_symbol(tmp_path: Path, count: int) -> None:
    source = _source(tmp_path)
    accessor = c_backend._platform_file_dll(PROJECT_ROOT).platform_file_target_equate_count_capacity
    accessor.argtypes = []
    accessor.restype = ctypes.c_size_t
    assert accessor() == 1024
    text = c_backend.render_project_source_with_c_backend(
        source, metadata_path=_metadata(tmp_path, count), project_root=PROJECT_ROOT)
    declarations = [line for line in text.splitlines() if re.match(r'^BOUND_EQ_\d{4}\s+EQU\s+', line)]
    assert len(declarations) == count
    assert any(re.match(rf'^BOUND_EQ_{count-1:04d}\s+EQU\s+\${count-1:X}$', line) for line in declarations)
    assert c_backend.assemble_platform_source_text_with_c_backend(
        'amiga-raw', text, project_root=PROJECT_ROOT)[0] == source.path.read_bytes()
    assert _vasm(tmp_path, 'rendered', text) == source.path.read_bytes()
    # Resolve the last declaration independently instead of merely counting it.
    last_symbol_program = '\n'.join(declarations) + f'\n    SECTION code,code\n    move.w #BOUND_EQ_{count-1:04d},d0\n    rts\n'
    last_symbol_bytes = _vasm(tmp_path, 'last_original', f'    SECTION code,code\n    move.w #{count-1},d0\n    rts\n')
    assert c_backend.assemble_platform_source_text_with_c_backend(
        'amiga-raw', last_symbol_program, project_root=PROJECT_ROOT)[0] == last_symbol_bytes
    assert _vasm(tmp_path, 'last_symbol', last_symbol_program) == last_symbol_bytes


def test_real_equate_overflow_rejects_1025_without_truncated_output(tmp_path: Path) -> None:
    source = _source(tmp_path)
    with pytest.raises(RuntimeError, match=r'target equate capacity exceeded \(1024\)'):
        c_backend.render_project_source_with_c_backend(
            source, metadata_path=_metadata(tmp_path, 1025), project_root=PROJECT_ROOT)


def test_real_duplicate_equate_updates_at_capacity(tmp_path: Path) -> None:
    source = _source(tmp_path)
    text = c_backend.render_project_source_with_c_backend(
        source, metadata_path=_metadata(tmp_path, 1024, duplicate=True), project_root=PROJECT_ROOT)
    assert len(re.findall(r'^BOUND_EQ_\d{4}\s+EQU\s+', text, flags=re.MULTILINE)) == 1024
    assert re.search(r'^BOUND_EQ_1023\s+EQU\s+600$', text, flags=re.MULTILINE)


def test_real_1025th_equate_append_preserves_target_and_history(tmp_path: Path) -> None:
    from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
    from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata

    source = _source(tmp_path)
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))

    def action(index):
        return ManualActionKind.CREATE_MANUAL_TARGET_EQUATE, {'target_equate': {
            'target_equate_id': f'equate-{index}', 'name': f'BOUND_EQ_{index:04d}', 'value': index,
        }}

    append_manual_actions(tmp_path, actions=[action(index) for index in range(1024)], binary_source=source)
    before = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob('*')
              if p.is_file() and p.name != '.target-history.lock'}
    with pytest.raises(ValueError, match='at most 1024 target equates.*candidate contains 1025'):
        append_manual_actions(tmp_path, actions=[action(1024)], binary_source=source)
    assert {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob('*')
            if p.is_file() and p.name != '.target-history.lock'} == before
