"""End-only owner correction preserves fields/references and refuses data loss."""
import json
import pytest
from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.manual_action_catalog import target_action_catalog, target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_action, append_manual_actions, load_manual_projection
from tests.test_manual_action_log import _write_raw_source
from tests.test_restoration_batch import batch_target as batch_target


@pytest.fixture
def owner(tmp_path):
    _write_raw_source(tmp_path, tmp_path/'binary.bin', b'\0\0\0\x08'+b'\0'*28)
    source = resolve_target_binary_source(tmp_path)
    def append(kind, payload):
        return append_manual_action(tmp_path, kind=ManualActionKind(kind), payload=payload, binary_source=source)
    layout = dict(layout_id='owner', hunk=0, source_start=0, source_end=17,
                  name='record', role='pointer_table', default_unit='long')
    append('create_manual_data_block_layout', {'data_block_layout': layout})
    append('create_manual_custom_struct', {'custom_struct': dict(name='Record', size=4,
        fields=[dict(name='value', type='long', offset=0, size=4, value_kind='scalar')])})
    kind, payload = target_catalog_manual_payload('target.data_block.element.set', dict(
        layout_id='owner', offset=0, width=16, kind='struct', array_count=4,
        array_stride=4, binding_kind='custom_struct', type_id='Record'))
    append(kind, payload)
    append('interpret_manual_data_block_element_ref', {'data_block_interpreted_ref': dict(
        interpreted_ref_id='ref', layout_id='owner', offset=0, width=4,
        reference_kind='absolute', target_hunk=0, target_offset=8, source_value=8,
        target_locator=dict(hunk=0, offset=8))})
    return tmp_path, source, append, layout


def resize(end=16, expected=17, identity='owner'):
    return target_catalog_manual_payload('target.data_block.layout.resize', dict(
        layout_id=identity, source_end=end, expected_source_end=expected))


def test_resize_catalog_is_explicit_end_only():
    action = next(a for a in target_action_catalog() if a['action_id']=='target.data_block.layout.resize')
    assert action['parameter_schema']['additionalProperties'] is False
    assert resize()==('resize_manual_data_block_layout', {
        'data_block_layout': {'layout_id':'owner','source_end':16}, 'expected_source_end':17})


@pytest.mark.parametrize('params', [dict(layout_id='',source_end=16,expected_source_end=17),
    dict(layout_id='owner',source_end=True,expected_source_end=17),
    dict(layout_id='owner',source_end=16,expected_source_end=False),
    dict(layout_id='owner',source_end=-1,expected_source_end=17)])
def test_resize_bad_parameters(params):
    with pytest.raises(ValueError):target_catalog_manual_payload('target.data_block.layout.resize', params)


def test_resize_preserves_bound_fields_refs_identity_and_undo_redo(owner):
    directory, source, append, layout = owner
    before=load_manual_projection(directory,binary_source=source)
    log=directory/'manual_actions.jsonl';prefix=log.read_bytes()
    kind,payload=resize();action=append(kind,payload)
    after=load_manual_projection(directory,binary_source=source)
    assert after.data_block_layouts==({**layout,'source_end':16},)
    assert after.data_block_elements==before.data_block_elements
    assert after.data_block_interpreted_refs==before.data_block_interpreted_refs
    assert after.custom_structs==before.custom_structs
    # Offline replay uses the same source identity bound into the log header.
    assert load_manual_projection(directory).data_block_layouts==after.data_block_layouts
    append('undo_action', {'undoes_action_id':action['action_id']})
    assert load_manual_projection(directory,binary_source=source).data_block_layouts==(layout,)
    append('redo_action', {'redoes_action_id':action['action_id']})
    assert load_manual_projection(directory,binary_source=source).data_block_layouts==after.data_block_layouts
    assert log.read_bytes().startswith(prefix)


@pytest.mark.parametrize('end,expected,identity,message', [
    (15,17,'owner','truncate'), (0,17,'owner','positive integer'),
    (33,17,'owner','source bounds'), (16,18,'owner','stale'),
    (17,17,'owner','changed integer'), (16,17,'missing','active owner')])
def test_resize_refusals_do_not_append(owner,end,expected,identity,message):
    directory,source,append,_=owner;log=directory/'manual_actions.jsonl';prefix=log.read_bytes()
    with pytest.raises(ValueError,match=message):
        kind,payload=resize(end,expected,identity);append(kind,payload)
    assert log.read_bytes()==prefix


def test_resize_expansion_checks_bounds_and_conflicts(owner):
    directory,source,append,layout=owner
    append('create_manual_data_block_layout',{'data_block_layout':dict(
        layout_id='next',hunk=0,source_start=20,source_end=24)})
    log=directory/'manual_actions.jsonl';prefix=log.read_bytes()
    with pytest.raises(ValueError,match='overlaps'):
        kind,payload=resize(21);append(kind,payload)
    assert log.read_bytes()==prefix
    kind,payload=resize(20);append(kind,payload)
    assert load_manual_projection(directory,binary_source=source).data_block_layouts[0]['source_end']==20


def test_failed_batch_keeps_history_atomic(owner):
    directory,source,append,_=owner;log=directory/'manual_actions.jsonl';prefix=log.read_bytes()
    a=resize();b=resize(15,16)
    with pytest.raises(ValueError,match='truncate'):
        append_manual_actions(directory,actions=[(ManualActionKind(k),p) for k,p in [a,b]],binary_source=source)
    assert log.read_bytes()==prefix


def test_resize_refuses_unsupported_coordinate_views(owner):
    directory,source,append,_=owner
    append('create_manual_data_block_layout',{'data_block_layout':dict(
        layout_id='mapped',hunk=0,source_start=20,source_end=24,runtime_start=100,runtime_end=104)})
    log=directory/'manual_actions.jsonl';prefix=log.read_bytes()
    with pytest.raises(ValueError,match='without a runtime view'):
        kind,payload=resize(23,24,'mapped');append(kind,payload)
    assert log.read_bytes()==prefix


def test_resize_shared_service_checks_revision_before_append(batch_target, monkeypatch):
    from types import SimpleNamespace
    from amiga_reversing.disasm import restoration, server
    from tests.test_restoration_batch import invoke
    directory=batch_target.directory
    _write_raw_source(directory,directory/'binary.bin',b'\x4e\x75'+b'\0'*30)
    source=resolve_target_binary_source(directory)
    monkeypatch.setattr(server,'resolve_project_paths',lambda *a,**kw:SimpleNamespace(target_dir=directory,binary_source=source))
    append_manual_action(directory,kind=ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT,
        payload={'data_block_layout':dict(layout_id='owner',hunk=0,source_start=2,source_end=17)},binary_source=source)
    entry=dict(command_id='target.data_block.layout.resize',context={'kind':'target'},
        parameters=dict(layout_id='owner',expected_source_end=17,source_end=16),
        evidence={'reason':'Synthetic correction of unowned suffix; preserve identity.',
                  'source_evidence_refs':['s0:00000000:instruction']})
    revision=restoration.revisions('bloodwych')['revision']
    result=invoke(batch_target,entries=[entry],revision=revision)
    assert result['actions'][0]['kind']=='resize_manual_data_block_layout'
    assert load_manual_projection(directory,binary_source=source).data_block_layouts[0]['source_end']==16
    prefix=(directory/'manual_actions.jsonl').read_bytes()
    with pytest.raises(ValueError,match='stale_revision'):
        invoke(batch_target,entries=[entry],revision=revision)
    assert (directory/'manual_actions.jsonl').read_bytes()==prefix


def test_resize_refuses_hunk_source_without_claiming_section_bounds(batch_target):
    directory=batch_target.directory;source=batch_target.source
    append_manual_action(directory,kind=ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT,
        payload={'data_block_layout':dict(layout_id='owner',hunk=1,source_start=0,source_end=4)},binary_source=source)
    log=directory/'manual_actions.jsonl';prefix=log.read_bytes()
    kind,payload=resize(3,4)
    with pytest.raises(ValueError,match='raw source section 0'):
        append_manual_action(directory,kind=ManualActionKind(kind),payload=payload,binary_source=source)
    assert log.read_bytes()==prefix


def test_resize_preserves_reference_even_after_legacy_element_replacement(owner):
    directory,source,append,_=owner
    append('interpret_manual_data_block_element_ref', {'data_block_interpreted_ref':dict(
        interpreted_ref_id='tail',layout_id='owner',offset=12,width=4,
        reference_kind='absolute',target_hunk=0,target_offset=0,source_value=0,
        target_locator=dict(hunk=0,offset=0))})
    # An existing interpreted leaf can outlive replacement of its containing
    # element. Resize must guard the reference itself, not only current fields.
    kind,payload=target_catalog_manual_payload('target.data_block.element.set',dict(
        layout_id='owner',offset=0,width=8,kind='array',array_count=2,array_stride=4))
    append(kind,payload)
    log=directory/'manual_actions.jsonl';prefix=log.read_bytes()
    kind,payload=resize(8)
    with pytest.raises(ValueError,match='owned reference'):
        append(kind,payload)
    assert log.read_bytes()==prefix


def test_dependent_target_binding_uses_current_metadata_and_revision(batch_target, monkeypatch):
    from types import SimpleNamespace
    from amiga_reversing.disasm import restoration, server
    from tests.test_restoration_batch import invoke
    directory=batch_target.directory
    _write_raw_source(directory,directory/'binary.bin',b'\x4e\x75'+b'\0'*30)
    source=resolve_target_binary_source(directory)
    monkeypatch.setattr(server,'resolve_project_paths',lambda *a,**kw:SimpleNamespace(target_dir=directory,binary_source=source))
    append_manual_action(directory,kind=ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT,
        payload={'data_block_layout':dict(layout_id='owner',hunk=0,source_start=2,source_end=17)},binary_source=source)
    revision=restoration.revisions('bloodwych')['revision']
    changed=invoke(batch_target,entries=[dict(command_id='target.data_block.layout.resize',context={'kind':'target'},
        parameters=dict(layout_id='owner',expected_source_end=17,source_end=16),
        evidence=dict(reason='Correct a known raw owner endpoint.',evidence_refs=['s0:00000000:instruction']))],revision=revision)
    # Refresh the canonical owner, rather than reusing a stale native locator.
    inspected=load_manual_projection(directory,binary_source=source).data_block_layouts[0]
    assert inspected['source_end']==16
    result=restoration.execute('bloodwych',dict(operation='command',expected_revision=changed['revision'],
        command_id='target.data_block.element.set',context={'kind':'target'},
        parameters=dict(layout_id=inspected['layout_id'],offset=0,width=14,kind='array',array_count=14,array_stride=1),
        interpretation=dict(source_evidence_status='hypothesis',reason='Bind refreshed canonical owner after resize.')))
    assert load_manual_projection(directory,binary_source=source).data_block_elements[0]['width']==14
    prefix=(directory/'manual_actions.jsonl').read_bytes()
    with pytest.raises(ValueError,match='stale_revision'):
        restoration.execute('bloodwych',dict(operation='command',expected_revision=changed['revision'],
            command_id='target.data_block.element.set',context={'kind':'target'},
            parameters=dict(layout_id='owner',offset=0,width=15,kind='array',array_count=15,array_stride=1)))
    assert (directory/'manual_actions.jsonl').read_bytes()==prefix
