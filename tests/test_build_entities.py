from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import disassemble
from m68k.indirect_core import IndirectSite, IndirectSiteStatus
from m68k_kb import runtime_m68k_analysis
from m68k.name_entities import name_subroutines
from m68k.os_calls import AppSlotInfo


def test_build_entities_help_loads_cleanly():
    script = Path(__file__).resolve().parent.parent / "scripts" / "build_entities.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Build entities.jsonl from hunk binary analysis" in result.stdout


def _load_build_entities_module():
    path = Path(__file__).resolve().parent.parent / "scripts" / "build_entities.py"
    spec = importlib.util.spec_from_file_location("build_entities_script", path)
    if spec is None or spec.loader is None:
        raise ValueError("Unable to load build_entities.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_subroutine_app_slots_uses_containing_struct_region():
    module = _load_build_entities_module()
    inst = disassemble(assemble_instruction("movea.l 4300(a6),a0"), max_cpu="68010")[0]
    sub = module.SubroutineRange(addr=0x20, end=0x24, block_count=1, instr_count=1)
    blocks = {
        0x20: SimpleNamespace(start=0x20, instructions=[inst]),
    }
    slot_infos = (
        AppSlotInfo(
            offset=0x10B8,
            symbol="app_timer_device_iorequest",
            usages=(),
            struct="IO",
            size=48,
            named_base="timer.device",
        ),
    )

    app_slots = module.collect_subroutine_app_slots(sub, blocks, slot_infos, 6)

    assert app_slots == (
        module.ReferencedAppSlot(
            offset=0x10B8,
            symbol="app_timer_device_iorequest",
            struct="IO",
            size=48,
            pointer_struct=None,
            named_base="timer.device",
        ),
    )


def test_app_slot_entity_payloads_emit_struct_and_named_base():
    module = _load_build_entities_module()

    payloads = module.app_slot_entity_payloads((
        module.ReferencedAppSlot(
            offset=0x0CD6,
            symbol="app_dos_library_base",
            struct=None,
            size=None,
            pointer_struct="DosLibrary",
            named_base="dos.library",
        ),
    ))

    assert payloads == [{
        "offset": "0x0CD6",
        "symbol": "app_dos_library_base",
        "kind": "struct_pointer",
        "pointer_struct": "DosLibrary",
        "named_base": "dos.library",
    }]


def test_app_slot_entity_payloads_format_negative_offsets():
    module = _load_build_entities_module()

    payloads = module.app_slot_entity_payloads((
        module.ReferencedAppSlot(
            offset=-2,
            symbol="app_freemem_memoryblock",
            struct=None,
            size=None,
            pointer_struct=None,
            named_base=None,
        ),
    ))

    assert payloads == [{
        "offset": "-0x0002",
        "symbol": "app_freemem_memoryblock",
    }]


def test_summarize_entity_app_slots_adds_direct_and_transitive_summaries():
    module = _load_build_entities_module()
    entities = [
        {
            "addr": "0x0000",
            "end": "0x0010",
            "type": "code",
            "calls": ["0x0100"],
            "app_slots": [{
                "offset": "0x10B8",
                "symbol": "app_timer_device_iorequest",
                "struct": "IO",
                "named_base": "timer.device",
            }],
        },
        {
            "addr": "0x0100",
            "end": "0x0110",
            "type": "code",
            "app_slots": [{
                "offset": "0x0CD6",
                "symbol": "app_dos_library_base",
                "kind": "struct_pointer",
                "pointer_struct": "DosLibrary",
                "named_base": "dos.library",
            }],
        },
    ]

    module.summarize_entity_app_slots(entities)

    assert entities[0]["named_bases"] == ["timer.device"]
    assert entities[0]["struct_refs"] == ["IO"]
    assert entities[0]["named_bases_transitive"] == ["dos.library", "timer.device"]
    assert entities[0]["struct_refs_transitive"] == ["DosLibrary", "IO"]
    assert entities[1]["named_bases"] == ["dos.library"]
    assert entities[1]["struct_refs"] == ["DosLibrary"]


def test_collect_subroutine_indirect_sites_keeps_dispatch_metadata():
    module = _load_build_entities_module()
    sub = module.SubroutineRange(addr=0x20, end=0x40, block_count=1, instr_count=1)
    sites = [
        IndirectSite(
            addr=0x24,
            mnemonic="jsr",
            flow_type=runtime_m68k_analysis.FlowType.CALL,
            shape="index.brief",
            status=IndirectSiteStatus.PER_CALLER,
            target=None,
            detail="dispatch",
            target_count=2,
        ),
    ]

    indirect_sites = module.collect_subroutine_indirect_sites(sub, sites)

    assert indirect_sites == (
        module.ReferencedIndirectSite(
            addr=0x24,
            shape="index.brief",
            status="per_caller",
            flow="call",
            detail="dispatch",
            target_count=2,
        ),
    )


def test_name_subroutines_uses_transitive_named_base_for_dispatch_wrapper():
    entities = [{
        "addr": "0x0010",
        "end": "0x0018",
        "type": "code",
        "named_bases_transitive": ["dos.library"],
        "indirect_sites": [{
            "addr": "0x0014",
            "shape": "index.brief",
            "status": "per_caller",
            "flow": "call",
        }],
    }]

    named = name_subroutines(entities, {}, b"", [])

    assert named == 1
    assert entities[0]["name"] == "dos_dispatch"
