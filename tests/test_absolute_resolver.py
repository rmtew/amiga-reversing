from __future__ import annotations

from disasm.absolute_resolver import resolve_absolute_labels
from m68k.os_calls import AppBaseInfo, AppBaseKind
from m68k_kb import runtime_hardware
from tests.platform_helpers import make_platform


def test_resolve_absolute_labels_keeps_hardware_addresses_reserved_and_app_base_labeled() -> None:
    platform = make_platform(app_base=AppBaseInfo(
        kind=AppBaseKind.ABSOLUTE,
        reg_num=6,
        concrete=0x8000,
    ))

    resolved = resolve_absolute_labels(platform=platform)

    assert resolved.absolute_labels[0x00000004] == "AbsExecBase"
    assert resolved.absolute_labels[0x00008000] == "app_base_00008000"
    assert 0x00008000 in resolved.reserved_absolute_addrs
    assert 0x00DFF000 in resolved.reserved_absolute_addrs
    assert 0x00BFE001 in resolved.reserved_absolute_addrs
    assert 0x00DFF000 not in resolved.absolute_labels
    assert 0x00BFE001 not in resolved.absolute_labels


def test_runtime_hardware_register_defs_classify_custom_and_cia_addresses() -> None:
    assert runtime_hardware.REGISTER_DEFS[0x00DFF09A] == {
        "symbol": "intena",
        "aliases": (),
        "family": "custom",
        "include": "hardware/custom.i",
        "base_symbol": "_custom",
        "offset": 0x9A,
    }
    assert runtime_hardware.REGISTER_DEFS[0x00BFE001] == {
        "symbol": "ciapra",
        "aliases": (),
        "family": "ciaa",
        "include": "hardware/cia.i",
        "base_symbol": "_ciaa",
        "offset": 0x0000,
    }
