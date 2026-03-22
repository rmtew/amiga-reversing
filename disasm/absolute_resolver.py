from __future__ import annotations

"""Resolve external absolute symbols from KB and analysis."""

from dataclasses import dataclass

from m68k.os_calls import AppBaseKind, PlatformState
from m68k_kb import runtime_hardware, runtime_os


@dataclass(slots=True)
class AbsoluteResolution:
    absolute_labels: dict[int, str]
    reserved_absolute_addrs: set[int]


def resolve_absolute_labels(*, platform: PlatformState) -> AbsoluteResolution:
    absolute_labels = {
        symbol.address: symbol.name
        for symbol in runtime_os.META.absolute_symbols
    }
    reserved_absolute_addrs = set(absolute_labels)
    for address in runtime_hardware.REGISTER_DEFS:
        reserved_absolute_addrs.add(address)

    app_base = platform.app_base
    if app_base is None or app_base.kind != AppBaseKind.ABSOLUTE:
        return AbsoluteResolution(
            absolute_labels=absolute_labels,
            reserved_absolute_addrs=reserved_absolute_addrs,
        )

    address = app_base.concrete
    label = f"app_base_{address:08X}"
    existing = absolute_labels.get(address)
    if existing is not None and existing != label:
        raise ValueError(
            f"Conflicting absolute label for ${address:08X}: "
            f"{existing!r} vs {label!r}"
        )
    absolute_labels[address] = label
    reserved_absolute_addrs.add(address)
    return AbsoluteResolution(
        absolute_labels=absolute_labels,
        reserved_absolute_addrs=reserved_absolute_addrs,
    )
