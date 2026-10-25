"""Declared relative WORD relations may name owned code, never just a label."""
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_base_displacement_integration import _round_trip
from tests.test_c_backend import _requires_c_backend_dlls

pytestmark = pytest.mark.c_backend


def _fixture(tmp_path: Path, load: int, second: str):
    _requires_c_backend_dlls()
    value = 8 if second == "unaccepted" else 6
    tail = "303c12344e75" if second == "interior" else "4e754e754e75"
    original = bytes.fromhex("60040004") + value.to_bytes(2, "big") + bytes.fromhex(tail)
    path = tmp_path / "code-table.bin"
    path.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=load,
        entrypoint=load, code_start_offset=0, display_path=str(path),
        analysis_cache_path=tmp_path / "binary.analysis")
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    specs = [
        ("target.data_block.layout.create", dict(hunk=0, source_start=2, source_end=6,
                                                name="offset_words", default_unit="word")),
        ("target.code_label.add", dict(hunk=0, addr=6, name="routine_a")),
    ]
    if second != "interior":
        specs += [("target.code.seed", dict(hunk=0, addr=8, name="routine_b")),
                  ("target.code_label.add", dict(hunk=0, addr=10, name="not_code"))]
    actions, layout_id = [], None
    for command, params in specs:
        kind, payload = target_catalog_manual_payload(command, parameters=params)
        actions.append((ManualActionKind(kind), payload))
        if command.endswith("layout.create"):
            layout_id = payload["data_block_layout"]["layout_id"]
    for command, params in [
        ("target.data_block.element.set", dict(layout_id=layout_id, offset=0, width=4,
            kind="array", array_count=2, array_stride=2)),
        ("target.data_block.element.interpret_ref", dict(layout_id=layout_id, offset=0,
            width=4, reference_kind="base_displacement_range", signed=True, scale=1,
            base_locator={"hunk": 0, "offset": 2}, target_hunk=0, target_offset=6,
            source_value=4)),
    ]:
        kind, payload = target_catalog_manual_payload(command, parameters=params)
        actions.append((ManualActionKind(kind), payload))
    append_manual_actions(tmp_path, actions=actions, binary_source=source)
    with effective_metadata_file(tmp_path) as metadata_path:
        rendered = c_backend.render_project_source_with_c_backend(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
    return original, rendered


@pytest.mark.parametrize("load", [0, 0x1000])
@pytest.mark.parametrize("second", ["accepted", "unaccepted", "interior"])
def test_relative_code_targets_require_accepted_instruction_starts(tmp_path, load, second):
    original, rendered = _fixture(tmp_path, load, second)
    assert "routine_a-offset_words" in rendered
    relations = [line for line in rendered.splitlines()
                 if line.lstrip().startswith("dc.w ") and "-offset_words" in line]
    if second == "accepted":
        assert len(relations) == 2
    elif second == "unaccepted":
        assert len(relations) == 1
        assert "not_code-offset_words" not in rendered
        assert "$0008" in rendered
    else:
        assert len(relations) == 1
        assert "$0006" in rendered
    _round_trip(tmp_path, rendered, original)
