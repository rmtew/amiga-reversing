from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from ctypes import (
    CDLL,
    POINTER,
    byref,
    c_char_p,
    c_int,
    c_size_t,
    c_uint32,
    c_void_p,
    create_string_buffer,
    string_at,
)
from functools import cache
from pathlib import Path
from typing import cast

from amiga_reversing.disasm.binary_source import (
    BinarySource,
    DiskEntryBinarySource,
    HunkFileBinarySource,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.facts_v2_source_refusal import (
    FactsV2SourceRefused,
    facts_v2_source_refused,
)
from amiga_reversing.disasm.listing_types import (
    AddressRowContext,
    AppSlotRef,
    BlockRowContext,
    HeaderRowContext,
    ListingRow,
    SemanticOperand,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths

type ApiCallRowKey = tuple[int, int]

_APP_SLOT_ACCESS_KINDS = {"read", "write", "read-write", "address"}


class UnsupportedCBackendProject(ValueError):
    pass


class FactsV2RenderAssembleFailed(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        source_profile: dict[str, object],
        assembler_profile: dict[str, object],
    ) -> None:
        self.source_profile = source_profile
        self.assembler_profile = assembler_profile
        super().__init__(message)


class FactsV2DirectRebuildRefused(RuntimeError):
    def __init__(
        self,
        source_profile: dict[str, object],
        direct_profile: dict[str, object],
    ) -> None:
        self.source_profile = source_profile
        self.direct_profile = direct_profile
        super().__init__(str(direct_profile.get("direct_rebuild_refusal_reason") or "direct rebuild refused"))


def render_binary_source_with_c_backend(
    binary_path: str | Path,
    *,
    syntax: str = "vasm",
    project_root: Path = PROJECT_ROOT,
) -> str:
    path = Path(binary_path)
    source = HunkFileBinarySource(
        kind="hunk_file",
        path=path,
        display_path=str(binary_path),
        analysis_cache_path=path.with_name(path.name + ".analysis"),
    )
    return render_project_source_with_c_backend(
        source,
        syntax=syntax,
        project_root=project_root,
    )


def analyze_binary_source_with_c_backend(
    binary_path: str | Path,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    analysis_text = _platform_file_text(
        "platform_file_facts_v2_analysis_path_json_alloc",
        "amiga-hunk",
        str(binary_path),
        "",
        "",
        project_root=project_root,
    )
    return cast(dict[str, object], json.loads(analysis_text))


def validate_amiga_hunk_executable_with_c_backend(
    binary_path: str | Path,
    *,
    project_root: Path = PROJECT_ROOT,
) -> None:
    try:
        summary_text = _platform_file_text(
            "platform_file_inspect_path_json_alloc",
            "amiga-hunk",
            str(binary_path),
            project_root=project_root,
        )
        summary = cast(dict[str, object], json.loads(summary_text))
    except Exception as exc:
        raise ValueError(f"Uploaded media is not an Amiga executable: {exc}") from exc
    if summary.get("file_kind") != "executable":
        raise ValueError("Uploaded media is not an Amiga executable")


def inspect_disk_with_c_backend(
    disk_path: str | Path,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    inspect_text = _platform_disk_text(
        "platform_disk_inspect_path_json_alloc",
        _platform_disk_name_for_path(Path(disk_path)),
        str(disk_path),
        project_root=project_root,
    )
    return cast(dict[str, object], json.loads(inspect_text))


def extract_disk_entry_with_c_backend(
    disk_path: str | Path,
    entry_path: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> bytes:
    return _platform_disk_bytes(
        "platform_disk_extract_entry_path_bytes_alloc",
        _platform_disk_name_for_path(Path(disk_path)),
        str(disk_path),
        entry_path,
        project_root=project_root,
    )


def render_project_source_with_c_backend(
    binary_source: BinarySource,
    *,
    syntax: str = "vasm",
    metadata_path: Path | None = None,
    project_root: Path = PROJECT_ROOT,
) -> str:
    source_text, profile = facts_v2_asm_source_project_source_with_c_backend_profile(
        binary_source,
        metadata_path=metadata_path,
        project_root=project_root,
    )
    if facts_v2_source_refused(profile):
        raise FactsV2SourceRefused(profile)
    return source_text


def assemble_platform_source_path_with_c_backend(
    backend: str,
    source_path: str | Path,
    *,
    include_dir: str | Path | None = None,
    output_path: str | Path | None = None,
    target_cpu: str = "any",
    enable_vasm_compat_rewrites: bool = False,
    project_root: Path = PROJECT_ROOT,
) -> tuple[bytes, dict[str, object]]:
    dll = _platform_file_dll(project_root)
    out_data = c_void_p()
    out_size = c_size_t()
    out_profile_json = c_void_p()
    out_error = c_void_p()
    common_args = [
        _c_arg(backend),
        _c_arg(str(include_dir) if include_dir is not None else ""),
        _c_arg(source_path),
    ]
    if output_path is None:
        function = dll.platform_file_assemble_source_path_bytes_profile_alloc
    else:
        function = dll.platform_file_assemble_source_path_to_output_bytes_profile_alloc
        common_args.append(_c_arg(output_path))
    result = function(
        *common_args,
        _c_arg(target_cpu),
        c_int(1 if enable_vasm_compat_rewrites else 0),
        byref(out_data),
        byref(out_size),
        byref(out_profile_json),
        byref(out_error),
    )
    try:
        profile_text = (
            string_at(out_profile_json.value).decode("utf-8", errors="replace")
            if out_profile_json.value
            else "{}"
        )
        profile = cast(dict[str, object], json.loads(profile_text))
        if result != 0:
            detail = string_at(out_error.value).decode("utf-8", errors="replace") if out_error.value else ""
            raise RuntimeError(f"C platform assembler failed: {detail}")
        data = bytes(string_at(out_data.value, out_size.value)) if out_data.value else b""
        return data, profile
    finally:
        if out_error.value:
            dll.platform_file_free_text(out_error)
        if out_profile_json.value:
            dll.platform_file_free_text(out_profile_json)
        if out_data.value:
            dll.platform_file_free_bytes(out_data)


def assemble_platform_source_text_with_c_backend(
    backend: str,
    source_text: str,
    *,
    include_dir: str | Path | None = None,
    output_path: str | Path | None = None,
    target_cpu: str = "any",
    enable_vasm_compat_rewrites: bool = False,
    project_root: Path = PROJECT_ROOT,
) -> tuple[bytes, dict[str, object]]:
    dll = _platform_file_dll(project_root)
    out_data = c_void_p()
    out_size = c_size_t()
    out_profile_json = c_void_p()
    out_error = c_void_p()
    common_args = [
        _c_arg(backend),
        _c_arg(str(include_dir) if include_dir is not None else ""),
        _c_arg(source_text),
    ]
    if output_path is None:
        function = dll.platform_file_assemble_source_text_bytes_profile_alloc
    else:
        function = dll.platform_file_assemble_source_text_to_output_bytes_profile_alloc
        common_args.append(_c_arg(output_path))
    result = function(
        *common_args,
        _c_arg(target_cpu),
        c_int(1 if enable_vasm_compat_rewrites else 0),
        byref(out_data),
        byref(out_size),
        byref(out_profile_json),
        byref(out_error),
    )
    try:
        profile_text = (
            string_at(out_profile_json.value).decode("utf-8", errors="replace")
            if out_profile_json.value
            else "{}"
        )
        profile = cast(dict[str, object], json.loads(profile_text))
        if result != 0:
            detail = string_at(out_error.value).decode("utf-8", errors="replace") if out_error.value else ""
            raise RuntimeError(f"C platform assembler failed: {detail}")
        data = bytes(string_at(out_data.value, out_size.value)) if out_data.value else b""
        return data, profile
    finally:
        if out_error.value:
            dll.platform_file_free_text(out_error)
        if out_profile_json.value:
            dll.platform_file_free_text(out_profile_json)
        if out_data.value:
            dll.platform_file_free_bytes(out_data)


def facts_v2_render_assemble_project_source_with_c_backend_profile(
    binary_source: BinarySource,
    *,
    metadata_path: Path | None = None,
    include_dir: str | Path | None = None,
    output_path: str | Path | None = None,
    target_cpu: str = "any",
    enable_vasm_compat_rewrites: bool = False,
    project_root: Path = PROJECT_ROOT,
) -> tuple[bytes, dict[str, object], dict[str, object]]:
    metadata_text = _metadata_path_text(metadata_path)
    include_text = str(include_dir) if include_dir is not None else ""
    output_text = str(output_path) if output_path is not None else ""
    with _source_file_for_c_backend(binary_source, project_root=project_root) as source_file:
        if source_file.entry_offset is None:
            return _platform_file_facts_v2_render_assemble_profile(
                "platform_file_facts_v2_render_assemble_path_bytes_profile_alloc",
                source_file.platform_name,
                str(source_file.path),
                metadata_text,
                include_text,
                output_text,
                target_cpu,
                1 if enable_vasm_compat_rewrites else 0,
                project_root=project_root,
            )
        return _platform_file_facts_v2_render_assemble_profile(
            "platform_file_facts_v2_render_assemble_raw_path_bytes_profile_alloc",
            source_file.platform_name,
            str(source_file.path),
            source_file.entry_offset,
            metadata_text,
            include_text,
            output_text,
            target_cpu,
            1 if enable_vasm_compat_rewrites else 0,
            project_root=project_root,
        )


def facts_v2_direct_rebuild_project_source_with_c_backend_profile(
    binary_source: BinarySource,
    *,
    metadata_path: Path | None = None,
    output_path: str | Path | None = None,
    compare_original: bool = False,
    project_root: Path = PROJECT_ROOT,
) -> tuple[bytes, dict[str, object], dict[str, object]]:
    metadata_text = _metadata_path_text(metadata_path)
    output_text = str(output_path) if output_path is not None else ""
    if isinstance(binary_source, DiskEntryBinarySource):
        data = binary_source.read_bytes()
        return _platform_file_facts_v2_direct_rebuild_buffer_profile(
            (
                "platform_file_facts_v2_direct_rebuild_compare_buffer_bytes_profile_alloc"
                if compare_original
                else "platform_file_facts_v2_direct_rebuild_buffer_bytes_profile_alloc"
            ),
            _platform_file_name_for_disk_path(binary_source.adf_path),
            data,
            metadata_text,
            binary_source.display_path,
            output_text,
            project_root=project_root,
        )
    with _source_file_for_c_backend(binary_source, project_root=project_root) as source_file:
        if source_file.entry_offset is not None:
            raise UnsupportedCBackendProject("facts_v2 direct rebuild does not support raw binary sources")
        return _platform_file_facts_v2_direct_rebuild_profile(
            (
                "platform_file_facts_v2_direct_rebuild_compare_path_bytes_profile_alloc"
                if compare_original
                else "platform_file_facts_v2_direct_rebuild_path_bytes_profile_alloc"
            ),
            source_file.platform_name,
            str(source_file.path),
            metadata_text,
            output_text,
            project_root=project_root,
        )


def analyze_project_source_with_c_backend(
    binary_source: BinarySource,
    *,
    metadata_path: Path | None = None,
    entry_offset_args: tuple[str, ...] = (),
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    metadata_text = _metadata_path_text(metadata_path)
    entry_offsets_text = _entry_offsets_text(entry_offset_args)
    with _source_file_for_c_backend(binary_source, project_root=project_root) as source_file:
        if source_file.entry_offset is None:
            analysis_text = _platform_file_text(
                "platform_file_facts_v2_analysis_path_json_alloc",
                source_file.platform_name,
                str(source_file.path),
                metadata_text,
                entry_offsets_text,
                project_root=project_root,
            )
        else:
            analysis_text = _platform_file_text(
                "platform_file_facts_v2_analysis_raw_path_json_alloc",
                source_file.platform_name,
                str(source_file.path),
                source_file.entry_offset,
                metadata_text,
                entry_offsets_text,
                project_root=project_root,
            )
    return cast(dict[str, object], json.loads(analysis_text))


def effective_policy_project_source_with_c_backend(
    binary_source: BinarySource,
    *,
    metadata_path: Path | None = None,
    entry_offset_args: tuple[str, ...] = (),
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    metadata_text = _metadata_path_text(metadata_path)
    entry_offsets_text = _entry_offsets_text(entry_offset_args)
    with _source_file_for_c_backend(binary_source, project_root=project_root) as source_file:
        if source_file.entry_offset is None:
            policy_text = _platform_file_text(
                "platform_file_effective_policy_path_json_alloc",
                source_file.platform_name,
                str(source_file.path),
                metadata_text,
                entry_offsets_text,
                project_root=project_root,
            )
        else:
            policy_text = _platform_file_text(
                "platform_file_effective_policy_raw_path_json_alloc",
                source_file.platform_name,
                str(source_file.path),
                source_file.entry_offset,
                metadata_text,
                entry_offsets_text,
                project_root=project_root,
            )
    return cast(dict[str, object], json.loads(policy_text))


def benchmark_project_source_with_text_from_c_backend(
    binary_source: BinarySource,
    *,
    syntax: str = "vasm",
    metadata_path: Path | None = None,
    project_root: Path = PROJECT_ROOT,
) -> tuple[dict[str, object], str]:
    source_text, profile = facts_v2_asm_source_project_source_with_c_backend_profile(
        binary_source,
        metadata_path=metadata_path,
        project_root=project_root,
    )
    return _benchmark_from_facts_v2_asm_source_profile(profile), source_text


def build_project_rows_with_c_backend(
    project_name: str,
    project_root: Path = PROJECT_ROOT,
) -> tuple[list[ListingRow], dict[ApiCallRowKey, dict[str, object]]]:
    return build_project_rows_generation_with_c_backend(
        project_name,
        generation="full",
        project_root=project_root,
    )


def build_project_rows_generation_with_c_backend(
    project_name: str,
    *,
    generation: str,
    project_root: Path = PROJECT_ROOT,
) -> tuple[list[ListingRow], dict[ApiCallRowKey, dict[str, object]]]:
    rows, api_calls, _ = build_project_rows_generation_with_c_backend_profile(
        project_name,
        generation=generation,
        project_root=project_root,
    )
    return rows, api_calls


def build_project_rows_generation_with_c_backend_profile(
    project_name: str,
    *,
    generation: str,
    project_root: Path = PROJECT_ROOT,
) -> tuple[list[ListingRow], dict[ApiCallRowKey, dict[str, object]], dict[str, object]]:
    if generation not in {"basic", "full"}:
        raise ValueError(f"Unsupported listing generation: {generation}")
    paths = resolve_project_paths(project_name, project_root=project_root)
    with effective_metadata_file(paths.target_dir) as metadata_path:
        metadata_text = _metadata_path_text(metadata_path)
        rows, api_calls, profile, _ = _build_project_rows_generation_from_source(
            paths.binary_source,
            metadata_text=metadata_text,
            generation=generation,
            syntax="canonical",
            include_source_text=False,
            project_root=project_root,
        )
        return rows, api_calls, profile


def build_project_rows_generation_with_c_backend_profile_text(
    project_name: str,
    *,
    generation: str,
    syntax: str = "canonical",
    project_root: Path = PROJECT_ROOT,
) -> tuple[list[ListingRow], dict[ApiCallRowKey, dict[str, object]], dict[str, object], str | None]:
    if generation not in {"basic", "full"}:
        raise ValueError(f"Unsupported listing generation: {generation}")
    paths = resolve_project_paths(project_name, project_root=project_root)
    with effective_metadata_file(paths.target_dir) as metadata_path:
        metadata_text = _metadata_path_text(metadata_path)
        return _build_project_rows_generation_from_source(
            paths.binary_source,
            metadata_text=metadata_text,
            generation=generation,
            syntax=syntax,
            include_source_text=True,
            project_root=project_root,
        )


def _build_project_rows_generation_from_source(
    binary_source: BinarySource,
    *,
    metadata_text: str,
    generation: str,
    syntax: str,
    include_source_text: bool,
    project_root: Path,
) -> tuple[list[ListingRow], dict[ApiCallRowKey, dict[str, object]], dict[str, object], str | None]:
    profile: dict[str, object] = {}
    source_text: str | None = None
    with _source_file_for_c_backend(binary_source, project_root=project_root) as source_file:
        include_dir = _platform_include_dir_for_listing(source_file.platform_name, project_root)
        if source_file.entry_offset is None:
            function_name = (
                "platform_file_facts_v2_listing_rows_with_analysis_and_text_path_json_alloc"
                if include_source_text
                else (
                    "platform_file_facts_v2_basic_listing_rows_path_json_alloc"
                    if generation == "basic"
                    else "platform_file_facts_v2_listing_rows_with_analysis_path_json_alloc"
                )
            )
            combined_text = _platform_file_text(
                function_name,
                source_file.platform_name,
                str(source_file.path),
                metadata_text,
                str(include_dir),
                project_root=project_root,
            )
        else:
            function_name = (
                "platform_file_facts_v2_listing_rows_with_analysis_and_text_raw_path_json_alloc"
                if include_source_text
                else (
                    "platform_file_facts_v2_basic_listing_rows_raw_path_json_alloc"
                    if generation == "basic"
                    else "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc"
                )
            )
            combined_text = _platform_file_text(
                function_name,
                source_file.platform_name,
                str(source_file.path),
                source_file.entry_offset,
                metadata_text,
                str(include_dir),
                project_root=project_root,
            )
        combined = cast(dict[str, object], json.loads(combined_text))
        listing_rows = cast(dict[str, object], combined.get("listing", {}))
        analysis = cast(dict[str, object], combined.get("analysis", {}))
        profile = cast(dict[str, object], combined.get("profile", {}))
        rendered_source_text = combined.get("source_text")
        source_text = rendered_source_text if isinstance(rendered_source_text, str) else None
    return rows_from_c_listing_json(listing_rows), api_calls_from_c_analysis(analysis), profile, source_text


def type_catalog_from_c_backend(
    project_name: str,
    project_root: Path = PROJECT_ROOT,
) -> list[dict[str, object]]:
    resolve_project_paths(project_name, project_root=project_root)
    return amiga_type_catalog_with_c_backend(project_root=project_root)


def amiga_type_catalog_with_c_backend(
    project_root: Path = PROJECT_ROOT,
) -> list[dict[str, object]]:
    catalog_text = _platform_file_text("platform_file_type_catalog_json_alloc", "amiga-hunk", project_root=project_root)
    catalog = json.loads(catalog_text)
    return cast(list[dict[str, object]], catalog if isinstance(catalog, list) else [])


def amiga_naming_catalog_with_c_backend(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    catalog_text = _platform_file_text(
        "platform_file_naming_catalog_json_alloc", "amiga-hunk", project_root=project_root
    )
    catalog = json.loads(catalog_text)
    return cast(dict[str, object], catalog if isinstance(catalog, dict) else {})


def amiga_os_metadata_catalog_with_c_backend(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    catalog_text = _platform_file_text(
        "platform_file_os_metadata_catalog_json_alloc", "amiga-hunk", project_root=project_root
    )
    catalog = json.loads(catalog_text)
    return cast(dict[str, object], catalog if isinstance(catalog, dict) else {})


def validate_api_input_struct_with_c_backend(
    project_name: str,
    library: str,
    function: str,
    input_name: str,
    struct_name: str,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    resolve_project_paths(project_name, project_root=project_root)
    metadata_text = _platform_file_text(
        "platform_file_api_input_struct_json_alloc",
        "amiga-hunk",
        library,
        function,
        input_name,
        struct_name,
        project_root=project_root,
    )
    metadata = json.loads(metadata_text)
    return cast(dict[str, object], metadata if isinstance(metadata, dict) else {})


def rows_from_c_listing_json(payload: dict[str, object]) -> list[ListingRow]:
    rows: list[ListingRow] = []
    for raw_row in cast(list[dict[str, object]], payload.get("rows", [])):
        row_id = raw_row.get("row_id")
        kind = raw_row.get("kind")
        text = raw_row.get("text")
        if not isinstance(row_id, str) or not isinstance(kind, str) or not isinstance(text, str):
            continue
        addr = raw_row.get("addr")
        entity_addr = raw_row.get("entity_addr")
        stable_key = raw_row.get("stable_key")
        analysis_generation = raw_row.get("analysis_generation")
        analysis_phase = raw_row.get("analysis_phase")
        section_index = raw_row.get("section_index")
        start_offset = raw_row.get("start_offset")
        end_offset = raw_row.get("end_offset")
        label = raw_row.get("label")
        opcode_or_directive = raw_row.get("opcode_or_directive")
        operand_text = raw_row.get("operand_text")
        comment_text = raw_row.get("comment_text")
        structured_data = raw_row.get("structured_data")
        source_context = _source_context_from_c_json(raw_row.get("source_context"))
        app_slot_refs = _app_slot_refs_from_c_json(raw_row.get("app_slot_refs"))
        row_bytes = raw_row.get("bytes")
        parsed_bytes = None
        if isinstance(row_bytes, str) and row_bytes != "":
            try:
                parsed_bytes = bytes.fromhex(row_bytes)
            except ValueError:
                parsed_bytes = None
        rows.append(
            ListingRow(
                row_id=row_id,
                kind=kind,
                text=text,
                stable_key=stable_key if isinstance(stable_key, str) else None,
                analysis_generation=analysis_generation if isinstance(analysis_generation, str) else "full",
                analysis_phase=analysis_phase if isinstance(analysis_phase, str) else None,
                section_index=section_index if isinstance(section_index, int) else None,
                start_offset=start_offset if isinstance(start_offset, int) else None,
                end_offset=end_offset if isinstance(end_offset, int) else None,
                addr=addr if isinstance(addr, int) else None,
                entity_addr=entity_addr if isinstance(entity_addr, int) else None,
                bytes=parsed_bytes,
                label=label if isinstance(label, str) else None,
                opcode_or_directive=opcode_or_directive if isinstance(opcode_or_directive, str) else None,
                operand_parts=()
                if not isinstance(operand_text, str) or operand_text == ""
                else (SemanticOperand(kind="text", text=operand_text),),
                app_slot_refs=app_slot_refs,
                operand_text=operand_text if isinstance(operand_text, str) else "",
                comment_parts=() if not isinstance(comment_text, str) or comment_text == "" else (comment_text,),
                comment_text=comment_text if isinstance(comment_text, str) else "",
                source_context=source_context,
                structured_data=structured_data if isinstance(structured_data, dict) else None,
            )
        )
    return rows


def _app_slot_refs_from_c_json(value: object) -> tuple[AppSlotRef, ...]:
    if not isinstance(value, list):
        return ()
    refs: list[AppSlotRef] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        symbol = item.get("symbol")
        displacement = item.get("displacement")
        base_register = item.get("base_register")
        operand_index = item.get("operand_index")
        access = item.get("access")
        if (
            not isinstance(symbol, str)
            or not isinstance(displacement, int)
            or not isinstance(base_register, str)
            or not isinstance(operand_index, int)
            or not isinstance(access, str)
            or access not in _APP_SLOT_ACCESS_KINDS
        ):
            continue
        refs.append(
            AppSlotRef(
                symbol=symbol,
                displacement=displacement,
                base_register=base_register,
                operand_index=operand_index,
                access=access,
            )
        )
    return tuple(refs)


def api_calls_from_c_analysis(analysis: dict[str, object]) -> dict[ApiCallRowKey, dict[str, object]]:
    result: dict[ApiCallRowKey, dict[str, object]] = {}
    for section in cast(list[dict[str, object]], analysis.get("sections", [])):
        section_index_value = section.get("section_index", 0)
        section_index = section_index_value if isinstance(section_index_value, int) else 0
        for call in cast(list[dict[str, object]], section.get("recovered_platform_calls", [])):
            symbol = call.get("function_name") or call.get("symbol_name") or call.get("note_symbol_name")
            if not isinstance(symbol, str) or symbol == "":
                continue
            offset = call.get("offset")
            if not isinstance(offset, int):
                continue
            library = _api_call_library_name(call)
            function = symbol.removeprefix("_LVO")
            result[(section_index, offset)] = {
                "library": library,
                "function": function,
                "note_kind": call.get("note_kind"),
                "call_kind": call.get("kind"),
                "symbol_name": call.get("symbol_name"),
                "note_symbol_name": call.get("note_symbol_name"),
                "inputs": _api_call_inputs(call),
            }
    return result


def _source_context_from_c_json(value: object) -> HeaderRowContext | BlockRowContext | AddressRowContext | None:
    if not isinstance(value, dict):
        return None
    section = value.get("section")
    if isinstance(section, str):
        return HeaderRowContext(section=section)
    kind = value.get("kind")
    hunk_index = value.get("hunk_index")
    if isinstance(kind, str) and isinstance(hunk_index, int):
        verified_state = value.get("verified_state")
        return BlockRowContext(
            kind=kind,
            hunk_index=hunk_index,
            verified_state=verified_state if isinstance(verified_state, str) else None,
        )
    block = value.get("block")
    if isinstance(block, int):
        return AddressRowContext(block=block)
    return None


def _api_call_library_name(call: dict[str, object]) -> str:
    library_name = call.get("library_name")
    if isinstance(library_name, str) and library_name != "":
        return library_name
    note_base = call.get("note_base_name")
    if isinstance(note_base, str) and note_base != "":
        return note_base
    return "unknown"


def _api_call_inputs(call: dict[str, object]) -> list[dict[str, object]]:
    inputs = call.get("inputs")
    if not isinstance(inputs, list):
        return []
    result: list[dict[str, object]] = []
    for item in inputs:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        regs = item.get("regs")
        if not isinstance(name, str):
            continue
        result.append(
            {
                "name": name,
                "regs": [reg for reg in regs if isinstance(reg, str)] if isinstance(regs, list) else [],
                "type": item.get("type") if isinstance(item.get("type"), str) else None,
                "i_struct": item.get("i_struct") if isinstance(item.get("i_struct"), str) else None,
                "source": item.get("source") if isinstance(item.get("source"), str) else "parsed NDK",
                "semantic_kind": item.get("semantic_kind") if isinstance(item.get("semantic_kind"), str) else None,
                "value_domain": item.get("value_domain") if isinstance(item.get("value_domain"), str) else None,
            }
        )
    return result


def _metadata_path_text(metadata_path: Path | None) -> str:
    if metadata_path is None or not metadata_path.exists():
        return ""
    return str(metadata_path)


def _entry_offsets_text(entry_offset_args: tuple[str, ...]) -> str:
    return ";".join(entry_offset_args)


def _platform_file_text(function_name: str, *args: object, project_root: Path) -> str:
    dll = _platform_file_dll(project_root)
    function = getattr(dll, function_name)
    out_text = c_void_p()
    c_args = [_c_arg(arg) for arg in args]
    result = function(*c_args, byref(out_text))
    try:
        text = string_at(out_text.value).decode("utf-8", errors="replace") if out_text.value else ""
        if result != 0:
            raise RuntimeError(f"C backend DLL failed: {text}")
        return text
    finally:
        if out_text.value:
            dll.platform_file_free_text(out_text)


def _platform_file_facts_v2_source_text_profile(
    function_name: str, *args: object, project_root: Path
) -> tuple[str, dict[str, object]]:
    dll = _platform_file_dll(project_root)
    function = getattr(dll, function_name)
    out_source_text = c_void_p()
    out_profile_json = c_void_p()
    c_args = [_c_arg(arg) for arg in args]
    result = function(*c_args, byref(out_source_text), byref(out_profile_json))
    try:
        source_text = (
            string_at(out_source_text.value).decode("utf-8", errors="replace")
            if out_source_text.value
            else ""
        )
        profile_text = (
            string_at(out_profile_json.value).decode("utf-8", errors="replace")
            if out_profile_json.value
            else "{}"
        )
        if result != 0:
            raise RuntimeError(f"C backend DLL failed: {profile_text}")
        return source_text, cast(dict[str, object], json.loads(profile_text))
    finally:
        if out_source_text.value:
            dll.platform_file_free_text(out_source_text)
        if out_profile_json.value:
            dll.platform_file_free_text(out_profile_json)


def _platform_file_facts_v2_render_assemble_profile(
    function_name: str, *args: object, project_root: Path
) -> tuple[bytes, dict[str, object], dict[str, object]]:
    dll = _platform_file_dll(project_root)
    function = getattr(dll, function_name)
    out_data = c_void_p()
    out_size = c_size_t()
    out_source_profile_json = c_void_p()
    out_assembler_profile_json = c_void_p()
    out_error = c_void_p()
    c_args = [_c_arg(arg) for arg in args[:-1]]
    c_args.append(c_int(int(args[-1])))
    result = function(
        *c_args,
        byref(out_data),
        byref(out_size),
        byref(out_source_profile_json),
        byref(out_assembler_profile_json),
        byref(out_error),
    )
    try:
        source_profile_text = (
            string_at(out_source_profile_json.value).decode("utf-8", errors="replace")
            if out_source_profile_json.value
            else "{}"
        )
        assembler_profile_text = (
            string_at(out_assembler_profile_json.value).decode("utf-8", errors="replace")
            if out_assembler_profile_json.value
            else "{}"
        )
        source_profile = cast(dict[str, object], json.loads(source_profile_text))
        assembler_profile = cast(dict[str, object], json.loads(assembler_profile_text))
        if facts_v2_source_refused(source_profile):
            raise FactsV2SourceRefused(source_profile)
        if result != 0:
            detail = string_at(out_error.value).decode("utf-8", errors="replace") if out_error.value else ""
            raise FactsV2RenderAssembleFailed(
                f"C facts_v2 render+assemble failed: {detail}",
                source_profile=source_profile,
                assembler_profile=assembler_profile,
            )
        data = bytes(string_at(out_data.value, out_size.value)) if out_data.value else b""
        return data, source_profile, assembler_profile
    finally:
        if out_error.value:
            dll.platform_file_free_text(out_error)
        if out_source_profile_json.value:
            dll.platform_file_free_text(out_source_profile_json)
        if out_assembler_profile_json.value:
            dll.platform_file_free_text(out_assembler_profile_json)
        if out_data.value:
            dll.platform_file_free_bytes(out_data)


def _platform_file_facts_v2_direct_rebuild_profile(
    function_name: str, *args: object, project_root: Path
) -> tuple[bytes, dict[str, object], dict[str, object]]:
    dll = _platform_file_dll(project_root)
    function = getattr(dll, function_name)
    out_data = c_void_p()
    out_size = c_size_t()
    out_source_profile_json = c_void_p()
    out_direct_profile_json = c_void_p()
    out_error = c_void_p()
    c_args = [_c_arg(arg) for arg in args]
    result = function(
        *c_args,
        byref(out_data),
        byref(out_size),
        byref(out_source_profile_json),
        byref(out_direct_profile_json),
        byref(out_error),
    )
    try:
        source_profile_text = (
            string_at(out_source_profile_json.value).decode("utf-8", errors="replace")
            if out_source_profile_json.value
            else "{}"
        )
        direct_profile_text = (
            string_at(out_direct_profile_json.value).decode("utf-8", errors="replace")
            if out_direct_profile_json.value
            else "{}"
        )
        source_profile = cast(dict[str, object], json.loads(source_profile_text))
        direct_profile = cast(dict[str, object], json.loads(direct_profile_text))
        if facts_v2_source_refused(source_profile):
            raise FactsV2SourceRefused(source_profile)
        if direct_profile.get("direct_rebuild_refused") is True:
            raise FactsV2DirectRebuildRefused(source_profile, direct_profile)
        if result != 0:
            detail = string_at(out_error.value).decode("utf-8", errors="replace") if out_error.value else ""
            raise FactsV2RenderAssembleFailed(
                f"C facts_v2 direct rebuild failed: {detail}",
                source_profile=source_profile,
                assembler_profile=direct_profile,
            )
        data = bytes(string_at(out_data.value, out_size.value)) if out_data.value else b""
        return data, source_profile, direct_profile
    finally:
        if out_error.value:
            dll.platform_file_free_text(out_error)
        if out_source_profile_json.value:
            dll.platform_file_free_text(out_source_profile_json)
        if out_direct_profile_json.value:
            dll.platform_file_free_text(out_direct_profile_json)
        if out_data.value:
            dll.platform_file_free_bytes(out_data)


def _platform_file_facts_v2_direct_rebuild_buffer_profile(
    function_name: str,
    platform_name: str,
    data: bytes,
    metadata_text: str,
    display_path: str,
    output_text: str,
    *,
    project_root: Path,
) -> tuple[bytes, dict[str, object], dict[str, object]]:
    dll = _platform_file_dll(project_root)
    function = getattr(dll, function_name)
    data_buffer = create_string_buffer(data)
    out_data = c_void_p()
    out_size = c_size_t()
    out_source_profile_json = c_void_p()
    out_direct_profile_json = c_void_p()
    out_error = c_void_p()
    result = function(
        _c_arg(platform_name),
        data_buffer,
        len(data),
        _c_arg(metadata_text),
        _c_arg(display_path),
        _c_arg(output_text),
        byref(out_data),
        byref(out_size),
        byref(out_source_profile_json),
        byref(out_direct_profile_json),
        byref(out_error),
    )
    try:
        source_profile_text = (
            string_at(out_source_profile_json.value).decode("utf-8", errors="replace")
            if out_source_profile_json.value
            else "{}"
        )
        direct_profile_text = (
            string_at(out_direct_profile_json.value).decode("utf-8", errors="replace")
            if out_direct_profile_json.value
            else "{}"
        )
        source_profile = cast(dict[str, object], json.loads(source_profile_text))
        direct_profile = cast(dict[str, object], json.loads(direct_profile_text))
        if facts_v2_source_refused(source_profile):
            raise FactsV2SourceRefused(source_profile)
        if direct_profile.get("direct_rebuild_refused") is True:
            raise FactsV2DirectRebuildRefused(source_profile, direct_profile)
        if result != 0:
            detail = string_at(out_error.value).decode("utf-8", errors="replace") if out_error.value else ""
            raise FactsV2RenderAssembleFailed(
                f"C facts_v2 direct rebuild failed: {detail}",
                source_profile=source_profile,
                assembler_profile=direct_profile,
            )
        rebuilt = bytes(string_at(out_data.value, out_size.value)) if out_data.value else b""
        return rebuilt, source_profile, direct_profile
    finally:
        if out_error.value:
            dll.platform_file_free_text(out_error)
        if out_source_profile_json.value:
            dll.platform_file_free_text(out_source_profile_json)
        if out_direct_profile_json.value:
            dll.platform_file_free_text(out_direct_profile_json)
        if out_data.value:
            dll.platform_file_free_bytes(out_data)


def _platform_disk_text(function_name: str, *args: object, project_root: Path) -> str:
    dll = _platform_disk_dll(project_root)
    function = getattr(dll, function_name)
    out_text = c_void_p()
    c_args = [_c_arg(arg) for arg in args]
    result = function(*c_args, byref(out_text))
    try:
        text = string_at(out_text.value).decode("utf-8", errors="replace") if out_text.value else ""
        if result != 0:
            raise RuntimeError(f"C disk backend DLL failed: {text}")
        return text
    finally:
        if out_text.value:
            dll.platform_disk_free_text(out_text)


def _platform_disk_bytes(function_name: str, *args: object, project_root: Path) -> bytes:
    dll = _platform_disk_dll(project_root)
    function = getattr(dll, function_name)
    out_data = c_void_p()
    out_size = c_size_t()
    out_error = c_void_p()
    c_args = [_c_arg(arg) for arg in args]
    result = function(*c_args, byref(out_data), byref(out_size), byref(out_error))
    try:
        if result != 0:
            detail = string_at(out_error.value).decode("utf-8", errors="replace") if out_error.value else ""
            raise RuntimeError(f"C disk backend DLL failed: {detail}")
        return bytes(string_at(out_data.value, out_size.value)) if out_data.value else b""
    finally:
        if out_error.value:
            dll.platform_disk_free_text(out_error)
        if out_data.value:
            dll.platform_disk_free_bytes(out_data)


def _c_arg(value: object) -> object:
    if isinstance(value, Path):
        return c_char_p(os.fsencode(value))
    if isinstance(value, str):
        return c_char_p(value.encode("utf-8"))
    if isinstance(value, int):
        return c_uint32(value)
    raise TypeError(f"Unsupported C backend argument: {value!r}")


@cache
def _platform_file_dll(project_root: Path) -> CDLL:
    dll = _load_dll(project_root, "platform_file_lib.dll")
    dll.platform_file_free_text.argtypes = [c_void_p]
    dll.platform_file_free_text.restype = None
    dll.platform_file_free_bytes.argtypes = [c_void_p]
    dll.platform_file_free_bytes.restype = None
    _configure_text_function(dll, "platform_file_inspect_path_json_alloc", 2)
    _configure_text_function(dll, "platform_file_facts_v2_analysis_path_json_alloc", 4)
    _configure_text_function(dll, "platform_file_facts_v2_analysis_raw_path_json_alloc", 5)
    _configure_text_function(dll, "platform_file_effective_policy_path_json_alloc", 4)
    _configure_text_function(dll, "platform_file_effective_policy_raw_path_json_alloc", 5)
    _configure_text_function(dll, "platform_file_facts_v2_asm_source_path_text_alloc", 3)
    _configure_text_function(dll, "platform_file_facts_v2_asm_source_raw_path_text_alloc", 4)
    _configure_text_function(dll, "platform_file_facts_v2_asm_source_path_json_alloc", 3)
    _configure_text_function(dll, "platform_file_facts_v2_asm_source_raw_path_json_alloc", 4)
    dll.platform_file_facts_v2_asm_source_path_text_profile_alloc.argtypes = [
        c_char_p,
        c_char_p,
        c_char_p,
        POINTER(c_void_p),
        POINTER(c_void_p),
    ]
    dll.platform_file_facts_v2_asm_source_path_text_profile_alloc.restype = c_int
    dll.platform_file_facts_v2_asm_source_raw_path_text_profile_alloc.argtypes = [
        c_char_p,
        c_char_p,
        c_uint32,
        c_char_p,
        POINTER(c_void_p),
        POINTER(c_void_p),
    ]
    dll.platform_file_facts_v2_asm_source_raw_path_text_profile_alloc.restype = c_int
    dll.platform_file_facts_v2_render_assemble_path_bytes_profile_alloc.argtypes = [
        c_char_p,
        c_char_p,
        c_char_p,
        c_char_p,
        c_char_p,
        c_char_p,
        c_int,
        POINTER(c_void_p),
        POINTER(c_size_t),
        POINTER(c_void_p),
        POINTER(c_void_p),
        POINTER(c_void_p),
    ]
    dll.platform_file_facts_v2_render_assemble_path_bytes_profile_alloc.restype = c_int
    dll.platform_file_facts_v2_render_assemble_raw_path_bytes_profile_alloc.argtypes = [
        c_char_p,
        c_char_p,
        c_uint32,
        c_char_p,
        c_char_p,
        c_char_p,
        c_char_p,
        c_int,
        POINTER(c_void_p),
        POINTER(c_size_t),
        POINTER(c_void_p),
        POINTER(c_void_p),
        POINTER(c_void_p),
    ]
    dll.platform_file_facts_v2_render_assemble_raw_path_bytes_profile_alloc.restype = c_int
    dll.platform_file_facts_v2_direct_rebuild_path_bytes_profile_alloc.argtypes = [
        c_char_p,
        c_char_p,
        c_char_p,
        c_char_p,
        POINTER(c_void_p),
        POINTER(c_size_t),
        POINTER(c_void_p),
        POINTER(c_void_p),
        POINTER(c_void_p),
    ]
    dll.platform_file_facts_v2_direct_rebuild_path_bytes_profile_alloc.restype = c_int
    dll.platform_file_facts_v2_direct_rebuild_compare_path_bytes_profile_alloc.argtypes = [
        c_char_p,
        c_char_p,
        c_char_p,
        c_char_p,
        POINTER(c_void_p),
        POINTER(c_size_t),
        POINTER(c_void_p),
        POINTER(c_void_p),
        POINTER(c_void_p),
    ]
    dll.platform_file_facts_v2_direct_rebuild_compare_path_bytes_profile_alloc.restype = c_int
    dll.platform_file_facts_v2_direct_rebuild_buffer_bytes_profile_alloc.argtypes = [
        c_char_p,
        c_void_p,
        c_size_t,
        c_char_p,
        c_char_p,
        c_char_p,
        POINTER(c_void_p),
        POINTER(c_size_t),
        POINTER(c_void_p),
        POINTER(c_void_p),
        POINTER(c_void_p),
    ]
    dll.platform_file_facts_v2_direct_rebuild_buffer_bytes_profile_alloc.restype = c_int
    dll.platform_file_facts_v2_direct_rebuild_compare_buffer_bytes_profile_alloc.argtypes = [
        c_char_p,
        c_void_p,
        c_size_t,
        c_char_p,
        c_char_p,
        c_char_p,
        POINTER(c_void_p),
        POINTER(c_size_t),
        POINTER(c_void_p),
        POINTER(c_void_p),
        POINTER(c_void_p),
    ]
    dll.platform_file_facts_v2_direct_rebuild_compare_buffer_bytes_profile_alloc.restype = c_int
    _configure_text_function(dll, "platform_file_facts_v2_listing_rows_with_analysis_path_json_alloc", 4)
    _configure_text_function(dll, "platform_file_facts_v2_listing_rows_with_analysis_and_text_path_json_alloc", 4)
    _configure_text_function(dll, "platform_file_facts_v2_basic_listing_rows_path_json_alloc", 4)
    _configure_text_function(dll, "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc", 5)
    _configure_text_function(dll, "platform_file_facts_v2_listing_rows_with_analysis_and_text_raw_path_json_alloc", 5)
    _configure_text_function(dll, "platform_file_facts_v2_basic_listing_rows_raw_path_json_alloc", 5)
    _configure_text_function(dll, "platform_file_type_catalog_json_alloc", 1)
    _configure_text_function(dll, "platform_file_naming_catalog_json_alloc", 1)
    _configure_text_function(dll, "platform_file_os_metadata_catalog_json_alloc", 1)
    _configure_text_function(dll, "platform_file_api_input_struct_json_alloc", 5)
    dll.platform_file_assemble_source_path_bytes_profile_alloc.argtypes = [
        c_char_p,
        c_char_p,
        c_char_p,
        c_char_p,
        c_int,
        POINTER(c_void_p),
        POINTER(c_size_t),
        POINTER(c_void_p),
        POINTER(c_void_p),
    ]
    dll.platform_file_assemble_source_path_bytes_profile_alloc.restype = c_int
    dll.platform_file_assemble_source_path_to_output_bytes_profile_alloc.argtypes = [
        c_char_p,
        c_char_p,
        c_char_p,
        c_char_p,
        c_char_p,
        c_int,
        POINTER(c_void_p),
        POINTER(c_size_t),
        POINTER(c_void_p),
        POINTER(c_void_p),
    ]
    dll.platform_file_assemble_source_path_to_output_bytes_profile_alloc.restype = c_int
    dll.platform_file_assemble_source_text_bytes_profile_alloc.argtypes = [
        c_char_p,
        c_char_p,
        c_char_p,
        c_char_p,
        c_int,
        POINTER(c_void_p),
        POINTER(c_size_t),
        POINTER(c_void_p),
        POINTER(c_void_p),
    ]
    dll.platform_file_assemble_source_text_bytes_profile_alloc.restype = c_int
    dll.platform_file_assemble_source_text_to_output_bytes_profile_alloc.argtypes = [
        c_char_p,
        c_char_p,
        c_char_p,
        c_char_p,
        c_char_p,
        c_int,
        POINTER(c_void_p),
        POINTER(c_size_t),
        POINTER(c_void_p),
        POINTER(c_void_p),
    ]
    dll.platform_file_assemble_source_text_to_output_bytes_profile_alloc.restype = c_int
    return dll


@cache
def _platform_disk_dll(project_root: Path) -> CDLL:
    dll = _load_dll(project_root, "platform_disk_lib.dll")
    dll.platform_disk_free_text.argtypes = [c_void_p]
    dll.platform_disk_free_text.restype = None
    dll.platform_disk_free_bytes.argtypes = [c_void_p]
    dll.platform_disk_free_bytes.restype = None
    _configure_text_function(dll, "platform_disk_inspect_path_json_alloc", 2)
    dll.platform_disk_extract_entry_path_bytes_alloc.argtypes = [
        c_char_p,
        c_char_p,
        c_char_p,
        POINTER(c_void_p),
        POINTER(c_size_t),
        POINTER(c_void_p),
    ]
    dll.platform_disk_extract_entry_path_bytes_alloc.restype = c_int
    return dll


def _load_dll(project_root: Path, name: str) -> CDLL:
    build_dir = project_root / "src" / "build"
    dll_path = build_dir / name
    if not dll_path.exists():
        raise FileNotFoundError(f"Missing C backend DLL: {dll_path}")
    if hasattr(os, "add_dll_directory"):
        _dll_directory_handles.append(os.add_dll_directory(str(build_dir)))
    return CDLL(str(dll_path))


def _configure_text_function(dll: CDLL, function_name: str, input_arg_count: int) -> None:
    function = getattr(dll, function_name)
    argtypes: list[object] = [c_char_p] * input_arg_count + [POINTER(c_void_p)]
    if "raw_path" in function_name:
        argtypes = [c_char_p, c_char_p, c_uint32, *([c_char_p] * (input_arg_count - 3)), POINTER(c_void_p)]
    function.argtypes = argtypes
    function.restype = c_int


_dll_directory_handles: list[object] = []


class _CBackendSourceFile:
    def __init__(self, path: Path, platform_name: str, entry_offset: int | None = None) -> None:
        self.path = path
        self.platform_name = platform_name
        self.entry_offset = entry_offset


@contextmanager
def _source_file_for_c_backend(
    binary_source: BinarySource,
    *,
    project_root: Path,
) -> Iterator[_CBackendSourceFile]:
    if isinstance(binary_source, HunkFileBinarySource):
        yield _CBackendSourceFile(binary_source.path, _platform_file_name_for_path(binary_source.path))
        return
    if isinstance(binary_source, DiskEntryBinarySource):
        data = binary_source.read_bytes()
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(binary_source.entry_path).suffix) as temp_file:
                temp_file.write(data)
                temp_path = Path(temp_file.name)
            yield _CBackendSourceFile(temp_path, _platform_file_name_for_disk_path(binary_source.adf_path))
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
        return
    if isinstance(binary_source, RawBinarySource):
        yield _CBackendSourceFile(binary_source.path, "amiga-raw", binary_source.local_entrypoint)
        return
    raise UnsupportedCBackendProject(f"C backend does not support binary source: {binary_source.display_path}")


def facts_v2_asm_source_project_source_with_c_backend(
    binary_source: BinarySource,
    *,
    metadata_path: Path | None = None,
    project_root: Path = PROJECT_ROOT,
) -> str:
    metadata_text = _metadata_path_text(metadata_path)
    with _source_file_for_c_backend(binary_source, project_root=project_root) as source_file:
        if source_file.entry_offset is None:
            return _platform_file_text(
                "platform_file_facts_v2_asm_source_path_text_alloc",
                source_file.platform_name,
                str(source_file.path),
                metadata_text,
                project_root=project_root,
            )
        return _platform_file_text(
            "platform_file_facts_v2_asm_source_raw_path_text_alloc",
            source_file.platform_name,
            str(source_file.path),
            source_file.entry_offset,
            metadata_text,
            project_root=project_root,
        )


def facts_v2_asm_source_project_with_c_backend_profile(
    project_name: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> tuple[str, dict[str, object]]:
    paths = resolve_project_paths(project_name, project_root=project_root)
    with effective_metadata_file(paths.target_dir) as metadata_path:
        return facts_v2_asm_source_project_source_with_c_backend_profile(
            paths.binary_source,
            metadata_path=metadata_path,
            project_root=project_root,
        )


def facts_v2_asm_source_project_source_with_c_backend_profile(
    binary_source: BinarySource,
    *,
    metadata_path: Path | None = None,
    project_root: Path = PROJECT_ROOT,
) -> tuple[str, dict[str, object]]:
    metadata_text = _metadata_path_text(metadata_path)
    with _source_file_for_c_backend(binary_source, project_root=project_root) as source_file:
        if source_file.entry_offset is None:
            source_text, profile_dict = _platform_file_facts_v2_source_text_profile(
                "platform_file_facts_v2_asm_source_path_text_profile_alloc",
                source_file.platform_name,
                str(source_file.path),
                metadata_text,
                project_root=project_root,
            )
        else:
            source_text, profile_dict = _platform_file_facts_v2_source_text_profile(
                "platform_file_facts_v2_asm_source_raw_path_text_profile_alloc",
                source_file.platform_name,
                str(source_file.path),
                source_file.entry_offset,
                metadata_text,
                project_root=project_root,
            )
    if facts_v2_source_refused(profile_dict) and not _facts_v2_asm_source_has_lossy_numeric_output(
        profile_dict
    ):
        return "", profile_dict
    return source_text, profile_dict


def _facts_v2_asm_source_has_lossy_numeric_output(profile: dict[str, object]) -> bool:
    facts_v2 = profile.get("facts_v2")
    if not isinstance(facts_v2, dict):
        return False
    value = facts_v2.get("asm_source_lossy_numeric_hunk_relocations")
    return isinstance(value, int) and value > 0


def _platform_include_dir_for_listing(platform_name: str, project_root: Path) -> Path:
    if platform_name == "atari-st":
        return project_root / "ext" / "atarist_includes" / "devpac_3_10" / "include"
    return project_root / "ext" / "amiga_includes" / "ndk_2.0" / "include"


def _benchmark_from_facts_v2_asm_source_profile(profile: dict[str, object]) -> dict[str, object]:
    facts_v2 = profile.get("facts_v2")
    facts_v2_dict = dict(facts_v2) if isinstance(facts_v2, dict) else {}
    return {
        "benchmark_version": 1,
        "platform": profile.get("backend"),
        "path": profile.get("path"),
        "analysis_backend": "facts_v2",
        "facts_v2": facts_v2_dict,
        "analysis": {
            "recovered_platform_base_slot_count": _profile_int(
                facts_v2_dict, "platform_base_slot_count"
            ),
            "recovered_platform_call_count": _profile_int(
                facts_v2_dict, "platform_call_count"
            ),
            "recovered_platform_effect_count": _profile_int(
                facts_v2_dict, "platform_effect_count"
            ),
        },
        "render": {
            "symbol_ref_count": 0,
            "symbol_ref_abs_count": 0,
            "symbol_ref_pc_relative_count": 0,
            "symbol_ref_section_relative_count": 0,
            "statement_count": _profile_int(facts_v2_dict, "render_ir_statements"),
            "label_statement_count": _profile_int(facts_v2_dict, "render_ir_labels"),
            "instruction_statement_count": _profile_int(facts_v2_dict, "render_ir_instructions"),
            "data_statement_count": _profile_int(facts_v2_dict, "render_ir_data_spans"),
            "symbolic_instruction_count": _profile_int(facts_v2_dict, "asm_source_symbolic_instructions"),
            "text_bytes": _profile_int(facts_v2_dict, "asm_source_bytes"),
        },
        "timing": _facts_v2_benchmark_timing(profile, facts_v2_dict),
    }


def _facts_v2_benchmark_timing(
    profile: dict[str, object],
    facts_v2: dict[object, object],
) -> dict[str, object]:
    timing = dict(profile["timing"]) if isinstance(profile.get("timing"), dict) else {}
    decode_seconds = _profile_float(facts_v2, "decode_seconds")
    seed_seconds = _profile_float(facts_v2, "seed_seconds")
    fixed_point_seconds = _profile_float(facts_v2, "fixed_point_seconds")
    render_ir_seconds = _profile_float(facts_v2, "render_ir_seconds")
    source_render_seconds = _profile_float(facts_v2, "source_render_seconds")
    timing.update(
        {
            "decode_seconds": decode_seconds,
            "seed_seconds": seed_seconds,
            "fixed_point_seconds": fixed_point_seconds,
            "render_ir_seconds": render_ir_seconds,
            "source_render_seconds": source_render_seconds,
            "analysis_seconds": round(decode_seconds + seed_seconds + fixed_point_seconds, 6),
            "ir_build_seconds": render_ir_seconds,
            "render_seconds": source_render_seconds,
        }
    )
    return timing


def _profile_int(payload: dict[object, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return 0
    return value if isinstance(value, int) else 0


def _profile_float(payload: dict[object, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool):
        return 0.0
    return round(float(value), 6) if isinstance(value, (int, float)) else 0.0


def _platform_file_name_for_path(path: Path) -> str:
    if path.suffix.lower() in {".prg", ".tos", ".ttp"}:
        return "atari-st"
    return "amiga-hunk"


def _platform_file_name_for_disk_path(path: Path) -> str:
    if path.suffix.lower() in {".st", ".msa"}:
        return "atari-st"
    return "amiga-hunk"


def _platform_disk_name_for_path(path: Path) -> str:
    if path.suffix.lower() in {".st", ".msa"}:
        return "atari-st-disk"
    return "amiga-disk"
