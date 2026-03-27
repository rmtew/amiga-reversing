from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter


@dataclass(slots=True)
class PhaseTimer:
    totals: dict[str, float] = field(default_factory=dict)

    @contextmanager
    def phase(self, name: str) -> Iterator[None]:
        started = perf_counter()
        try:
            yield
        finally:
            self.totals[name] = self.totals.get(name, 0.0) + (perf_counter() - started)

    def value(self, name: str) -> float:
        return self.totals.get(name, 0.0)
