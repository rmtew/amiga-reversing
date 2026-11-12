"""Generated single-pointer field roles repeat only at visible boundaries."""
import pytest

from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind as Kind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_typed_pointer_domains import _assert_vasm_bytes


@pytest.mark.parametrize('case', ['plain', 'custom_field', 'one', 'label', 'authored', 'same_text', 'two_owners', 'two_fields', 'different_format'])
def test_pointer_field_comments_preserve_boundaries_and_authored_text(tmp_path, case):
    count = 1 if case == 'one' else 6 if case == 'two_fields' else 3
    raw = bytes.fromhex('4e75') + (4096 + 2 + 4 * count).to_bytes(4, 'big') * count + b'ABC\0'
    path = tmp_path / 'input.bin'; path.write_bytes(raw)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=4096, entrypoint=4096,
        code_start_offset=0, display_path=str(path), analysis_cache_path=tmp_path / 'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    actions = []
    def add(command, parameters):
        kind, payload = target_catalog_manual_payload(command, parameters)
        actions.append((Kind(kind), payload))
        return payload
    role = 'destination' if case == 'custom_field' else 'text'
    fields = [dict(name=role, type='APTR', offset=0, size=4, value_kind='target_pointer', pointer_address_domain='mapped_source')]
    if case == 'two_fields':
        fields.append(dict(fields[0], name='other_text', offset=4))
    width = 8 if case == 'two_fields' else 4
    add('target.custom_struct.add', dict(name='Cell', size=width, fields=fields))
    if case == 'different_format':
        add('target.custom_struct.add', dict(name='Other', size=4, fields=fields))
    def owner(start, end, name, type_id='Cell'):
        layout = add('target.data_block.layout.create', dict(hunk=0, source_start=start,
            source_end=end, name=name, role='pointer_table', default_unit='long'))['data_block_layout']['layout_id']
        add('target.data_block.element.set', dict(layout_id=layout, offset=0, width=end-start,
            kind='array', name=name, array_count=(end-start)//width, array_stride=width,
            binding_kind='custom_struct', type_id=type_id))
    if case in ['two_owners', 'different_format']:
        owner(2, 6, 'first')
        owner(6, 14, 'second', 'Other' if case == 'different_format' else 'Cell')
    else:
        owner(2, 2+4*count, 'references')
    if case == 'label':
        add('target.data.name', dict(hunk=0, addr=6, name='selected_reference'))
    if case in ['authored', 'same_text']:
        actions.append((Kind.CREATE_MANUAL_COMMENT, {'comment': dict(comment_id='authored', hunk=0,
            addr=6, text='text' if case == 'same_text' else 'Keep this "quoted; annotation".')}))
    add('target.string.seed', dict(hunk=0, addr=2+4*count, end=len(raw), name='message'))
    append_manual_actions(tmp_path, binary_source=source, actions=actions)
    with effective_metadata_file(tmp_path) as metadata:
        artifact = cb.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)[2]
    try:
        text = artifact.inline_source_text_with_profile()[0]
        package = artifact.source_package_payload(64)
        rows = [line for line in text.splitlines() if line.lstrip().startswith('dc.l')]
        assert len(rows) == count and all('message' in row for row in rows)
        annotated = [row for row in rows if '\t; ' + role in row]
        expected = 3 if case in ['two_fields', 'authored', 'same_text'] else 2 if case in ['label', 'two_owners', 'different_format'] else 1
        assert len(annotated) == expected, text
        if case == 'two_fields':
            assert sum('\t; other_text' in row for row in rows) == 3
        if case == 'authored':
            assert 'Keep this "quoted; annotation".' in text
        if case == 'same_text':
            assert sum(line.strip() == '; text' for line in text.splitlines()) == 1
        assert package['source_text'] == text
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw', text)[0] == raw
        _assert_vasm_bytes(tmp_path, text, raw)
    finally:
        artifact.close()
