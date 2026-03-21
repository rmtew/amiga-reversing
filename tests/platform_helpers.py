from m68k.os_calls import PlatformState, get_platform_config


def make_platform(*, scratch_regs=None, initial_base_reg=None, initial_mem=None,
                  pending_call_effect=None, summary_cache=None) -> PlatformState:
    platform = get_platform_config()
    if scratch_regs is not None:
        platform.scratch_regs = tuple(scratch_regs)
    if initial_base_reg is not None:
        platform.initial_base_reg = initial_base_reg
    if initial_mem is not None:
        platform.initial_mem = initial_mem
    if pending_call_effect is not None:
        platform.pending_call_effect = pending_call_effect
    if summary_cache is not None:
        platform.summary_cache = summary_cache
    return platform
