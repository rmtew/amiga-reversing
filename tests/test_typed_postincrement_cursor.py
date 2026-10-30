"""Bounded typed memory cursors preserve EA modes and comment-only field refs."""

from __future__ import annotations

import json
import subprocess
from contextlib import closing
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from tests.test_c_backend import _requires_c_backend_dlls

pytestmark = pytest.mark.c_backend


def _vasm(tmp_path: Path, name: str, text: str) -> bytes:
    source_path = tmp_path / f"{name}.s"
    binary_path = tmp_path / f"{name}.bin"
    source_path.write_text(text, encoding="utf-8")
    result = subprocess.run([
        str(PROJECT_ROOT / "tools" / "vasmm68k_mot.exe"), "-Fbin", "-quiet",
        "-o", str(binary_path), str(source_path),
    ], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return binary_path.read_bytes()


def _artifact(tmp_path: Path, instructions: list[str], width: int = 2, register: str = "A0", other_register: str | None = None):
    _requires_c_backend_dlls()
    original_source = "\n".join(["    SECTION section,code", *[f"    {line}" for line in instructions], "    rts", ""])
    original = _vasm(tmp_path, "original", original_source)
    path = tmp_path / "cursor.bin"
    path.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=path,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(path), analysis_cache_path=tmp_path / "cursor.analysis")
    metadata_path = tmp_path / "cursor.json"
    metadata_path.write_text(json.dumps({
        "target_type": "raw_binary",
        "entry_register_seeds": [{
            "entry_offset": 0, "hunk": 0, "register": register, "kind": "struct_ptr",
            "struct_name": "Triplet", "note": "Triplet", "context_name": None,
        }, *([dict(entry_offset=0,hunk=0,register=other_register,kind="struct_ptr",
                   struct_name="Triplet",note="Triplet")] if other_register else [])],
        "custom_structs": [{"name": "Triplet", "size": width * 3, "fields": [
            {"name": name, "type": {1: "byte", 2: "word", 4: "long"}[width],
             "offset": index * width, "size": width}
            for index, name in enumerate(("first", "second", "third"))
        ]}],
    }), encoding="utf-8")
    _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
        source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
    return source, metadata_path, artifact, original


@pytest.mark.parametrize(("suffix", "width"), [("b", 1), ("w", 2), ("l", 4)])
def test_real_typed_postincrement_reads_preupdate_fields_then_stops_at_root_end(
        tmp_path: Path, suffix: str, width: int) -> None:
    instructions = [f"move.{suffix} (a0)+,d{index}" for index in range(4)]
    source, metadata_path, artifact, original = _artifact(tmp_path, instructions, width)
    with closing(artifact):
        fields = artifact.query_payload("fields", limit=100)["items"]
        resolved = [field for field in fields if field.get("field_name")]
        assert [(field["source_offset"], field["field_name"], field["field_offset"])
                for field in resolved] == [(0, "first", 0), (2, "second", width), (4, "third", width * 2)]
        assert all(field["root_struct_name"] == "Triplet" for field in resolved)
        assert all(field["provenance"]["kind"] != 0 for field in resolved)
        for index, name in enumerate(("first", "second", "third")):
            instruction, = artifact.query_payload("instructions", source_offset=index * 2)["items"]
            assert instruction["text"] == instructions[index]
            assert f"Triplet_{name}" in instruction["annotation"]
            refs = artifact.query_payload("references", source_offset=index * 2, direction="outgoing")["items"]
            field_ref, = [ref for ref in refs if ref.get("symbol") == f"Triplet_{name}"]
            assert field_ref["comment_only"] is True
        assert not any(field["source_offset"] == 6 and field.get("field_name") for field in fields)
    rendered = c_backend.render_project_source_with_c_backend(
        source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
    for instruction in instructions:
        assert instruction in rendered
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw", rendered, project_root=PROJECT_ROOT)
    assert rebuilt == original
    assert _vasm(tmp_path, "rendered", rendered) == original


@pytest.mark.parametrize(("instructions", "register"), [
    (["move.w -(a0),d0", "move.w (a0),d1"], "A0"),
    (["move.w (a7)+,d0", "move.w (a7),d1"], "A7"),
    (["movea.l (a0)+,a0", "move.w (a0),d1"], "A0"),
    (["cmpm.w (a0)+,(a0)+", "move.w (a0),d1"], "A0"),
    (["movem.w (a0)+,d0-d1", "move.w (a0),d2"], "A0"),
    (["move.w (a0)+,(a0)", "move.w (a0),d1"], "A0"),
    (["adda.l #$7FFFFFFF,a0", "adda.l #$7FFFFFFF,a0", "move.w (a0)+,d0"], "A0"),
])
def test_real_unsupported_updates_do_not_preserve_a_stale_typed_cursor(
        tmp_path: Path, instructions: list[str], register: str) -> None:
    _, _, artifact, _ = _artifact(tmp_path, instructions, register=register)
    with closing(artifact):
        fields = artifact.query_payload("fields", limit=100)["items"]
        assert not any(field.get("field_name") for field in fields)


def test_real_scalar_read_does_not_copy_root_cursor_into_output_register(tmp_path: Path) -> None:
    _, _, artifact, _ = _artifact(tmp_path, [
        "move.l (a0)+,d0", "movea.l d0,a1", "move.l (a1),d1", "move.l (a0)+,d2",
    ], width=4)
    with closing(artifact):
        fields = artifact.query_payload("fields", limit=100)["items"]
        assert [(field["source_offset"], field["field_name"], field["field_offset"])
                for field in fields if field.get("field_name")] == [(0, "first", 0), (6, "second", 4)]


@pytest.mark.parametrize(('suffix', 'width'), [('b', 1), ('w', 2), ('l', 4)])
@pytest.mark.parametrize('operation', ['move', 'eor'])
def test_real_typed_destination_updates_retain_fields_and_original_modes(tmp_path, suffix, width, operation):
    instructions = [f'{operation}.{suffix} d0,(a0)+', f'clr.{suffix} (a0)+',
                    f'move.{suffix} d1,-(a0)', f'move.{suffix} d2,-(a0)',
                    f'move.{suffix} (a0),d3']
    source, metadata_path, artifact, original = _artifact(tmp_path, instructions, width)
    with closing(artifact):
        fields = artifact.query_payload('fields', limit=100)['items']
        assert [(f['source_offset'], f['field_name'], f['field_offset'])
                for f in fields if f.get('field_name')] == [
                    (0, 'first', 0), (2, 'second', width), (4, 'second', width),
                    (6, 'first', 0), (8, 'first', 0)]
        for offset, name in [(0, 'first'), (2, 'second'), (4, 'second'), (6, 'first')]:
            instruction, = artifact.query_payload('instructions', source_offset=offset)['items']
            assert f'Triplet_{name}' in instruction['annotation']
            refs = artifact.query_payload('references', source_offset=offset, direction='outgoing')['items']
            field_ref, = [r for r in refs if r.get('symbol') == f'Triplet_{name}']
            assert field_ref['comment_only'] is True
    rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered, project_root=PROJECT_ROOT)
    assert rebuilt == original and _vasm(tmp_path, 'destination', rendered) == original


@pytest.mark.parametrize('instructions', [
    ['move.w d0,-(a0)', 'move.w (a0),d1'],
    ['move.l a0,(a0)+', 'move.w (a0),d1'],
    ['adda.w #2,a0', 'cmpm.w (a0)+,(a0)+', 'move.w (a0),d1'],
    ['movem.w d0-d1,-(a0)', 'move.w (a0),d1'],
    ['clr.w (a7)+', 'move.w (a7),d1'],
])
def test_real_ambiguous_or_underflowing_destination_cursor_is_not_retained(tmp_path, instructions):
    _, _, artifact, _ = _artifact(tmp_path, instructions, register='A7' if 'a7' in instructions[0] else 'A0')
    with closing(artifact):
        assert not any(f.get('field_name') for f in artifact.query_payload('fields', limit=100)['items'])


@pytest.mark.parametrize(('suffix', 'width'), [('b', 1), ('w', 2), ('l', 4)])
def test_real_predecrement_read_uses_bounded_previous_field(tmp_path, suffix, width):
    instructions = [f'move.{suffix} (a0)+,d0', f'move.{suffix} (a0)+,d1',
                    f'move.{suffix} -(a0),d2', f'move.{suffix} -(a0),d3']
    source, metadata_path, artifact, original = _artifact(tmp_path, instructions, width)
    with closing(artifact):
        fields = artifact.query_payload('fields', limit=100)['items']
        assert [(f['source_offset'], f['field_offset']) for f in fields if f.get('field_name')] == [
            (0, 0), (2, width), (4, width), (6, 0)]
    rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered, project_root=PROJECT_ROOT)
    assert rebuilt == original and _vasm(tmp_path, 'predecrement', rendered) == original


@pytest.mark.parametrize(('mode','prefix','field'), [
    ('post', [], 'second'),
    ('pre', ['adda.l #2,a0', 'adda.l #2,a1'], 'first'),
])
def test_distinct_auto_update_streams_keep_both_cursors(tmp_path, mode, prefix, field):
    operands = '(a0)+,(a1)+' if mode == 'post' else '-(a0),-(a1)'
    source, metadata_path, artifact, original = _artifact(tmp_path,
        prefix + [f'move.w {operands}', 'move.w (a0),d0', 'move.w (a1),d1'], other_register='A1')
    with closing(artifact):
        fields=[f for f in artifact.query_payload('fields',limit=100)['items'] if f.get('field_name')]
        assert [f['field_name'] for f in fields] == ['first','first',field,field]
        assert [f['operand_index'] for f in fields[:2]] == [0,1]
        assert all(f['root_struct_name']=='Triplet' for f in fields)
        rendered=artifact.inline_source_text_with_profile()[0]
        assert f'move.w {operands}' in rendered
    rebuilt,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',rendered,project_root=PROJECT_ROOT)
    assert rebuilt==original and _vasm(tmp_path,'two-stream',rendered)==original


def test_independent_untyped_destination_does_not_erase_source_cursor(tmp_path):
    _,_,artifact,_=_artifact(tmp_path,['move.w (a0)+,(a1)+','move.w (a0),d1'])
    with closing(artifact):
        fields=[f for f in artifact.query_payload('fields',limit=100)['items'] if f.get('field_name')]
        assert [f['field_name'] for f in fields]==['first','second']
        assert not any(f['operand_index']==1 for f in fields)
