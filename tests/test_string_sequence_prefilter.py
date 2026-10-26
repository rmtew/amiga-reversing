"""String candidate filtering preserves code/data ownership and declared aliases."""
import json

import pytest

from amiga_reversing.disasm import c_backend
from tests.test_c_backend import _requires_c_backend_dlls

pytestmark = pytest.mark.c_backend


@pytest.mark.parametrize('case', ['three', 'two', 'owned', 'control_declared', 'control_alias', 'punctuation_declared', 'two_groups'])
def test_sequence_filter_keeps_legacy_admission(tmp_path, case):
    _requires_c_backend_dlls()
    control = case.startswith('control')
    data = b'\r\nA\0\r\nB\0\r\nC\0' if control else b'MISS\xffHITS\xffRUNS\xff'
    if case == 'two':
        data = b'MISS\xffHITS\xff'
    if case == 'punctuation_declared':
        data = b'!\0@\0?\0'
    if case == 'two_groups':
        data += b'\0' + data
    entities = []
    if case in {'owned', 'control_alias'}:
        entities.append(dict(type='data', subtype='opaque_data', hunk=0,
                             addr=3, end=15 if control else 8))
    if control:
        entities += [dict(type='data', subtype='string', hunk=0,
                          addr=3 + 4 * i, end=7 + 4 * i) for i in range(3)]
    if case == 'punctuation_declared':
        entities += [dict(type='data', subtype='string', hunk=0,
                          addr=3 + 2 * i, end=5 + 2 * i) for i in range(3)]
    binary = tmp_path / 'sequence.raw'
    binary.write_bytes(bytes.fromhex('4e7500') + data)
    metadata = tmp_path / 'target.json'
    metadata.write_text(json.dumps(dict(seeded_entities=entities)))
    payload = json.loads(c_backend._platform_file_text(
        'platform_file_facts_v2_analysis_raw_path_json_alloc',
        'amiga-raw', str(binary), 0, 0, 0, str(metadata), '',
        project_root=c_backend.PROJECT_ROOT))
    analysis = payload  # Direct analysis API is flat; artifact.analysis_payload unwraps separately.
    sequences = [(item['offset'], item['size']) for item in
                 analysis['analysis_policy']['structured_data_items']
                 if item.get('source_pattern') == 'string_table_sequence']
    expected = [(3, 4), (7, 4), (11, 4)] if control else [(3, 5), (8, 5), (13, 5)]
    if case == 'punctuation_declared':
        expected = [(3, 2), (5, 2), (7, 2)]
    if case == 'two_groups':
        expected += [(19, 5), (24, 5), (29, 5)]
    assert sequences == ([] if case in {'two', 'owned'} else expected)
    assert analysis['source_quality_diagnostic_count'] == 0
    if case in {'owned', 'control_alias'}:
        assert any(item['offset'] == 3 and item['kind'] == 1 for item in
                   analysis['analysis_policy']['structured_data_items'])
