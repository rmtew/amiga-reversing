"""Shared KB-driven static register/base value reconstruction helpers."""

from __future__ import annotations

from collections.abc import Sequence

from . import constant_evaluator
from .constant_evaluator import SizedInstructionLike


def _resolve_block_constant_reg(instructions: Sequence[SizedInstructionLike], reg_mode: str, reg_num: int,
                                stop_before: int) -> int | None:
    """Resolve a simple concrete register value from local deterministic writes."""
    return constant_evaluator.resolve_constant_reg(
        instructions, reg_mode, reg_num, stop_before)
