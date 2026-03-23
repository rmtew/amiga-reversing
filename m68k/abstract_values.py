"""Shared abstract value type and constructors for M68K analysis."""

from __future__ import annotations


class AbstractValue:
    """A value that may be concrete, symbolic (base+offset), or unknown."""

    __slots__ = ("_concrete", "sym_base", "sym_offset", "label", "tag")

    _concrete: int | None
    sym_base: str | None
    sym_offset: int | None
    label: str | None
    tag: object | None

    def __init__(self, concrete: int | None = None, sym_base: str | None = None,
                 sym_offset: int | None = None, label: str | None = None,
                 tag: object | None = None) -> None:
        self._concrete = concrete
        self.sym_base = sym_base
        self.sym_offset = sym_offset
        self.label = label
        self.tag = tag

    @property
    def is_known(self) -> bool:
        return self._concrete is not None

    @property
    def is_symbolic(self) -> bool:
        return self.sym_base is not None

    @property
    def concrete(self) -> int:
        assert self._concrete is not None, "Concrete value requested from non-concrete AbstractValue"
        return self._concrete

    def sym_add(self, delta: int) -> AbstractValue:
        assert self.sym_offset is not None, "Symbolic offset missing"
        return AbstractValue(sym_base=self.sym_base,
                             sym_offset=self.sym_offset + delta,
                             tag=self.tag)

    def __repr__(self) -> str:
        if self._concrete is not None:
            return f"${self._concrete:08x}"
        if self.sym_base is not None:
            off = self.sym_offset
            assert off is not None, "Symbolic offset missing"
            if off == 0:
                return self.sym_base
            return f"{self.sym_base}{off:+d}"
        return f"-{self.label or ''}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AbstractValue):
            return NotImplemented
        return (self._concrete == other._concrete
                and self.sym_base == other.sym_base
                and self.sym_offset == other.sym_offset
                and self.tag == other.tag)

    def __hash__(self) -> int:
        return hash((self._concrete, self.sym_base, self.sym_offset))


_UNKNOWN = AbstractValue()


def _concrete(val: int, tag: object | None = None) -> AbstractValue:
    return AbstractValue(concrete=val & 0xFFFFFFFF, tag=tag)


def _symbolic(base: str, offset: int = 0,
              tag: object | None = None) -> AbstractValue:
    return AbstractValue(sym_base=base, sym_offset=offset, tag=tag)


def _unknown(label: str = "", tag: object | None = None) -> AbstractValue:
    if not label and tag is None:
        return _UNKNOWN
    return AbstractValue(label=label, tag=tag)
