from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class SessionHunkMetadata(TypedDict):
    hunk_index: int
    code_size: int
    entity_count: int
    label_count: int
    core_block_count: int
    hint_block_count: int
    jump_table_count: int
    relocated: bool
    execution_view_count: int


class SessionMetadata(TypedDict):
    target_name: str | None
    binary_path: str
    entities_path: str
    analysis_cache_path: str
    output_path: str | None
    entity_count: int
    hunk_count: int
    hunks: list[SessionHunkMetadata]


class ListingWindowPayload(TypedDict):
    anchor_addr: int | None
    start: int
    end: int
    has_more_before: bool
    has_more_after: bool
    total_rows: int
    analysis_generation: NotRequired[str | None]
    review_warnings: NotRequired[list[dict[str, object]]]
    rows: list[dict[str, object]]


def session_metadata(session: Any) -> SessionMetadata:
    return {
        "target_name": session.target_name,
        "binary_path": str(session.binary_path),
        "entities_path": str(session.entities_path),
        "analysis_cache_path": str(session.analysis_cache_path),
        "output_path": str(session.output_path) if session.output_path else None,
        "entity_count": len(session.entities),
        "hunk_count": len(session.hunk_sessions),
        "hunks": [
            {
                "hunk_index": hunk.hunk_index,
                "code_size": hunk.code_size,
                "entity_count": len(hunk.entities),
                "label_count": len(hunk.labels),
                "core_block_count": len(hunk.blocks),
                "hint_block_count": len(hunk.hint_blocks),
                "jump_table_count": len(hunk.jump_table_regions),
                "relocated": bool(hunk.execution_views),
                "execution_view_count": len(hunk.execution_views),
            }
            for hunk in session.hunk_sessions
        ],
    }


