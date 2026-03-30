from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"
_PROFILE_PATHS = {
    "vasm": _KNOWLEDGE_DIR / "asm_vasm.json",
    "devpac": _KNOWLEDGE_DIR / "asm_devpac.json",
}


@dataclass(frozen=True, slots=True)
class AssemblerDirectiveProfile:
    include: str
    section: str
    equ: str
    dc_b: str
    dc_w: str
    dc_l: str
    ds_b: str
    dcb_b: str


@dataclass(frozen=True, slots=True)
class AssemblerIncludeAdapter:
    prelude_lines: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AssemblerRenderProfile:
    assembler_id: str
    header_generated_syntax: str
    comment_prefix: str
    blank_line: str
    line_ending: str
    directives: AssemblerDirectiveProfile
    include_adapters: dict[str, AssemblerIncludeAdapter]
    string_delimiters: tuple[str, ...]
    unsupported_hint_operand_kinds: tuple[str, ...]
    current_location_token: str | None
    omit_zero_pc_index_displacement: bool
    require_label_anchor_for_self_relative_data: bool
    auto_align_dc_w: bool
    auto_align_dc_l: bool


@dataclass(frozen=True, slots=True)
class AssemblerProfile:
    assembler_id: str
    syntax_family: str
    local_include_root: str | None
    output_file_option: str | None
    render: AssemblerRenderProfile


def load_assembler_profile(profile_name: str) -> AssemblerProfile:
    profile_path = _PROFILE_PATHS.get(profile_name)
    if profile_path is None:
        raise ValueError(f"Unknown assembler profile: {profile_name}")
    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    render_payload = payload.get("render_profile")
    assert isinstance(render_payload, dict), (
        f"Missing render_profile in assembler KB: {profile_path}"
    )
    directives_payload = render_payload.get("directives")
    assert isinstance(directives_payload, dict), (
        f"Missing render_profile.directives in assembler KB: {profile_path}"
    )
    syntax_family = payload.get("syntax_family")
    assert isinstance(syntax_family, str) and syntax_family, (
        f"Missing syntax_family in assembler KB: {profile_path}"
    )
    local_include_root = payload.get("local_include_root")
    assert local_include_root is None or isinstance(local_include_root, str), (
        f"Invalid local_include_root in assembler KB: {profile_path}"
    )
    options_payload = payload.get("options", {})
    assert isinstance(options_payload, dict), (
        f"Invalid options in assembler KB: {profile_path}"
    )
    output_file_option = options_payload.get("output_file")
    assert output_file_option is None or isinstance(output_file_option, str), (
        f"Invalid options.output_file in assembler KB: {profile_path}"
    )
    assembler_id = render_payload.get("assembler_id")
    assert isinstance(assembler_id, str) and assembler_id, (
        f"Missing render_profile.assembler_id in assembler KB: {profile_path}"
    )
    header_generated_syntax = render_payload.get("header_generated_syntax")
    assert isinstance(header_generated_syntax, str) and header_generated_syntax, (
        f"Missing render_profile.header_generated_syntax in assembler KB: {profile_path}"
    )
    comment_prefix = render_payload.get("comment_prefix")
    assert isinstance(comment_prefix, str) and comment_prefix, (
        f"Missing render_profile.comment_prefix in assembler KB: {profile_path}"
    )
    blank_line = render_payload.get("blank_line")
    assert isinstance(blank_line, str), (
        f"Missing render_profile.blank_line in assembler KB: {profile_path}"
    )
    line_ending = render_payload.get("line_ending")
    assert line_ending in ("lf", "crlf"), (
        f"Missing or invalid render_profile.line_ending in assembler KB: {profile_path}"
    )
    include_directive = directives_payload.get("include")
    section_directive = directives_payload.get("section")
    equ_directive = directives_payload.get("equ")
    dc_b_directive = directives_payload.get("dc_b")
    dc_w_directive = directives_payload.get("dc_w")
    dc_l_directive = directives_payload.get("dc_l")
    ds_b_directive = directives_payload.get("ds_b")
    dcb_b_directive = directives_payload.get("dcb_b")
    assert isinstance(include_directive, str) and include_directive, (
        f"Missing render_profile.directives.include in assembler KB: {profile_path}"
    )
    assert isinstance(section_directive, str) and section_directive, (
        f"Missing render_profile.directives.section in assembler KB: {profile_path}"
    )
    assert isinstance(equ_directive, str) and equ_directive, (
        f"Missing render_profile.directives.equ in assembler KB: {profile_path}"
    )
    assert isinstance(dc_b_directive, str) and dc_b_directive, (
        f"Missing render_profile.directives.dc_b in assembler KB: {profile_path}"
    )
    assert isinstance(dc_w_directive, str) and dc_w_directive, (
        f"Missing render_profile.directives.dc_w in assembler KB: {profile_path}"
    )
    assert isinstance(dc_l_directive, str) and dc_l_directive, (
        f"Missing render_profile.directives.dc_l in assembler KB: {profile_path}"
    )
    assert isinstance(ds_b_directive, str) and ds_b_directive, (
        f"Missing render_profile.directives.ds_b in assembler KB: {profile_path}"
    )
    assert isinstance(dcb_b_directive, str) and dcb_b_directive, (
        f"Missing render_profile.directives.dcb_b in assembler KB: {profile_path}"
    )
    include_adapters_payload = render_payload.get("include_adapters", {})
    assert isinstance(include_adapters_payload, dict), (
        f"Invalid render_profile.include_adapters in assembler KB: {profile_path}"
    )
    include_adapters: dict[str, AssemblerIncludeAdapter] = {}
    for include_path, adapter_payload in include_adapters_payload.items():
        assert isinstance(include_path, str) and include_path, (
            f"Invalid include adapter key in assembler KB: {profile_path}"
        )
        assert isinstance(adapter_payload, dict), (
            f"Invalid include adapter payload for {include_path} in assembler KB: {profile_path}"
        )
        prelude_lines = adapter_payload.get("prelude_lines")
        assert isinstance(prelude_lines, list) and all(isinstance(line, str) for line in prelude_lines), (
            f"Invalid include adapter prelude_lines for {include_path} in assembler KB: {profile_path}"
        )
        include_adapters[include_path] = AssemblerIncludeAdapter(
            prelude_lines=tuple(prelude_lines),
        )
    string_delimiters_payload = render_payload.get("string_delimiters")
    assert isinstance(string_delimiters_payload, list) and all(
        isinstance(delimiter, str) and len(delimiter) == 1
        for delimiter in string_delimiters_payload
    ) and string_delimiters_payload, (
        f"Invalid render_profile.string_delimiters in assembler KB: {profile_path}"
    )
    unsupported_hint_operand_kinds_payload = render_payload.get("unsupported_hint_operand_kinds", [])
    assert isinstance(unsupported_hint_operand_kinds_payload, list) and all(
        isinstance(kind, str) and kind for kind in unsupported_hint_operand_kinds_payload
    ), (
        f"Invalid render_profile.unsupported_hint_operand_kinds in assembler KB: {profile_path}"
    )
    current_location_token = render_payload.get("current_location_token")
    assert current_location_token is None or (
        isinstance(current_location_token, str) and current_location_token
    ), (
        f"Invalid render_profile.current_location_token in assembler KB: {profile_path}"
    )
    omit_zero_pc_index_displacement = render_payload.get("omit_zero_pc_index_displacement", False)
    assert isinstance(omit_zero_pc_index_displacement, bool), (
        f"Invalid render_profile.omit_zero_pc_index_displacement in assembler KB: {profile_path}"
    )
    require_label_anchor_for_self_relative_data = render_payload.get(
        "require_label_anchor_for_self_relative_data", False
    )
    assert isinstance(require_label_anchor_for_self_relative_data, bool), (
        "Invalid render_profile.require_label_anchor_for_self_relative_data "
        f"in assembler KB: {profile_path}"
    )
    auto_align_dc_w = render_payload.get("auto_align_dc_w", False)
    assert isinstance(auto_align_dc_w, bool), (
        f"Invalid render_profile.auto_align_dc_w in assembler KB: {profile_path}"
    )
    auto_align_dc_l = render_payload.get("auto_align_dc_l", False)
    assert isinstance(auto_align_dc_l, bool), (
        f"Invalid render_profile.auto_align_dc_l in assembler KB: {profile_path}"
    )
    return AssemblerProfile(
        assembler_id=assembler_id,
        syntax_family=syntax_family,
        local_include_root=local_include_root,
        output_file_option=output_file_option,
        render=AssemblerRenderProfile(
            assembler_id=assembler_id,
            header_generated_syntax=header_generated_syntax,
            comment_prefix=comment_prefix,
            blank_line=blank_line,
            line_ending=line_ending,
            directives=AssemblerDirectiveProfile(
                include=include_directive,
                section=section_directive,
                equ=equ_directive,
                dc_b=dc_b_directive,
                dc_w=dc_w_directive,
                dc_l=dc_l_directive,
                ds_b=ds_b_directive,
                dcb_b=dcb_b_directive,
            ),
            include_adapters=include_adapters,
            string_delimiters=tuple(string_delimiters_payload),
            unsupported_hint_operand_kinds=tuple(unsupported_hint_operand_kinds_payload),
            current_location_token=current_location_token,
            omit_zero_pc_index_displacement=omit_zero_pc_index_displacement,
            require_label_anchor_for_self_relative_data=require_label_anchor_for_self_relative_data,
            auto_align_dc_w=auto_align_dc_w,
            auto_align_dc_l=auto_align_dc_l,
        ),
    )


VASM_PROFILE = load_assembler_profile("vasm")
