"""SDK constants need no prior rendered declaration to name a literal."""

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.listing_context import listing_element_contexts
from amiga_reversing.disasm.manual_action_catalog import listing_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_actions,
    manual_action_log_path,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def literal_fixture(tmp_path, value):
    binary = tmp_path / "literal.bin"
    original, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        f" SECTION code,code\n ORG 0\n move.w #{value},d0\n rts\n",
        output_path=binary,
    )
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(binary),
        analysis_cache_path=tmp_path / "analysis",
    )
    write_target_metadata(
        tmp_path, TargetMetadata(target_type="program", entry_register_seeds=())
    )
    return source, original


@pytest.mark.parametrize(
    ("symbol", "value"),
    [
        ("INTB_BLIT", 6),
        ("INTF_BLIT", 64),
        ("INTB_TBE", 0),
        ("NO_SUCH_PLATFORM_CONSTANT", None),
    ],
)
def test_native_registry_resolves_unused_and_zero_constants(tmp_path, symbol, value):
    source, _ = literal_fixture(tmp_path, 6)
    assert c_backend.platform_constant_value_with_c_backend(source, symbol) == value


@pytest.mark.parametrize(
    ("symbol", "value", "accepted"),
    [
        ("INTB_BLIT", 6, True),
        ("INTF_BLIT", 64, True),
        ("INTB_TBE", 0, True),
        ("INTB_BLIT", 7, False),
    ],
)
def test_normal_literal_command_accepts_matching_sdk_values_before_append(
    tmp_path, symbol, value, accepted
):
    source, original = literal_fixture(tmp_path, value)
    artifact = c_backend.build_listing_artifact_profile_from_binary_source(source)[2]
    try:
        assert artifact.query_payload("symbols", symbol=symbol, limit=2)["total"] == 0
        row = next(
            r
            for r in artifact.addr_window_payload(addr=0, before=0, after=4)[0]["rows"]
            if r["kind"] == "instruction" and r["start_offset"] == 0
        )
        element = next(
            e for e in listing_element_contexts(row) if e["element_kind"] == "immediate"
        )
        kind, payload = listing_catalog_manual_payload(
            row,
            "representation.symbol",
            element_context=element,
            parameters={"symbol": symbol},
        )
    finally:
        artifact.close()
    path = manual_action_log_path(tmp_path)
    before = path.read_bytes() if path.exists() else None
    if not accepted:
        with pytest.raises(ValueError, match="platform symbol constant must match"):
            append_manual_actions(
                tmp_path,
                binary_source=source,
                actions=[(ManualActionKind(kind), payload)],
            )
        assert (path.read_bytes() if path.exists() else None) == before
        return
    append_manual_actions(
        tmp_path, binary_source=source, actions=[(ManualActionKind(kind), payload)]
    )
    with effective_metadata_file(tmp_path) as metadata:
        rendered = c_backend.render_project_source_with_c_backend(
            source, metadata_path=metadata
        )
    assert f"move.w #{symbol},d0" in rendered
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        rendered,
        include_dir=PROJECT_ROOT / "ext/amiga_includes/ndk_2.0/include",
    )
    assert rebuilt == original
