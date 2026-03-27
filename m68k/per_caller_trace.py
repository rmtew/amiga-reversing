from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Any

from .m68k_executor import AbstractMemory, CPUState


def _value_signature(val: Any) -> tuple[Any, ...]:
    return (
        bool(getattr(val, "is_known", False)),
        getattr(val, "concrete", None) if getattr(val, "is_known", False) else None,
        getattr(val, "sym_base", None),
        getattr(val, "sym_offset", None),
        getattr(val, "label", None),
        repr(getattr(val, "tag", None)),
    )


def cpu_signature(cpu: CPUState) -> tuple[Any, ...]:
    return (
        tuple(_value_signature(val) for val in cpu.d),
        tuple(_value_signature(val) for val in cpu.a),
        _value_signature(cpu.sp),
    )


def register_projection(
    cpu: CPUState,
    regs: list[tuple[str, int]] | tuple[tuple[str, int], ...],
) -> dict[str, tuple[Any, ...]]:
    return {
        f"{mode}{num}": _value_signature(cpu.get_reg(mode, num))
        for mode, num in regs
    }


def mem_signature(mem: AbstractMemory) -> tuple[Any, ...]:
    bytes_sig = tuple(sorted((addr, _value_signature(val)) for addr, val in mem._bytes.items()))
    tags_sig = tuple(sorted((repr(key), repr(tag)) for key, tag in mem._tags.items()))
    return bytes_sig, tags_sig


def state_signature(cpu: CPUState, mem: AbstractMemory) -> tuple[Any, ...]:
    return cpu_signature(cpu), mem_signature(mem)


@dataclass(slots=True)
class PerCallerTrace:
    path: Path
    _lock: Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._lock = Lock()

    def event(self, kind: str, **payload: Any) -> None:
        record = {"kind": kind, "ts": round(perf_counter(), 6), **payload}
        line = json.dumps(record, separators=(",", ":"))
        with self._lock, self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


_TRACE: PerCallerTrace | None | object = None


def get_per_caller_trace() -> PerCallerTrace | None:
    global _TRACE
    if _TRACE is not None:
        return None if _TRACE is False else _TRACE
    raw = os.environ.get("AMIGA_PER_CALLER_TRACE")
    if not raw:
        _TRACE = False
        return None
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    _TRACE = PerCallerTrace(path)
    return _TRACE
