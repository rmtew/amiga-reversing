"""Canonical emitted RS fields/SIZEOF are scalars, not invented address owners."""

import subprocess

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_action_catalog import listing_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind as Kind, append_manual_actions, manual_action_log_path
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from tests.test_displacement_symbol import setup_source


def record_actions():
    return [(Kind.CREATE_MANUAL_CUSTOM_STRUCT, {'custom_struct': {
        'name': 'Packet', 'size': 10, 'fields': [
            {'name': 'depth', 'offset': 0, 'size': 2, 'type': 'WORD'},
            {'name': 'radius', 'offset': 2, 'size': 2, 'type': 'WORD'},
            {'name': 'alias', 'offset': 2, 'size': 2, 'type': 'WORD'},
            {'name': 'x', 'offset': 6, 'size': 2, 'type': 'WORD'},
        ]}})]


@pytest.mark.parametrize('instruction,kind,symbol,operand', [
    ('move.w d0,0.w(a1)', 'displacement', 'Packet_depth', 1),
    ('move.w d0,2(a1)', 'displacement', 'Packet_radius', 1),
    ('move.w d0,6(a1,d2.w)', 'indexed_displacement', 'Packet_x', 1),
    ('adda.w #10,a1', 'immediate', 'Packet_SIZEOF', 0),
])
def test_existing_layout_constant_roundtrips_without_equate_proxy(tmp_path, instruction, kind, symbol, operand):
    source, original, row = setup_source(tmp_path, 0, instruction=instruction)
    _, payload = listing_catalog_manual_payload(row, 'representation.symbol',
        element_context={'element_kind': kind, 'operand_index': operand}, parameters={'symbol': symbol})
    append_manual_actions(tmp_path, binary_source=source,
        actions=record_actions() + [(Kind.CREATE_MANUAL_REPRESENTATION, payload)])
    with effective_metadata_file(tmp_path) as path:
        policy = c_backend.effective_policy_project_source_with_c_backend(source, metadata_path=path)["analysis_policy"]
        assert {x['name']: x['value'] for x in policy['layout_constants']} == {
            'Packet_depth': 0, 'Packet_radius': 2, 'Packet_x': 6, 'Packet_SIZEOF': 10}
        assert policy['target_equates'] == []
        text = c_backend.render_project_source_with_c_backend(source, metadata_path=path)
    assert text.count(symbol) == 2  # Single declaration plus actual use.
    assert 'Packet_alias' not in text
    assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text)[0] == original
    asm, output = tmp_path / 'rendered.s', tmp_path / 'oracle.bin'
    asm.write_text(text)
    # vasm otherwise rewrites ADDA.W #constant,An into LEA.
    result = subprocess.run([str(PROJECT_ROOT / 'tools/vasmm68k_mot.exe'), '-no-opt', '-quiet',
        '-Fbin', '-o', str(output), str(asm)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert output.read_bytes() == original


@pytest.mark.parametrize('symbol,value,width', [
    ('Packet_radius', 6, 2), ('Packet_x', 2, 2), ('Packet_radius', 2, 1),
    ('Packet_alias', 2, 2), ('Packet_missing', 2, 2), ('Packet_SIZEOF', 2, 2),
])
def test_missing_nonemitted_or_wrong_value_layout_rejects_atomically(tmp_path, symbol, value, width):
    source, _, _ = setup_source(tmp_path, 2)
    rep = {'representation': {'representation_id': 'bad', 'hunk': 0, 'addr': 0, 'end': 4,
        'style': 'symbol', 'element_kind': 'displacement', 'operand_index': 0,
        'value': value, 'width_bytes': width, 'symbol': symbol}}
    with pytest.raises(ValueError, match='equal-valued canonical EQU'):
        append_manual_actions(tmp_path, binary_source=source,
            actions=record_actions() + [(Kind.CREATE_MANUAL_REPRESENTATION, rep)])
    assert not manual_action_log_path(tmp_path).exists()


def test_layout_renderer_rechecks_value_against_original_operand(tmp_path):
    source, _, row = setup_source(tmp_path, 6)
    _, payload = listing_catalog_manual_payload(row, 'representation.symbol',
        element_context={'element_kind': 'displacement', 'operand_index': 0},
        parameters={'symbol': 'Packet_radius'})
    payload['representation']['value'] = 2  # Forged presentation, decoded bytes still 6.
    append_manual_actions(tmp_path, binary_source=source,
        actions=record_actions() + [(Kind.CREATE_MANUAL_REPRESENTATION, payload)])
    with effective_metadata_file(tmp_path) as path:
        with pytest.raises(RuntimeError):
            c_backend.render_project_source_with_c_backend(source, metadata_path=path)


def test_layout_and_equate_collision_refuses_before_history(tmp_path):
    source, _, row = setup_source(tmp_path, 2)
    _, payload = listing_catalog_manual_payload(row, 'representation.symbol',
        element_context={'element_kind': 'displacement', 'operand_index': 0},
        parameters={'symbol': 'Packet_radius'})
    actions = record_actions() + [(Kind.CREATE_MANUAL_TARGET_EQUATE,
        {'target_equate': {'name': 'Packet_radius', 'value': 2}}),
        (Kind.CREATE_MANUAL_REPRESENTATION, payload)]
    with pytest.raises(ValueError, match='ambiguous canonical layout/EQU'):
        append_manual_actions(tmp_path, binary_source=source, actions=actions)
    assert not manual_action_log_path(tmp_path).exists()


def test_inheritance_does_not_invent_unemitted_child_field_symbols(tmp_path):
    source, _, _ = setup_source(tmp_path, 2)
    actions = record_actions() + [(Kind.CREATE_MANUAL_CUSTOM_STRUCT, {'custom_struct': {
        'name': 'Child', 'size': 12, 'base_struct': 'Packet', 'fields': [
            {'name': 'tail', 'offset': 10, 'size': 2, 'type': 'WORD'}]}})]
    append_manual_actions(tmp_path, binary_source=source, actions=actions)
    with effective_metadata_file(tmp_path) as path:
        policy = c_backend.effective_policy_project_source_with_c_backend(source, metadata_path=path)['analysis_policy']
    constants = {x['name']: x['value'] for x in policy['layout_constants']}
    assert constants['Packet_radius'] == 2 and constants['Child_tail'] == 10
    assert constants['Child_SIZEOF'] == 12 and 'Child_radius' not in constants
    before = manual_action_log_path(tmp_path).read_bytes()
    with pytest.raises(ValueError, match='equal-valued canonical EQU'):
        append_manual_actions(tmp_path, binary_source=source, actions=[(Kind.CREATE_MANUAL_REPRESENTATION,
            {'representation': {'representation_id': 'bad-child', 'hunk': 0, 'addr': 0, 'end': 4,
                'style': 'symbol', 'element_kind': 'displacement', 'operand_index': 0,
                'value': 2, 'width_bytes': 2, 'symbol': 'Child_radius'}})])
    assert manual_action_log_path(tmp_path).read_bytes() == before


def test_immediate_selector_cannot_substitute_its_own_value(tmp_path):
    _, _, row = setup_source(tmp_path, 0, instruction='move.w #10,d0')
    with pytest.raises(ValueError, match='not available'):
        listing_catalog_manual_payload(row, 'representation.symbol',
            element_context={'element_kind': 'immediate', 'operand_index': 0, 'value': 11},
            parameters={'symbol': 'Packet_SIZEOF'})
