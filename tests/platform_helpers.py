from __future__ import annotations

from typing import TYPE_CHECKING

from m68k.os_calls import (
    AppBaseInfo,
    AppBaseKind,
    CallEffect,
    PlatformState,
    ScratchReg,
    get_platform_config,
)

if TYPE_CHECKING:
    from m68k.m68k_executor import AbstractMemory, CallSummary


def make_platform(
    *,
    scratch_regs: tuple[ScratchReg, ...] | None = None,
    app_base: AppBaseInfo | tuple[int, int] | None = None,
    initial_mem: AbstractMemory | None = None,
    pending_call_effect: CallEffect | None = None,
    summary_cache: dict[int, CallSummary | None] | None = None,
) -> PlatformState:
    platform = get_platform_config()
    if scratch_regs is not None:
        platform.scratch_regs = tuple(scratch_regs)
    if app_base is not None:
        if isinstance(app_base, tuple):
            platform.app_base = AppBaseInfo(
                kind=AppBaseKind.DYNAMIC,
                reg_num=app_base[0],
                concrete=app_base[1],
            )
        else:
            platform.app_base = app_base
    if initial_mem is not None:
        platform.initial_mem = initial_mem
    if pending_call_effect is not None:
        platform.pending_call_effect = pending_call_effect
    if summary_cache is not None:
        platform.summary_cache = summary_cache
    return platform
