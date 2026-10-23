"""Compact singleton source labels retain the declared record view."""

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from tests.test_compact_struct_arrays import assert_package_bytes, fixture


@pytest.mark.parametrize('nested', [False, True])
def test_single_record_compact_array_retains_its_declared_type_at_the_label(tmp_path, nested):
    source, original, metadata = fixture(tmp_path, count=1, selected=34, nested=nested)
    assert len(metadata.seeded_entities) == 1
    with effective_metadata_file(tmp_path) as path:
        artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=path)[2]
    try:
        text = artifact.inline_source_text_with_profile()[0]
    finally:
        artifact.close()
    assert 'cells:\t; ARRAY '+('Block' if nested else 'Cell')+'[1]\n' in text
    assert_package_bytes(tmp_path, text, original)


def test_single_expanded_struct_keeps_its_field_annotations(tmp_path):
    source, original, metadata = fixture(tmp_path, count=1, kind='struct', selected=34)
    assert len(metadata.seeded_entities) == 4
    with effective_metadata_file(tmp_path) as path:
        artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=path)[2]
    try:
        text = artifact.inline_source_text_with_profile()[0]
    finally:
        artifact.close()
    assert 'cells:\t; ARRAY Cell[1]' not in text
    assert '; word_0' in text
    assert_package_bytes(tmp_path, text, original)
