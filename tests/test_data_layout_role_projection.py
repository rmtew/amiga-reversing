import pytest

from amiga_reversing.disasm.effective_metadata import _data_block_element_entity
from amiga_reversing.disasm.target_metadata import (
    DataBlockLayoutMetadata, DataBlockElementMetadata, DataBlockElementKind,
    TargetMetadataSeedOrigin, TargetMetadataReviewStatus,
)


@pytest.mark.parametrize("role, subtype", [
    ("sound_sample", "sound_sample"), ("lookup_table", "lookup_table"),
    ("Amiga startup fills 200 WORD offsets with stride 40", None),
    (None, None),
])
def test_data_layout_prose_is_preserved_without_becoming_native_subtype(role, subtype):
    fields = dict(seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED, citation="test")
    layout = DataBlockLayoutMetadata(layout_id="table", hunk=0,
        source_start=2, source_end=10, name="table", role=role,
        default_unit="word", **fields)
    element = DataBlockElementMetadata(layout_id="table", offset=0, width=8,
        kind=DataBlockElementKind.ARRAY, array_count=4, array_stride=2, **fields)
    entity = _data_block_element_entity(layout, element)
    assert entity.subtype == subtype
    assert entity.comment == role
    assert entity.unit == "word"
