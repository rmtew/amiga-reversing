"""Native arbitration must precede ownership conflict export; no target overrides."""

import json

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.target_metadata import (
    SeededEntityMetadata,
    TargetMetadata,
    write_target_metadata,
)
from tests.test_restoration_accounting import REVIEW


@pytest.mark.parametrize("accepted_bitmap", [False, True])
def test_native_terminal_island_retains_arbitration_without_false_storage_conflict(
    tmp_path, accepted_bitmap
):
    text = ' SECTION code,code\n ORG $10000\n rts\nwatch:\n move.w 2(a6),$DFF180.l\n bra.b watch\n dc.b "TEXT",0\n'
    original, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw", text
    )
    assert len(original) == 17
    b = tmp_path / "input.bin"
    b.write_bytes(original)
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=b,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=0x10000,
        entrypoint=0x10000,
        code_start_offset=0,
        display_path=str(b),
        analysis_cache_path=tmp_path / "analysis",
    )
    (tmp_path / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "path": str(b),
                "address_model": "runtime_absolute",
                "load_address": 0x10000,
                "entrypoint": 0x10000,
                "code_start_offset": 0,
            }
        )
    )
    seeds = [
        SeededEntityMetadata(
            addr=12,
            end=17,
            hunk=0,
            type="data",
            subtype="string",
            unit="byte",
            encoding="ascii",
            name="text",
            **REVIEW,
        )
    ]
    if accepted_bitmap:
        seeds.append(
            SeededEntityMetadata(
                addr=2,
                end=12,
                hunk=0,
                type="data",
                subtype="bitmap",
                unit="word",
                name="pixels",
                **REVIEW,
            )
        )
    write_target_metadata(
        tmp_path,
        TargetMetadata(
            target_type="program", entry_register_seeds=(), seeded_entities=tuple(seeds)
        ),
    )
    with effective_metadata_file(tmp_path) as metadata:
        artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=metadata
        )[2]
    try:
        a = artifact.analysis_payload()[0]["sections"][0]
        signals = [s for s in a["orphan_code_signals"] if s["offset"] == 2]
        assert len(signals) == 1
        signal = signals[0]
        assert signal["size"] == 10 and signal["status"] == (
            "suppressed" if accepted_bitmap else "unresolved"
        )
        assert signal["nearby_data_relation"] == (
            "overlap" if accepted_bitmap else "after"
        )
        assert not [r for r in a["range_ownerships"] if r["kind_name"] == "conflict"]
        assert not [b for b in a["blocks"] if 2 <= b["start_offset"] < 12]
        rendered = artifact.source_text_with_profile()[0]
        assert "\tmove.w " not in rendered
        assert (
            c_backend.assemble_platform_source_text_with_c_backend(
                "amiga-raw", rendered
            )[0]
            == original
        )
    finally:
        artifact.close()
