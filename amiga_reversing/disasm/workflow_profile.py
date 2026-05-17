from __future__ import annotations

import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass(slots=True)
class WorkflowSpan:
    name: str
    seconds: float
    module: str
    detail: dict[str, object] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "name": self.name,
            "seconds": round(float(self.seconds), 6),
            "module": self.module,
        }
        if self.detail:
            payload["detail"] = dict(self.detail)
        return payload


@dataclass(slots=True)
class WorkflowProfile:
    workflow_id: str
    target_id: str | None = None
    input_stamp: dict[str, object] | None = None
    spans: list[WorkflowSpan] = field(default_factory=list)
    counters: dict[str, int | float | str | bool] = field(default_factory=dict)

    def add_span(
        self,
        name: str,
        seconds: float,
        *,
        module: str,
        detail: Mapping[str, object] | None = None,
    ) -> WorkflowSpan:
        span = WorkflowSpan(
            name=name,
            seconds=max(0.0, float(seconds)),
            module=module,
            detail=dict(detail or {}),
        )
        self.spans.append(span)
        return span

    @contextmanager
    def span(
        self,
        name: str,
        *,
        module: str,
        detail: Mapping[str, object] | None = None,
    ) -> Iterator[None]:
        started_at = time.perf_counter()
        try:
            yield
        finally:
            self.add_span(name, time.perf_counter() - started_at, module=module, detail=detail)

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "workflow_id": self.workflow_id,
            "spans": [span.to_payload() for span in self.spans],
        }
        if self.target_id is not None:
            payload["target_id"] = self.target_id
        if self.input_stamp is not None:
            payload["input_stamp"] = dict(self.input_stamp)
        if self.counters:
            payload["counters"] = dict(self.counters)
        return payload


def workflow_profile_payload(profile: WorkflowProfile | None) -> dict[str, object] | None:
    return profile.to_payload() if profile is not None else None
