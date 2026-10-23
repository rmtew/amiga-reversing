"""One-past cursor values may step back into a record without typing end reads."""
import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from tests.test_typed_postincrement_cursor import _artifact, _vasm
from tests.test_static_field_seed_cursor import _fields, _seed


@pytest.mark.parametrize('suffix,width', [('b', 1), ('w', 2), ('l', 4)])
def test_complete_record_reads_then_pointer_store_and_reverse_writes_are_typed(tmp_path, suffix, width):
    instructions = [f'move.{suffix} (a0)+,d{i}' for i in range(3)]
    instructions += ['move.l a0,(a1)']
    instructions += [f'move.{suffix} d{i},-(a0)' for i in reversed(range(3))]
    source, metadata, artifact, original = _artifact(tmp_path, instructions, width)
    try:
        fields = artifact.query_payload('fields', limit=100)['items']
        names = [f['field_name'] for f in fields if f.get('field_name')]
        assert names == ['first','second','third','third','second','first']
        rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata, project_root=PROJECT_ROOT)
    finally:artifact.close()
    for i,name in enumerate(['first','second','third']):
        assert f'move.{suffix} (a0)+,d{i}\t; operand 1: Triplet_{name} at (a0)+' in rendered
        assert f'move.{suffix} d{i},-(a0)\t; operand 2: Triplet_{name} at -(a0)' in rendered
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered, project_root=PROJECT_ROOT)
    assert rebuilt == original == _vasm(tmp_path, 'rebuilt', rendered)


@pytest.mark.parametrize('suffix,width', [('b', 1), ('w', 2), ('l', 4)])
@pytest.mark.parametrize('access', ['read', 'write'])
def test_endpoint_access_is_untyped_but_bounded_predecrement_still_resolves(tmp_path, suffix, width, access):
    instructions = [f'move.{suffix} (a0)+,d{i}' for i in range(3)]
    endpoint_operands = '(a0),d3' if access == 'read' else 'd3,(a0)'
    instructions += [f'move.{suffix} {endpoint_operands}', f'move.{suffix} -(a0),d4']
    source, metadata, artifact, original = _artifact(tmp_path, instructions, width)
    try:
        fields = artifact.query_payload('fields', limit=100)['items']
        assert [f['field_name'] for f in fields if f.get('field_name')] == ['first','second','third','third']
        rows = artifact.addr_window_payload(addr=0, before=0, after=30)[0]['rows']
        outside = next(r for r in rows if endpoint_operands in r.get('text',''))
        assert 'Triplet_' not in outside['text']
    finally:artifact.close()


@pytest.mark.parametrize('suffix,width', [('b', 1), ('w', 2), ('l', 4)])
def test_unsupported_endpoint_postincrement_cannot_recover_a_field_by_backstepping(tmp_path, suffix, width):
    instructions = [f'move.{suffix} (a0)+,d{i}' for i in range(4)]
    instructions += [f'move.{suffix} -(a0),d4', f'move.{suffix} -(a0),d5']
    source, metadata, artifact, original = _artifact(tmp_path, instructions, width)
    try:
        fields = artifact.query_payload('fields', limit=100)['items']
        assert [f['field_name'] for f in fields if f.get('field_name')] == ['first','second','third']
    finally:artifact.close()


def test_last_array_element_one_past_cursor_can_read_its_last_field_again(tmp_path):
    tail = _vasm(tmp_path, 'tail', ' SECTION code,code\n move.w (a0)+,d0\n move.w -(a0),d1\n rts\n').hex()
    fields = _fields(tmp_path, [_seed(addr=32,end=64,field_name='',unit='byte')],target=62,
        instruction_tail=tail,root_fields=[{'name':'first','type':'word','offset':0,'size':2},
                                         {'name':'last','type':'word','offset':14,'size':2}])
    assert [(f['source_offset'],f['field_name']) for f in fields if f.get('field_name')] == [(4,'last'),(6,'last')]
