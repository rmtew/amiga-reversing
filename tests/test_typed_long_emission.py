"""Declared LONG fields retain their unit across even record strides."""
import json
import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm.binary_source import BinarySourceKind, HunkFileBinarySource
from amiga_reversing.disasm.c_backend import (
    assemble_platform_source_text_with_c_backend,
    render_project_source_with_c_backend,
)
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
    effective_metadata_text,
)
from amiga_reversing.disasm.manual_actions import build_target_identity
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


@pytest.mark.parametrize("odd", [False, True])
def test_real_native_declared_longs_follow_even_address_alignment(tmp_path: Path, odd: bool):
    size = 5 if odd else 18
    fields = ([{"name": "value", "type": "long", "offset": 1, "size": 4}] if odd else
              [{"name": "pixels", "type": "long", "offset": 0, "size": 4},
               {"name": "mask", "type": "long", "offset": 4, "size": 4},
               {"name": "dimensions", "type": "word", "offset": 8, "size": 10}])
    data = (bytes.fromhex('aa12345678') if odd else bytes.fromhex('00051dc8000689c40002001f002000000000'))
    data = data * 2
    assembly = ' SECTION section,code\n bra.b after\n dc.b ' + ','.join(f'${b:02X}' for b in data) + '\nafter:\n rts\n' + (' dc.w 0\n' if odd else '')
    binary = tmp_path / 'input.hunk'
    original, _ = assemble_platform_source_text_with_c_backend('amiga-hunk', assembly,
        output_path=binary, project_root=PROJECT_ROOT)
    source = HunkFileBinarySource(kind=BinarySourceKind.HUNK_FILE, path=binary,
        display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    (tmp_path / 'source_binary.json').write_text(json.dumps({'kind': 'hunk_file', 'path': str(binary)}))
    actions = [('create_manual_custom_struct', 'custom_struct', {'name': 'Frame', 'size': size, 'fields': fields}),
        ('create_manual_data_block_layout', 'data_block_layout', {'layout_id': 'frames', 'hunk': 0,
            'source_start': 2, 'source_end': 2 + len(data), 'name': 'frames', 'default_unit': 'byte'}),
        ('set_manual_data_block_element', 'data_block_element', {'data_block_element_id': 'frames:0',
            'layout_id': 'frames', 'offset': 0, 'width': len(data), 'kind': 'struct', 'array_count': 2,
            'array_stride': size, 'type_binding': {'type_binding_id': 'binding', 'layout_id': 'frames',
                'element_offset': 0, 'element_width': len(data), 'binding_kind': 'custom_struct',
                'bound_type_id': 'Frame', 'owner_action_id': 'a3'}})]
    records = [{'record': 'manual_action_log_header', 'version': 1, 'target_identity': build_target_identity(source)}]
    records += [{'record': 'manual_action', 'action_id': f'a{i}', 'sequence': i,
        'created_at': '2026-10-13T00:00:00+00:00', 'kind': kind, key: value}
        for i, (kind, key, value) in enumerate(actions, 1)]
    (tmp_path / 'manual_actions.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in records))
    metadata = json.loads(effective_metadata_text(tmp_path))
    longs = [e for e in metadata['seeded_entities'] if str(e.get('field_type')).lower() == 'long']
    assert len(longs) == (2 if odd else 4)
    assert [e['unit'] for e in longs] == (['byte', 'long'] if odd else ['long'] * 4)
    with effective_metadata_file(tmp_path) as path:
        rendered = render_project_source_with_c_backend(source, metadata_path=path, project_root=PROJECT_ROOT)
    if odd:
        assert 'dc.b $12,$34,$56,$78\t; value' in rendered
        assert 'dc.l $12345678\t; value' in rendered
    else:
        assert rendered.count('dc.l $00051DC8\t; pixels') == 2
        assert rendered.count('dc.l $000689C4\t; mask') == 2
        assert 'dc.b $00,$06,$89,$C4' not in rendered
    rebuilt, _ = assemble_platform_source_text_with_c_backend('amiga-hunk', rendered, project_root=PROJECT_ROOT)
    assert rebuilt == original
    oracle = PROJECT_ROOT / 'tools' / 'vasmm68k_mot.exe'
    assert oracle.is_file()
    outputs = []
    for name, text in [('original', assembly), ('rendered', rendered)]:
        source_path = tmp_path / f'{name}.s'
        output_path = tmp_path / f'{name}.bin'
        source_path.write_text(text)
        result = subprocess.run([str(oracle), '-quiet', '-Fbin', '-o', str(output_path), str(source_path)],
            capture_output=True, text=True, timeout=10, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        outputs.append(output_path.read_bytes())
    assert outputs[0] == outputs[1]
