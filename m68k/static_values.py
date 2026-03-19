"""Shared KB-driven static register/base value reconstruction helpers."""

from . import constant_evaluator


def _resolve_block_constant_reg(instructions, kb,
                                reg_mode: str, reg_num: int,
                                stop_before: int) -> int | None:
    """Resolve a simple concrete register value from local deterministic writes."""
    return constant_evaluator.resolve_constant_reg(
        instructions, kb, reg_mode, reg_num, stop_before)
