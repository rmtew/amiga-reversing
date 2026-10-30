"""Explicit raw image entry differs from a discovered or callable code seed."""
import pytest
from tests.test_guarded_source_record_domains import check_directory


def test_raw_runtime_entry_retains_initial_image_provenance(tmp_path):
    section, source = check_directory(tmp_path, count=104, target_type='raw_binary')
    extra = [r for r in section['recovered_platform_typed_accesses'] if r['field_name'] == 'extra']
    assert len(extra) == 1
    assert 'ExtendedHeader_extra' in source
    assert any(r['offset'] == 0 and r['evidence_kind'] == 'raw_image_entry'
               for r in section['code_start_refs'])


@pytest.mark.parametrize('options', [
    dict(exposure=True), dict(body='move.w #1,(a1)'),
    dict(after_count='move.w #1,(a0)\n tst.w d0\n beq.w done\n move.l 2(a0),d2\ndone:\n'),
    dict(after_count='jsr (a1)\n tst.w d0\n beq.w done\n move.l 2(a0),d2\ndone:\n'),
])
def test_raw_entry_does_not_bypass_snapshot_mutation_or_alternate_roots(tmp_path, options):
    section, _ = check_directory(tmp_path, count=104, target_type='raw_binary', **options)
    assert not [r for r in section['recovered_platform_typed_accesses'] if r['field_name'] == 'extra']
