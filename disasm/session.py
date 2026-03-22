"""Build canonical post-analysis disassembly sessions."""

from pathlib import Path

from m68k.hunk_parser import parse_file, HunkType
from m68k.indirect_core import IndirectSiteStatus
from m68k.os_calls import (analyze_call_setups, build_app_struct_regions,
                           propagate_typed_memory_regions)
from disasm.absolute_resolver import resolve_absolute_labels
from disasm.analysis_loader import load_hunk_analysis
from disasm.data_access import collect_data_access_sizes
from disasm.discovery import apply_generic_data_label_promotions
from disasm.entities import infer_target_name, load_entities
from disasm.hardware_symbols import collect_hardware_base_regs
from disasm.hunks import build_hunk_session, build_session_object, prepare_hunk_code
from disasm.metadata import build_hunk_metadata
from disasm.substitutions import (build_arg_substitutions,
                                  build_lvo_substitutions)
from m68k.os_calls import build_app_slot_symbols
from disasm.types import DisassemblySession, HunkDisassemblySession

def build_disassembly_session(binary_path: str, entities_path: str,
                              output_path: str | None = None,
                              base_addr: int = 0, code_start: int = 0,
                              profile_stages: bool = False) -> DisassemblySession:
    hf = parse_file(binary_path)
    entities = load_entities(entities_path)
    target_dir = Path(entities_path).parent if Path(entities_path).parent.exists() else None
    target_name = infer_target_name(target_dir, entities_path)
    hunk_sessions: list[HunkDisassemblySession] = []

    for hunk in hf.hunks:
        if hunk.hunk_type != HunkType.HUNK_CODE:
            continue

        code = hunk.data
        code_size = len(code)
        hunk_entities = [e for e in entities if e.get("hunk") == hunk.index]
        hunk_entities.sort(key=lambda e: int(e["addr"], 16))

        ha = load_hunk_analysis(
            binary_path=binary_path,
            code=code,
            relocs=hunk.relocs,
            hunk_index=hunk.index,
            base_addr=base_addr,
            code_start=code_start,
        )

        blocks = ha.blocks
        hint_blocks = ha.hint_blocks
        jt_list = ha.jump_tables
        lib_calls = ha.lib_calls
        os_kb = ha.os_kb
        platform = ha.platform
        reloc_targets = ha.reloc_targets
        exit_states = ha.exit_states
        relocated_segments = ha.relocated_segments
        code, code_size, relocated_segments, reloc_file_offset, reloc_base_addr = (
            prepare_hunk_code(code, relocated_segments)
        )
        absolute_resolution = resolve_absolute_labels(
            platform=platform,
        )
        call_setup_analysis = analyze_call_setups(
            blocks=blocks,
            lib_calls=lib_calls,
            os_kb=os_kb,
            code=code,
            platform=platform,
        )
        metadata = build_hunk_metadata(
            code=code,
            code_size=code_size,
            hunk_index=hunk.index,
            hunk_entities=hunk_entities,
            ha=ha,
            hf_hunks=hf.hunks,
            typed_string_ranges=call_setup_analysis.string_ranges,
            reserved_absolute_addrs=absolute_resolution.reserved_absolute_addrs,
            absolute_labels=absolute_resolution.absolute_labels,
        )
        code_addrs = metadata.code_addrs
        hint_blocks = metadata.hint_blocks
        hint_addrs = metadata.hint_addrs
        reloc_map = metadata.reloc_map
        reloc_target_set = metadata.reloc_target_set
        reserved_absolute_addrs = metadata.reserved_absolute_addrs
        pc_targets = metadata.pc_targets
        string_addrs = metadata.string_addrs
        generic_data_label_addrs = metadata.generic_data_label_addrs
        jt_regions = metadata.jump_table_regions
        jt_target_sources = metadata.jump_table_target_sources
        labels = metadata.labels
        string_ranges = metadata.string_ranges
        absolute_labels = metadata.absolute_labels

        region_map = propagate_typed_memory_regions(blocks, lib_calls, code, os_kb, platform)
        app_struct_regions = build_app_struct_regions(blocks, lib_calls, os_kb, platform)
        hardware_base_regs = collect_hardware_base_regs(blocks, code, platform)

        lvo_equs, lvo_substitutions = build_lvo_substitutions(
            blocks=blocks,
            lib_calls=lib_calls,
            hunk_entities=hunk_entities,
        )
        arg_equs, arg_substitutions = build_arg_substitutions(
            blocks=blocks,
            lib_calls=lib_calls,
            hunk_entities=hunk_entities,
            os_kb=os_kb,
        )
        app_offsets = build_app_slot_symbols(
            blocks=blocks,
            lib_calls=lib_calls,
            code=code,
            os_kb=os_kb,
            platform=platform,
        )

        arg_annotations = call_setup_analysis.arg_annotations
        apply_generic_data_label_promotions(
            labels,
            pc_targets,
            generic_data_label_addrs,
            call_setup_analysis.segment_data_symbols,
        )
        for addr, symbol in call_setup_analysis.segment_code_symbols.items():
            labels[addr] = symbol
        data_access_sizes = collect_data_access_sizes(blocks, exit_states)
        unresolved_indirects = {
            site.addr: site
            for site in ha.indirect_sites
            if site.status == IndirectSiteStatus.UNRESOLVED
        }

        hunk_sessions.append(build_hunk_session(
            hunk_index=hunk.index,
            code=code,
            code_size=code_size,
            entities=hunk_entities,
            blocks=blocks,
            hint_blocks=hint_blocks,
            code_addrs=code_addrs,
            hint_addrs=hint_addrs,
            reloc_map=reloc_map,
            reloc_target_set=reloc_target_set,
            reserved_absolute_addrs=reserved_absolute_addrs,
            pc_targets=pc_targets,
            string_addrs=string_addrs,
            string_ranges=string_ranges,
            labels=labels,
            absolute_labels=absolute_labels,
            jump_table_regions=jt_regions,
            jump_table_target_sources=jt_target_sources,
            region_map=region_map,
            app_struct_regions=app_struct_regions,
            hardware_base_regs=hardware_base_regs,
            lvo_equs=lvo_equs,
            lvo_substitutions=lvo_substitutions,
            arg_equs=arg_equs,
            arg_substitutions=arg_substitutions,
            app_offsets=app_offsets,
            arg_annotations=arg_annotations,
            data_access_sizes=data_access_sizes,
            platform=platform,
            os_kb=os_kb,
            base_addr=base_addr,
            code_start=code_start,
            relocated_segments=relocated_segments,
            reloc_file_offset=reloc_file_offset,
            reloc_base_addr=reloc_base_addr,
            unresolved_indirects=unresolved_indirects,
        ))

    return build_session_object(
        target_name=target_name,
        binary_path=Path(binary_path),
        entities_path=Path(entities_path),
        output_path=Path(output_path) if output_path else None,
        entities=entities,
        hunk_sessions=hunk_sessions,
        profile_stages=profile_stages,
    )




