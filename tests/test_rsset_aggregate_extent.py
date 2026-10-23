"""An aggregate app region keeps its full extent and adjacent declarations."""
from __future__ import annotations

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_action
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_c_backend import _requires_c_backend_dlls
from tests.test_rsset_rename_extent import _render, _vasm

pytestmark = pytest.mark.c_backend


@pytest.mark.parametrize('extent', [255, 256, 400, 32767])
def test_app_region_renders_exact_extent_and_keeps_neighbor(tmp_path, extent):
    _requires_c_backend_dlls()
    original = _vasm(tmp_path, 'original', '\n'.join([
        '    SECTION section,code',
        '    move.w $0000(a6),d2',
        '    move.w $0(a6,d1.w),d0',
        f'    move.b ${extent:04X}(a6),d1', '    rts', '',
    ]))
    binary = tmp_path / 'fixture.bin'
    binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'binary.analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    kind, payload = target_catalog_manual_payload('target.rsset_region.add', {
        'offset': 0, 'size': extent, 'symbol': 'app_row_offsets', 'storage_kind': 'byte_array',
    })
    append_manual_action(tmp_path, kind=ManualActionKind(kind), payload=payload, binary_source=source)
    kind, payload = target_catalog_manual_payload('target.rsset_region.add', {
        'offset': extent, 'size': 1, 'symbol': 'next_phase', 'storage_kind': 'scalar',
    })
    append_manual_action(tmp_path, kind=ManualActionKind(kind), payload=payload, binary_source=source)
    text = _render(tmp_path, source)
    assert f'app_row_offsets RS.B {extent}\nnext_phase RS.B 1\n' in text
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text)
    assert rebuilt == original
    assert _vasm(tmp_path, 'rebuilt', text) == original
    log = (tmp_path/'manual_actions.jsonl').read_bytes()
    journal = tmp_path/'decision_journal.jsonl'
    journal.write_bytes(b'preserved journal\n')
    with pytest.raises(ValueError, match='1..32767'):
        kind, payload = target_catalog_manual_payload('target.rsset_region.edit', {
            'offset': 0, 'size': 32768, 'symbol': 'too_large', 'storage_kind': 'byte_array',
        })
        append_manual_action(tmp_path, kind=ManualActionKind(kind), payload=payload, binary_source=source)
    assert (tmp_path/'manual_actions.jsonl').read_bytes() == log
    assert journal.read_bytes() == b'preserved journal\n'
