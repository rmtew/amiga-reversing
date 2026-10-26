"""Declared app fields and access records share guarded fallback admission."""
import json

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource


@pytest.mark.c_backend
@pytest.mark.parametrize('case', [
    'declared', 'declared_second', 'declared_suboffset', 'overrun_suboffset', 'declared_write', 'declared_readwrite', 'declared_address', 'undeclared', 'partial', 'other_register', 'hardware',
    'relative_hardware', 'relative_added', 'loaded_value', 'relative_then_unknown', 'other_layout', 'noncustom_fallback', 'seeded_app', 'seeded_app_after_hardware', 'seeded_data_after_word', 'seeded_app_a5', 'seeded_other_layout', 'seeded_hardware',
])
def test_app_access_catalogue_preserves_base_evidence_and_hardware_boundary(tmp_path, case):
    prefix = (' lea.l $DFF000.l,a6\n' if case == 'hardware' else
              ' lea.l $DFF040.l,a6\n' if case in ['relative_hardware', 'seeded_app_after_hardware'] else
              ' lea.l $DFF000.l,a6\n adda.w #$40,a6\n' if case == 'relative_added' else
              ' movea.l $DFF040.l,a6\n' if case == 'loaded_value' else
              ' lea.l $DFF040.l,a6\n movea.l (a0),a6\n' if case == 'relative_then_unknown' else
              ' lea.l $DFF000.l,a6\n moveq #64,d0\n adda.w d0,a6\n' if case == 'seeded_data_after_word' else '')
    reg = 'a5' if case in ['other_register', 'seeded_app_a5'] else 'a6'
    offset = 0x742 if case == 'noncustom_fallback' else 0x192 if case in ['declared_second', 'declared_suboffset', 'overrun_suboffset'] else 0x190
    operand = f'${offset:04X}({reg})'
    operation = (f'move.w d0,{operand}' if case == 'declared_write' else
                 f'addq.w #1,{operand}' if case == 'declared_readwrite' else
                 f'lea.l {operand},a0' if case == 'declared_address' else
                 f'move.w {operand},d0')
    asm = f' SECTION code,code\n ORG $1000\n{prefix} {operation}\n rts\n'
    original, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', asm)
    binary = tmp_path / 'input.bin'
    binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x1000,
        entrypoint=0x1000, code_start_offset=0, display_path=str(binary),
        analysis_cache_path=tmp_path/'analysis')
    regions = [] if case == 'undeclared' else [dict(offset=0x190 if case in ['declared_suboffset', 'overrun_suboffset'] else offset,
        size=1 if case == 'partial' else 4 if case == 'declared_suboffset' else 3 if case == 'overrun_suboffset' else 2, symbol='declared_state',
        layout_name='work' if case in ['other_layout', 'seeded_other_layout'] else 'app',
        base_symbol='__work_base__' if case in ['other_layout', 'seeded_other_layout'] else '__amiga_app_base__',
        storage_kind='scalar')]
    metadata = tmp_path/'metadata.json'
    seeds = []
    if case.startswith('seeded'):
        seeds = [dict(entry_offset=6 if case == 'seeded_app_after_hardware' else 8 if case == 'seeded_data_after_word' else 0, hunk=0, register='D0' if case == 'seeded_data_after_word' else reg.upper(), kind='library_base',
            library_name='__work_base__' if case == 'seeded_other_layout' else '_custom' if case == 'seeded_hardware' else '__amiga_app_base__')]
    metadata.write_text(json.dumps(dict(rsset_layout_regions=regions, entry_register_seeds=seeds)))
    art = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)[2]
    try:
        analysis = art.analysis_payload()[0]
        text = art.source_projection_with_profile()[0]
        matching = [r for r in analysis['sections'][0]['app_slot_refs'] if r['displacement'] == offset]
        row_refs = [art.row_for_source_offset(section_index=0, offset=r['offset'])['app_slot_refs'] for r in matching]
    finally:
        art.close()
    refs = [r for r in analysis['sections'][0]['app_slot_refs'] if r['displacement'] == offset]
    if case.startswith('declared') or case in ['noncustom_fallback', 'loaded_value', 'relative_then_unknown', 'seeded_app', 'seeded_app_after_hardware', 'seeded_data_after_word', 'seeded_app_a5']:
        assert len(refs) == 1
        assert refs[0]['access'] == dict(declared_write='write', declared_readwrite='read-write', declared_address='address').get(case, 'read')
        assert refs[0]['base_register'] == reg.upper()
        assert refs[0]['base_evidence'] == ('register_state' if case.startswith('seeded') and case != 'seeded_data_after_word' else 'declared_layout_a6_fallback' if case != 'noncustom_fallback' else 'a6_fallback')
        if case != 'declared_suboffset':
            assert f'declared_state({reg})' in text
        assert all(any(item['base_evidence'] == refs[0]['base_evidence'] for item in row) for row in row_refs)
    else:
        assert refs == []
        if case != 'seeded_other_layout':
            assert 'declared_state(' not in text
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text,
        include_dir=PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include')
    assert rebuilt == original
