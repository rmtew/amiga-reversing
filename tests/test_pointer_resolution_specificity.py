"""Exact pointer fields retain their native plan decisions under covering ranges."""
import json

import pytest

from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.c_backend import build_listing_artifact_profile_from_binary_source, assemble_platform_source_text_with_c_backend
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, SeededEntityMetadata, TargetMetadataSeedOrigin, TargetMetadataReviewStatus, target_metadata_json_payload
from amiga_reversing.disasm.typed_pointer_report import typed_pointer_report


@pytest.mark.parametrize('reverse', [False, True])
def test_exact_pointer_fields_win_over_covering_table(tmp_path, reverse):
    values = [0x1014, 0x1018, 0x101C, 0]
    original = bytes.fromhex('6010')+b''.join(v.to_bytes(4, 'big') for v in values)+bytes.fromhex('4e75')+bytes(12)
    binary = tmp_path/'input.bin'
    binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x1000, entrypoint=0x1000,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'cache')
    fields = [{'addr': 2+4*i, 'end': 6+4*i, 'hunk': 0, 'unit': 'long',
               'struct_name': 'Reference', 'field_name': 'target', 'field_type': 'long',
               'value_kind': 'target_pointer', 'pointer_address_domain': 'mapped_source'} for i in range(4)]
    broad = {'addr': 2, 'end': 18, 'hunk': 0, 'unit': 'long', 'name': 'covering_table'}
    targets = [{'addr': o, 'end': o+4, 'hunk': 0, 'unit': 'byte', 'name': f'payload_{o}'} for o in [20, 24, 28]]
    entities = ([broad]+fields if not reverse else fields+[broad])+targets
    metadata = target_metadata_json_payload(TargetMetadata(target_type='program', entry_register_seeds=()))
    metadata['seeded_entities'] = entities
    path = tmp_path/'metadata.json'
    path.write_text(json.dumps(metadata))
    _, _, artifact = build_listing_artifact_profile_from_binary_source(source, metadata_path=path, project_root=PROJECT_ROOT)
    try:
        for i, value in enumerate(values):
            row = artifact.row_for_source_offset(section_index=0, offset=2+4*i)
            assert row['start_offset'] == 2+4*i and row['end_offset'] == 6+4*i
            resolution = row['pointer_resolution']
            assert resolution['address_domain'] == 'mapped_source'
            assert resolution['encoded_value'] == value
            assert resolution['outcome'] == ('symbolic' if value else 'null')
            if value:
                assert resolution['target_offset'] == value-0x1000
        report_metadata = TargetMetadata(target_type='program', entry_register_seeds=(), seeded_entities=tuple(
            SeededEntityMetadata(**field, seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
                review_status=TargetMetadataReviewStatus.SEEDED, citation='fixture') for field in fields))
        report = typed_pointer_report(report_metadata, artifact.row_for_source_offset)
        assert report['outcomes'] == {'null': 1, 'symbolic': 3}
        text, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = assemble_platform_source_text_with_c_backend('amiga-raw', text, project_root=PROJECT_ROOT)
        assert rebuilt == original
    finally:
        artifact.close()
