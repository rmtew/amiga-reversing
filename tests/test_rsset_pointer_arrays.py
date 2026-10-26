"""Declared runtime pointer arrays retain their unit and exact storage extent."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact
from amiga_reversing.disasm import c_backend


@pytest.mark.parametrize('offset,size,kind,declaration', [
    (0x200, 40, 'pointer_table', 'RS.L 10'),
    (0x202, 1000, 'pointer_table', 'RS.L 250'),
    (0x200, 240, 'pointer_table', 'RS.L 60'),
    (0x200, 4, 'pointer_table', 'RS.L 1'),
    (0x201, 40, 'pointer_table', 'RS.B 40'),
    (0x200, 6, 'pointer_table', 'RS.B 6'),
    (0x200, 1000, 'byte_array', 'RS.B 1000'),
])
def test_runtime_pointer_array_declaration(tmp_path, offset, size, kind, declaration):
    artifact, original = cursor_artifact(tmp_path, f'lea.l ${offset:X}(a6),a0',
        metadata_extra=dict(rsset_layout_regions=[dict(layout_name='app', offset=offset,
            size=size, symbol='object_references', storage_kind=kind)]))
    try:
        source = artifact.inline_source_text_with_profile()[0]
        assert f'object_references {declaration}\n' in source
        assert f'object_references EQU ${offset:X}' not in source
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
        field = next(r for r in artifact.analysis_payload()[0]['base_layout_fields']
                     if r['symbol'] == 'object_references')
        assert field['offset'] == offset and field['size'] == size
    finally:
        artifact.close()
