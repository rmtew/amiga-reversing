"""Address formation must not acquire a physical outside-record footprint."""
import pytest

from tests.test_app_cursor_propagation import cursor_artifact


@pytest.mark.parametrize(('body', 'role', 'span'), [
    ('lea.l 4(a0),a1', 'address', 4),
    ('lea.l -4(a0),a1', 'address', 4),
    ('pea.l 4(a0)\naddq.l #4,a7', 'address', 4),
    ('move.l 4(a0),d0', 'memory_read', 4),
    ('move.l d0,4(a0)', 'memory_write', 4),
    # This is the generated destination role, not a complete RMW/bus trace.
    ('addi.l #1,4(a0)', 'memory_write', 4),
    ('movem.l d0-d1,4(a0)', 'memory_write', 8),
    ('movem.l 4(a0),d0-d1', 'memory_read', 8),
])
def test_unresolved_role_uses_generated_metadata_without_admitting_a_field(tmp_path, body, role, span):
    artifact, _ = cursor_artifact(tmp_path, body, regions=False, metadata_extra=dict(
        custom_structs=[dict(name='Record', size=4,
                            fields=[dict(name='value', type='LONG', offset=0, size=4)])],
        entry_register_seeds=[dict(hunk=0, entry_offset=0, register='A0',
                                  kind='struct_ptr', struct_name='Record', note='Fixture input')]))
    try:
        analysis = artifact.analysis_payload()[0]
        assert not analysis['incomplete_analysis']
        gap, = analysis['sections'][0]['recovered_platform_unresolved_typed_accesses']
        assert gap['classification'] == 'field_gap'
        assert gap['access'] == role and gap['access_size'] == span
        page = artifact.query_payload('field_gaps', limit=100)
        item, = page['items']
        assert item['status'] == 'unresolved' and item['access'] == role
        assert item['access_size'] == span
        row = artifact.row_for_source_offset(section_index=0, offset=gap['offset'])
        assert row['unresolved_typed_accesses'][0]['access'] == role
        ins, = artifact.query_payload('instructions', section_index=0, source_offset=gap['offset'],
                                     end_offset=gap['offset'] + 1, limit=1)['items']
        operand = next(x for x in ins['operand_facts'] if x['operand_index'] == gap['operand_index'])
        assert operand['access'] == role
    finally:
        artifact.close()
