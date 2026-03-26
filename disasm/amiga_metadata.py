from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import cast


def _json_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return value


@dataclass(frozen=True, slots=True)
class ResidentAutoinitMetadata:
    payload_offset: int
    base_size: int
    vectors_offset: int
    vector_format: str
    vector_offsets: tuple[int, ...]
    init_struct_offset: int | None
    init_func_offset: int | None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ResidentAutoinitMetadata:
        payload_offset = payload["payload_offset"]
        base_size = payload["base_size"]
        vectors_offset = payload["vectors_offset"]
        vector_format = payload["vector_format"]
        vector_offsets = payload["vector_offsets"]
        init_struct_offset = payload["init_struct_offset"]
        init_func_offset = payload["init_func_offset"]
        assert isinstance(payload_offset, int)
        assert isinstance(base_size, int)
        assert isinstance(vectors_offset, int)
        assert isinstance(vector_format, str)
        offsets = _json_list(vector_offsets)
        assert all(isinstance(item, int) for item in offsets)
        assert init_struct_offset is None or isinstance(init_struct_offset, int)
        assert init_func_offset is None or isinstance(init_func_offset, int)
        return cls(
            payload_offset=payload_offset,
            base_size=base_size,
            vectors_offset=vectors_offset,
            vector_format=vector_format,
            vector_offsets=tuple(cast(int, item) for item in offsets),
            init_struct_offset=init_struct_offset,
            init_func_offset=init_func_offset,
        )

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        assert isinstance(result, dict)
        return result
