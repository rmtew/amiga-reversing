"""Conditional reads consume validated native directory domains, not guessed targets."""
import pytest

from amiga_reversing.disasm import c_backend
from tests.test_source_pointer_loop_domain import header_table_artifact


GUARD = ' tst.w d0\n beq.w skip_extra\n move.l 2(a0),d2\nskip_extra:\n'


def check_directory(tmp_path, **options):
    artifact, original = header_table_artifact(tmp_path, derived=True, zero_counts=True,
        after_count=options.pop('after_count', GUARD), **options)
    try:
        payload = artifact.analysis_payload()[0]
        assert not payload['incomplete_analysis']
        section = payload['sections'][0]
        inline = artifact.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', inline)[0] == original
        return section, inline
    finally:
        artifact.close()


@pytest.mark.parametrize('count,aliases', [(2, False), (104, False), (3, True)])
def test_guarded_extension_from_a_validated_source_cursor_domain(tmp_path, count, aliases):
    section, inline = check_directory(tmp_path, count=count, aliases=aliases)
    extra = [r for r in section['recovered_platform_typed_accesses'] if r['field_name'] == 'extra']
    assert len(extra) == 1
    assert extra[0]['root_struct_name'] == 'ExtendedHeader'
    assert 'ExtendedHeader_extra' in inline
    assert not any(r['offset'] == extra[0]['offset'] and r['operand_index'] == extra[0]['operand_index']
                   for r in section['recovered_platform_unresolved_typed_accesses'])
    assert any(v['resolution'] == 'type_domain' and
               v['table_origin']['selection_kind'] == 'bounded_source_cursor'
               for v in section['address_values'])


@pytest.mark.parametrize('options', [
    dict(count=2, trips=3), dict(count=2, trips='unknown'),
    dict(count=2, null_prefix=True), dict(count=3, aliases=True, trips=2),
    dict(count=2, trips=1),  # The selected prefix excludes the later child.
    dict(count=2, exposure=True),
    dict(count=2, body='move.w #1,(a1)'),
    dict(count=2, after_count='move.w #1,(a0)\n' + GUARD),
    dict(count=2, after_count='jsr (a1)\n' + GUARD),
    dict(count=2, after_count='move.b #1,d0\n' + GUARD),
    dict(count=2, after_count='lea.l header_0(pc),a0\n' + GUARD),
])
def test_unproved_domains_and_invalidated_relations_refuse(tmp_path, options):
    section, _ = check_directory(tmp_path, **options)
    assert not [r for r in section['recovered_platform_typed_accesses'] if r['field_name'] == 'extra']


def test_refined_record_type_flows_into_the_existing_call_input_solver(tmp_path):
    section, inline = check_directory(tmp_path, count=2, loop=False, indexed=True,
        index_code='moveq.l #4,d2',
        after_count=' tst.w d0\n beq.w skip_extra\n bsr.w consume_extra\nskip_extra:\n',
        code_tail='consume_extra:\n move.l 2(a0),d2\n rts\n')
    refs = [r for r in section['recovered_platform_typed_accesses'] if r['field_name'] == 'extra']
    assert len(refs) == 1
    assert refs[0]['root_struct_name'] == 'ExtendedHeader'
    assert 'ExtendedHeader_extra' in inline
    assert not any(r['offset'] == refs[0]['offset'] and r['operand_index'] == refs[0]['operand_index']
                   for r in section['recovered_platform_unresolved_typed_accesses'])


def test_loop_call_does_not_assume_return_stack_disjoint_from_source_records(tmp_path):
    section, _ = check_directory(tmp_path, count=104,
        after_count=' tst.w d0\n beq.w skip_extra\n bsr.w consume_extra\nskip_extra:\n',
        code_tail='consume_extra:\n move.l 2(a0),d2\n rts\n')
    assert not [r for r in section['recovered_platform_typed_accesses'] if r['field_name'] == 'extra']


@pytest.mark.parametrize('store,expected', [('move.w #1,2(a1)', True),
    ('move.b #1,2(a1)', True), ('move.l #1,2(a1)', False), ('move.b #1,1(a1)', False)])
def test_directory_relation_survives_known_write_to_another_field(tmp_path, store, expected):
    # Capture in the unchanged directory loop, then mutate another field after
    # leaving it. Fresh snapshot reads on later mutated iterations are a
    # separate obligation; this test concerns an already captured predicate.
    access = ('move.w (a0)+,d0\n dbf.w d4,again\n'
              'lea.l header_0(pc),a1\n' + store + '\n' + GUARD)
    section, _ = check_directory(tmp_path, count=104, loop=False, record_access=access)
    assert any(r['field_name'] == 'extra' for r in section['recovered_platform_typed_accesses']) == expected
