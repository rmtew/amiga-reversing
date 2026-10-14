"""Real native rendering and queries for source-owned signed table words."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing import reversing_loop
from amiga_reversing.disasm import c_backend, server
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
    effective_metadata_text,
)
from amiga_reversing.disasm.manual_action_catalog import _data_block_element_ref_payload
from amiga_reversing.disasm.manual_actions import MANUAL_ACTION_LOG_FILE_NAME
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.projects import ProjectKind
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_c_backend import _requires_c_backend_dlls

pytestmark = pytest.mark.c_backend


def _fixture(tmp_path: Path, base: int = 8, target: int = 12,
             mode: str = "bidirectional", cleanup: str | None = None,
             overlap: bool = False) -> tuple[RawBinarySource, bytes, dict[str, object]]:
    _requires_c_backend_dlls()
    encoded = (target - base) & 0xFFFF
    original = bytes.fromhex("6002") + encoded.to_bytes(2, "big") + bytes.fromhex("4e75")
    original += bytes(max(base, target) + 2 - len(original))
    path = tmp_path / "displacements.bin"
    path.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=path,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(path), analysis_cache_path=tmp_path / "binary.analysis")
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    ref = _data_block_element_ref_payload([], {
        "layout_id": "relative-table", "offset": 0, "width": 2,
        "reference_kind": "base_displacement", "signed": True, "scale": 1,
        "base_locator": {"hunk": 0, "offset": base}, "target_hunk": 0,
        "target_offset": target, "source_value": encoded, "xref_generation_mode": mode,
    })
    actions: list[tuple[str, str, dict[str, object]]] = [
        ("create_manual_data_block_layout", "data_block_layout", {
            "layout_id": "relative-table", "hunk": 0, "source_start": 2,
            "source_end": 4, "default_unit": "word"}),
        ("set_manual_data_block_element", "data_block_element", {
            "layout_id": "relative-table", "offset": 0, "width": 2, "kind": "scalar"}),
    ]
    for name, offset in [("base_anchor", base), *([] if base == target else [("target_anchor", target)])]:
        actions.append(("create_manual_label", "label", {
            "label_id": name, "scope": "global", "hunk": 0, "addr": offset, "name": name}))
    if overlap:
        actions.append(("create_manual_representation", "representation", {
            "representation_id": "numeric-word", "hunk": 0, "addr": 2, "end": 4,
            "style": "hex", "element_kind": "operand"}))
    # Repeating the same accepted fact must not duplicate native relations.
    actions.extend([("interpret_manual_data_block_element_ref", "data_block_interpreted_ref", ref)] * 2)
    if cleanup == "reference":
        actions.append(("remove_manual_data_block_element_ref", "data_block_interpreted_ref", {
            "data_block_ref_id": ref["data_block_ref_id"], "layout_id": "relative-table", "offset": 0}))
    elif cleanup == "element":
        actions.append(("remove_manual_data_block_element", "data_block_element", {
            "layout_id": "relative-table", "offset": 0}))
    elif cleanup == "layout":
        actions.append(("remove_manual_data_block_layout", "data_block_layout", {"layout_id": "relative-table"}))
    records = [{"record": "manual_action_log_header", "version": 1, "target_identity": {}}]
    records.extend({"record": "manual_action", "action_id": f"a{i}", "sequence": i,
                    "created_at": "2026-10-13T00:00:00+00:00", "kind": kind, key: payload}
                   for i, (kind, key, payload) in enumerate(actions, 1))
    (tmp_path / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        "\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    return source, original, ref


def _owned(artifact: object, offset: int, direction: str) -> list[dict[str, object]]:
    payload = artifact.query_payload("references", section_index=0, source_offset=offset, direction=direction)
    return [item for item in payload["items"] if item.get("owner_kind") == "data_block_interpreted_ref"]


def _round_trip(tmp_path: Path, rendered: str, original: bytes) -> None:
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw", rendered, project_root=PROJECT_ROOT)
    assert rebuilt == original
    # Independent oracle: assemble the exact emitted source, including label arithmetic.
    vasm = PROJECT_ROOT / "tools" / "vasmm68k_mot.exe"
    assert vasm.exists(), "round-trip verification requires the repository vasm oracle"
    source_path = tmp_path / "rendered.s"
    output_path = tmp_path / "vasm.bin"
    source_path.write_text(rendered, encoding="utf-8")
    result = subprocess.run([str(vasm), "-Fbin", "-quiet", "-o", str(output_path), str(source_path)],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert output_path.read_bytes() == original


@pytest.mark.parametrize(("base", "target"), [(8, 12), (12, 8), (8, 8), (9, 32776), (32776, 8)])
def test_real_backend_signed_word_expression_and_independent_round_trip(
        tmp_path: Path, base: int, target: int) -> None:
    source, original, ref = _fixture(tmp_path, base, target)
    metadata = json.loads(effective_metadata_text(tmp_path))
    native, = metadata["manual_data_references"]
    assert native["source_value"] == ref["source_value"]
    assert not metadata["target_equates"] and not metadata["manual_runtime_address_refs"]
    assert not metadata["manual_representations"]
    with effective_metadata_file(tmp_path) as metadata_path:
        rendered = c_backend.render_project_source_with_c_backend(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
    target_name = "base_anchor" if base == target else "target_anchor"
    assert f"\tdc.w {target_name}-base_anchor\n" in rendered
    assert "dblk_ref_" not in rendered
    assert "base_anchor:" in rendered
    if base != target:
        assert "target_anchor:" in rendered
    _round_trip(tmp_path, rendered, original)


@pytest.mark.parametrize(("mode", "base", "target"), [
    ("bidirectional", 8, 12), ("source_only", 8, 12), ("none", 8, 12), ("bidirectional", 8, 8),
])
def test_real_backend_query_preserves_both_expression_roles_and_owner(
        tmp_path: Path, mode: str, base: int, target: int) -> None:
    source, _, ref = _fixture(tmp_path, base=base, target=target, mode=mode)
    with effective_metadata_file(tmp_path) as metadata_path:
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        try:
            outgoing = _owned(artifact, 2, "outgoing")
            assert len(outgoing) == (0 if mode == "none" else 2)
            assert {item["reference_role"] for item in outgoing} == (set() if mode == "none" else {"base", "target"})
            for item in outgoing:
                assert item["source_offset"] == 2
                assert item["target_section_index"] == 0
                assert item["target_offset"] == (base if item["reference_role"] == "base" else target)
                assert item["reference_kind"] == "base_displacement"
                assert item["source_value"] == (target - base) & 0xFFFF
                assert item["width"] == 2 and item["signed"] is True
                assert item["base_section_index"] == 0 and item["base_offset"] == base
                assert item["owner_id"] == ref["data_block_ref_id"]
                assert item["owner_layout_id"] == "relative-table" and item["owner_element_offset"] == 0
                assert item["xref_generation_mode"] == mode
            for offset in {base, target}:
                incoming = _owned(artifact, offset, "incoming")
                roles = ({"base"} if offset == base else set()) | ({"target"} if offset == target else set())
                assert len(incoming) == (len(roles) if mode == "bidirectional" else 0)
                assert {item["reference_role"] for item in incoming} == (roles if mode == "bidirectional" else set())
            row = artifact.row_for_source_offset(section_index=0, offset=2)
            assert row is not None
            assert not [item for item in row.get("runtime_address_refs", [])
                        if item.get("owner_kind") == "data_block_interpreted_ref"]
        finally:
            artifact.close()


@pytest.mark.parametrize("cleanup", ["reference", "element", "layout"])
def test_real_backend_cleanup_removes_expression_and_owned_queries(tmp_path: Path, cleanup: str) -> None:
    source, original, _ = _fixture(tmp_path, cleanup=cleanup)
    assert not json.loads(effective_metadata_text(tmp_path))["manual_data_references"]
    with effective_metadata_file(tmp_path) as metadata_path:
        rendered = c_backend.render_project_source_with_c_backend(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        try:
            assert not _owned(artifact, 2, "outgoing")
            assert not _owned(artifact, 8, "incoming")
            assert not _owned(artifact, 12, "incoming")
        finally:
            artifact.close()
    assert "target_anchor-base_anchor" not in rendered
    _round_trip(tmp_path, rendered, original)


def test_real_backend_semantic_reference_overrides_numeric_representation(tmp_path: Path) -> None:
    source, original, _ = _fixture(tmp_path, overlap=True)
    with effective_metadata_file(tmp_path) as metadata_path:
        rendered = c_backend.render_project_source_with_c_backend(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
    assert rendered.count("\tdc.w target_anchor-base_anchor\n") == 1
    _round_trip(tmp_path, rendered, original)


def test_target_command_validates_bytes_and_labels_against_real_native_artifact(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source, _, ref = _fixture(tmp_path, base=12, target=8)
    monkeypatch.setattr(server, "get_project", lambda _: SimpleNamespace(
        kind=ProjectKind.BINARY, ready=True, target_dir=str(tmp_path)))
    with effective_metadata_file(tmp_path) as metadata_path:
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        try:
            monkeypatch.setattr(server, "_valid_c_listing_artifact", lambda _: artifact)
            result = server._prepare_manual_action_command(
                "synthetic", "target.data_block.element.interpret_ref", {"kind": "target"}, [], ref)
            assert result == [("interpret_manual_data_block_element_ref", {"data_block_interpreted_ref": ref})]
        finally:
            artifact.close()


@pytest.mark.parametrize("remove_array", [False, True])
def test_real_backend_preserves_six_reference_words_in_one_existing_array(
        tmp_path: Path, remove_array: bool) -> None:
    _requires_c_backend_dlls()
    base = 32
    targets = (20, 24, 32, 36, 40, 44)
    encoded = tuple((target - base) & 0xFFFF for target in targets)
    original = bytes.fromhex("600c") + b"".join(value.to_bytes(2, "big") for value in encoded)
    original += bytes.fromhex("4e75") + bytes(46 - 16)
    path = tmp_path / "six-relative-words.bin"
    path.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=path,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(path), analysis_cache_path=tmp_path / "array.analysis")
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    actions: list[tuple[str, str, dict[str, object]]] = [
        ("create_manual_data_block_layout", "data_block_layout", {
            "layout_id": "six-words", "hunk": 0, "source_start": 2, "source_end": 14,
            "default_unit": "word"}),
        ("set_manual_data_block_element", "data_block_element", {
            "layout_id": "six-words", "offset": 0, "width": 12, "kind": "array",
            "name": "relative_words", "array_count": 6, "array_stride": 2,
            "representation": "hex"}),
    ]
    names = {target: f"array_target_{index}" for index, target in enumerate(targets)}
    names[base] = "array_base"
    for offset, name in names.items():
        actions.append(("create_manual_label", "label", {
            "label_id": name, "scope": "global", "hunk": 0, "addr": offset, "name": name}))
    refs = []
    for index, (target, bits) in enumerate(zip(targets, encoded, strict=True)):
        ref = _data_block_element_ref_payload([], {
            "layout_id": "six-words", "offset": index * 2, "width": 2,
            "reference_kind": "base_displacement", "signed": True, "scale": 1,
            "base_locator": {"hunk": 0, "offset": base}, "target_hunk": 0,
            "target_offset": target, "source_value": bits,
        })
        refs.append(ref)
        actions.append(("interpret_manual_data_block_element_ref", "data_block_interpreted_ref", ref))
    if remove_array:
        actions.append(("remove_manual_data_block_element", "data_block_element", {
            "layout_id": "six-words", "offset": 0}))
    records = [{"record": "manual_action_log_header", "version": 1, "target_identity": {}}]
    records.extend({"record": "manual_action", "action_id": f"a{i}", "sequence": i,
                    "created_at": "2026-10-13T00:00:00+00:00", "kind": kind, key: payload}
                   for i, (kind, key, payload) in enumerate(actions, 1))
    (tmp_path / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        "\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    metadata = json.loads(effective_metadata_text(tmp_path))
    assert len(metadata["manual_data_references"]) == (0 if remove_array else 6)
    assert not metadata["target_equates"] and not metadata["manual_runtime_address_refs"]
    with effective_metadata_file(tmp_path) as metadata_path:
        rendered = c_backend.render_project_source_with_c_backend(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        try:
            for index, (target, bits, ref) in enumerate(zip(targets, encoded, refs, strict=True)):
                items = _owned(artifact, 2 + index * 2, "outgoing")
                assert len(items) == (0 if remove_array else 2)
                assert {item["reference_role"] for item in items} == (set() if remove_array else {"base", "target"})
                for item in items:
                    assert item["owner_id"] == ref["data_block_ref_id"]
                    assert item["owner_layout_id"] == "six-words"
                    assert item["owner_element_offset"] == index * 2
                    assert item["source_value"] == bits
                    assert item["target_offset"] == (base if item["reference_role"] == "base" else target)
            incoming = _owned(artifact, base, "incoming")
            assert len(incoming) == (0 if remove_array else 7)
        finally:
            artifact.close()
    expressions = [f"\tdc.w {names[target]}-array_base\n" for target in targets]
    for expression in expressions:
        assert rendered.count(expression) == (0 if remove_array else 1)
    _round_trip(tmp_path, rendered, original)


@pytest.mark.parametrize(("mode", "removed"), [
    ("bidirectional", False), ("source_only", False), ("none", False), ("bidirectional", True),
])
def test_post_apply_verifier_checks_real_native_rows_and_relations(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, removed: bool) -> None:
    source, _, ref = _fixture(tmp_path, base=12, target=8, mode=mode,
                              cleanup="reference" if removed else None)
    monkeypatch.setattr(reversing_loop, "_data_block_render_location", lambda *args, **kwargs: (0, 2))
    with effective_metadata_file(tmp_path) as metadata_path:
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        try:
            monkeypatch.setattr(server, "_valid_c_listing_artifact", lambda _: artifact)
            results = {
                layer: reversing_loop._verify_base_displacement_reference(
                    "synthetic", {}, "data.clear_ref" if removed else "data.ref", ref,
                    project_root=tmp_path, layer=layer)
                for layer in ("rendered_source", "xref_projection")
            }
            for result in results.values():
                assert result["status"] == "passed", result
            rendered = results["rendered_source"]
            assert rendered["matching_expressions"] == ([] if removed else ["target_anchor-base_anchor"])
            assert bool(results["xref_projection"]["matching_native_references"]) == (
                not removed and mode != "none")
        finally:
            artifact.close()
