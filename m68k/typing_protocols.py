"""Shared typing protocols for reusable M68K analysis helpers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, Self

from .abstract_values import AbstractValue

if TYPE_CHECKING:
    from disasm.decode import DecodedInstructionForEmit


class MemoryLike(Protocol):
    def read(self, addr: int | AbstractValue, size: str) -> AbstractValue: ...

    def copy(self) -> Self: ...


class CpuStateLike(Protocol):
    @property
    def d(self) -> Sequence[AbstractValue]: ...

    @property
    def a(self) -> Sequence[AbstractValue]: ...

    @property
    def sp(self) -> AbstractValue: ...

    def get_reg(self, mode: str, reg: int) -> AbstractValue: ...
    def copy(self) -> Self: ...
    def set_reg(self, mode: str, reg: int, val: AbstractValue) -> None: ...


class OperandNodeLike(Protocol):
    @property
    def kind(self) -> str: ...

    @property
    def register(self) -> str | None: ...

    @property
    def value(self) -> int | None: ...


class DecodedOperandLike(Protocol):
    @property
    def mode(self) -> str: ...

    @property
    def reg(self) -> int | None: ...

    @property
    def value(self) -> int | None: ...

    @property
    def full_extension(self) -> bool: ...

    @property
    def memory_indirect(self) -> bool: ...

    @property
    def base_suppressed(self) -> bool: ...

    @property
    def index_suppressed(self) -> bool: ...

    @property
    def postindexed(self) -> bool: ...

    @property
    def index_is_addr(self) -> bool: ...

    @property
    def index_reg(self) -> int | None: ...

    @property
    def base_displacement(self) -> int | None: ...

    @property
    def outer_displacement(self) -> int | None: ...


class DecodedOperandsLike(Protocol):
    @property
    def ea_op(self) -> DecodedOperandLike | None: ...

    @property
    def dst_op(self) -> DecodedOperandLike | None: ...

    @property
    def reg_num(self) -> int | None: ...

    @property
    def imm_val(self) -> int | None: ...


class InstructionLike(Protocol):
    @property
    def offset(self) -> int: ...

    @property
    def size(self) -> int: ...

    @property
    def kb_mnemonic(self) -> str | None: ...

    @property
    def opcode_text(self) -> str | None: ...

    @property
    def operand_size(self) -> str | None: ...

    @property
    def operand_nodes(self) -> Sequence[OperandNodeLike] | None: ...

    @property
    def raw(self) -> bytes: ...

    @property
    def decoded_operands(self) -> DecodedInstructionForEmit | None: ...


class BasicBlockLike(Protocol):
    @property
    def instructions(self) -> Sequence[InstructionLike]: ...


class SuccessorBlockLike(BasicBlockLike, Protocol):
    @property
    def successors(self) -> Sequence[int]: ...
