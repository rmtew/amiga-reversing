"""Canonical typed-command references render real differences, without EQU proxies."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
    effective_metadata_text,
)
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_actions,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_base_displacement_integration import _round_trip
from tests.test_c_backend import _requires_c_backend_dlls

pytestmark = pytest.mark.c_backend


@pytest.mark.parametrize("displacement", [-8, 8])
def test_catalog_append_typed_word_label_difference_and_both_assemblers(
    tmp_path: Path, displacement: int,
) -> None:
    _requires_c_backend_dlls()
    original = bytes.fromhex("6012") + bytes(10)
    original += bytes.fromhex("000600300030") + (displacement & 0xFFFF).to_bytes(2, "big")
    original += bytes.fromhex("4e75")
    binary = tmp_path / "repeat.bin"
    binary.write_bytes(original)
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY, path=binary, address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0, entrypoint=0, code_start_offset=0,
        display_path=str(binary), analysis_cache_path=tmp_path / "repeat.analysis",
    )
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    specs = [
        ("target.custom_struct.add", {"name": "RepeatCommand", "size": 8, "fields": [
            {"name": name, "type": "WORD", "offset": offset, "size": 2}
            for offset, name in [(0, "opcode"), (2, "reload_count"), (4, "remaining_count"), (6, "relative_branch")]
        ]}),
        ("target.data_block.layout.create", {"hunk": 0, "source_start": 12, "source_end": 20,
                                              "name": "repeat_command", "default_unit": "word"}),
    ]
    actions = []
    for command, parameters in specs:
        kind, payload = target_catalog_manual_payload(command, parameters=parameters)
        actions.append((ManualActionKind(kind), payload))
    layout_id = actions[1][1]["data_block_layout"]["layout_id"]
    for command, parameters in [
        ("target.data_block.element.set", {"layout_id": layout_id, "offset": 0, "width": 8,
                                            "kind": "struct", "binding_kind": "custom_struct",
                                            "type_id": "RepeatCommand", "name": "command"}),
        ("target.code_label.add", {"hunk": 0, "addr": 12 + displacement, "name": "branch_target"}),
        ("target.data_block.element.interpret_ref", {
            "layout_id": layout_id, "offset": 6, "width": 2, "reference_kind": "base_displacement",
            "signed": True, "scale": 1, "base_locator": {"hunk": 0, "offset": 12},
            "target_hunk": 0, "target_offset": 12 + displacement,
            "source_value": displacement & 0xFFFF,
        }),
    ]:
        kind, payload = target_catalog_manual_payload(command, parameters=parameters)
        actions.append((ManualActionKind(kind), payload))
    append_manual_actions(tmp_path, actions=actions, binary_source=source)
    metadata = json.loads(effective_metadata_text(tmp_path))
    assert not metadata["target_equates"] and not metadata["manual_runtime_address_refs"]
    assert not metadata["manual_representations"]
    assert len(metadata["manual_data_references"]) == 1
    assert metadata["data_block_layouts"][0]["elements"][0]["kind"] == "struct"
    with effective_metadata_file(tmp_path) as metadata_path:
        rendered = c_backend.render_project_source_with_c_backend(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT,
        )
    assert "\tdc.w branch_target-repeat_command" in rendered
    assert "dblk_ref_" not in rendered
    assert "relative_branch" in rendered
    _round_trip(tmp_path, rendered, original)
