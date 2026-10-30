"""Absolute-address literals use the existing durable representation command."""
import pytest

from amiga_reversing.disasm.manual_action_catalog import (
    listing_catalog_manual_payload,
    listing_element_action_catalog,
)


def _row(width=4, value=0x66DC8, symbol=None):
    part = {"kind": "absolute_address", "operand_index": 0, "value": value, "width_bytes": width}
    if symbol:
        part["symbol"] = symbol
    return {"kind": "instruction", "section_index": 0, "start_offset": 0x724A,
            "end_offset": 0x724A + width + 2, "operand_parts": [part]}


@pytest.mark.parametrize(("width", "value"), [(2, 0x1234), (4, 0x1234), (4, 0x66DC8)])
def test_absolute_symbol_command_preserves_decoded_address_provenance(width, value):
    row = _row(width, value)
    context = {"element_kind": "absolute_address", "operand_index": 0, "value": value}
    actions = listing_element_action_catalog(row, context)
    assert [a["action_id"] for a in actions if a["action_id"].startswith("representation.")] == ["representation.symbol"]
    kind, payload = listing_catalog_manual_payload(row, "representation.symbol", element_context=context,
                                                  parameters={"symbol": "generated_mask_bank"})
    assert kind == "create_manual_representation"
    representation = payload["representation"]
    assert representation["symbol"] == "generated_mask_bank"
    assert representation["value"] == value
    assert representation["width_bytes"] == width
    assert representation["operand_index"] == 0


@pytest.mark.parametrize(("width", "value"), [(None, 0x1234), (1, 0x1234), (4, None)])
def test_absolute_symbol_factory_requires_native_literal_and_address_width(width, value):
    row = _row(width, value) if width is not None else _row(0, value)
    with pytest.raises(ValueError, match="not valid for context"):
        listing_catalog_manual_payload(row, "representation.symbol",
            element_context={"element_kind": "absolute_address", "operand_index": 0},
            parameters={"symbol": "generated_mask_bank"})


def test_absolute_symbol_factory_rejects_stale_literal_value():
    with pytest.raises(ValueError, match="not available"):
        listing_catalog_manual_payload(_row(), "representation.symbol",
            element_context={"element_kind": "absolute_address", "operand_index": 0, "value": 0x1234},
            parameters={"symbol": "generated_mask_bank"})


def test_absolute_strong_symbol_has_no_replacement_catalog_command():
    actions = listing_element_action_catalog(_row(symbol="_custom"), {"operand_index": 0})
    assert not any(a["action_id"] == "representation.symbol" for a in actions)


@pytest.mark.parametrize("equate_value", [0x66DC8, 0x66DC9])
def test_candidate_absolute_symbol_checks_whole_batch_before_persistence(tmp_path, equate_value):
    from amiga_reversing.disasm.binary_source import (
        BinarySourceKind,
        RawAddressModel,
        RawBinarySource,
    )
    from amiga_reversing.disasm.manual_actions import (
        ManualActionKind,
        append_manual_actions,
        manual_action_log_path,
    )
    from amiga_reversing.disasm.target_metadata import (
        TargetMetadata,
        write_target_metadata,
    )

    binary = tmp_path / "input.bin"
    binary.write_bytes(bytes.fromhex("43f900066dc84e75"))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / "analysis")
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    row = _row()
    row.update(start_offset=0, end_offset=6)
    _, payload = listing_catalog_manual_payload(row, "representation.symbol",
        element_context={"element_kind": "absolute_address", "operand_index": 0},
        parameters={"symbol": "generated_mask_bank"})
    actions = [(ManualActionKind.CREATE_MANUAL_TARGET_EQUATE,
                {"target_equate": {"name": "generated_mask_bank", "value": equate_value}}),
               (ManualActionKind.CREATE_MANUAL_REPRESENTATION, payload)]
    path = manual_action_log_path(tmp_path)
    if equate_value == 0x66DC8:
        records = append_manual_actions(tmp_path, actions=actions, binary_source=source)
        assert len(records) == 2
        assert path.exists()
    else:
        with pytest.raises(ValueError, match="EQU value must match"):
            append_manual_actions(tmp_path, actions=actions, binary_source=source)
        assert not path.exists()


@pytest.mark.parametrize(("width", "value"), [(2, 0x1234), (4, 0x1234), (4, 0x66DC8)])
def test_real_absolute_symbol_output_preserves_width_and_oracle_bytes(tmp_path, width, value):
    import subprocess

    from amiga_reversing.disasm.binary_source import (
        BinarySourceKind,
        RawAddressModel,
        RawBinarySource,
    )
    from amiga_reversing.disasm.c_backend import (
        assemble_platform_source_text_with_c_backend,
        render_project_source_with_c_backend,
    )
    from amiga_reversing.disasm.effective_metadata import effective_metadata_file
    from amiga_reversing.disasm.manual_actions import (
        ManualActionKind,
        append_manual_actions,
    )
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT
    from amiga_reversing.disasm.target_metadata import (
        TargetMetadata,
        write_target_metadata,
    )

    suffix = 'w' if width == 2 else 'l'
    binary = tmp_path / 'input.bin'
    original, _ = assemble_platform_source_text_with_c_backend('amiga-raw',
        f' SECTION section,code\n ORG 0\n lea.l ${value:X}.{suffix},a1\n rts\n', output_path=binary, project_root=PROJECT_ROOT)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    row = _row(width, value)
    row.update(start_offset=0, end_offset=width + 2)
    _, payload = listing_catalog_manual_payload(row, 'representation.symbol',
        element_context={'element_kind': 'absolute_address', 'operand_index': 0},
        parameters={'symbol': 'generated_mask_bank'})
    append_manual_actions(tmp_path, binary_source=source, actions=[
        (ManualActionKind.CREATE_MANUAL_TARGET_EQUATE, {'target_equate': {'name': 'generated_mask_bank', 'value': value}}),
        (ManualActionKind.CREATE_MANUAL_REPRESENTATION, payload)])
    with effective_metadata_file(tmp_path) as metadata_path:
        rendered = render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
    assert f'lea.l generated_mask_bank.{suffix},a1' in rendered
    rebuilt, _ = assemble_platform_source_text_with_c_backend('amiga-raw', rendered, project_root=PROJECT_ROOT)
    assert rebuilt == original
    rendered_path, output = tmp_path / 'rendered.s', tmp_path / 'oracle.bin'
    rendered_path.write_text(rendered)
    result = subprocess.run([str(PROJECT_ROOT / 'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin',
        '-o', str(output), str(rendered_path)], capture_output=True, text=True, timeout=10, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert output.read_bytes() == original


def test_suppressed_copy_alias_keeps_literal_available_for_canonical_naming(tmp_path):
    """Derived runtime aliases are replaceable; deliberate strong symbols are not."""
    import subprocess
    from amiga_reversing.disasm import c_backend
    from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
    from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
    from amiga_reversing.disasm.effective_metadata import effective_metadata_file
    from amiga_reversing.disasm.listing_context import listing_element_contexts
    from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT

    binary = tmp_path / 'input.bin'
    original, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', ''' SECTION section,code
 lea input(pc),a1
 lea $400.l,a2
 moveq #7,d1
copy: move.l (a1)+,(a2)+
 dbf d1,copy
 lea $400.l,a0
 rts
input: dcb.b 32,0
''', output_path=binary, project_root=PROJECT_ROOT)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x20000, entrypoint=0x20000,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    with effective_metadata_file(tmp_path) as metadata:
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)
        try:
            rendered, _ = artifact.inline_source_text_with_profile()
            assert 'discovered_copy suppressed' in rendered
            assert 'lea.l runtime_code_00000400.l,a0' in rendered
            row = artifact.row_for_source_offset(section_index=0, offset=18)
            element = next(e for e in listing_element_contexts(row) if e['element_kind'] == 'absolute_address')
            assert element['value'] == 0x400
            assert row['operand_parts'][0]['width_bytes'] == 4
            assert 'symbol' not in row['operand_parts'][0]
            kind, payload = listing_catalog_manual_payload(row, 'representation.symbol',
                element_context=element, parameters={'symbol': 'copy_work_start'})
        finally:
            artifact.close()
    append_manual_actions(tmp_path, binary_source=source, actions=[
        (ManualActionKind.CREATE_MANUAL_TARGET_EQUATE, {'target_equate': {'name': 'copy_work_start', 'value': 0x400}}),
        (ManualActionKind(kind), payload)])
    with effective_metadata_file(tmp_path) as metadata:
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)
        try:
            rendered, _ = artifact.inline_source_text_with_profile()
            named_row = artifact.row_for_source_offset(section_index=0, offset=18)
            assert named_row['operand_parts'][0]['symbol'] == 'copy_work_start'
            assert not any(action['action_id'] == 'representation.symbol'
                for action in listing_element_action_catalog(named_row, next(e for e in listing_element_contexts(named_row)
                    if e['element_kind'] == 'symbol' and e.get('symbol') == 'copy_work_start')))
        finally:
            artifact.close()
    assert 'lea.l copy_work_start.l,a0' in rendered
    assert 'discovered_copy suppressed' in rendered  # naming does not promote copied bytes to code
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered)
    assert rebuilt == original
    path, output = tmp_path / 'rendered.s', tmp_path / 'oracle.bin'
    path.write_text(rendered)
    result = subprocess.run([str(PROJECT_ROOT / 'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin',
        '-o', str(output), str(path)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    assert output.read_bytes() == original
