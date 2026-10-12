"""Stdio MCP adapter for the existing local restoration service.

Install the ``mcp`` optional extra. No analysis state is owned by this process.
"""

from __future__ import annotations

import argparse
import json
from typing import Literal

from amiga_reversing.disasm.restoration_client import (
    RestorationClient,
    RestorationClientError,
)


def create_server(client: RestorationClient):
    from mcp.server import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
    from mcp.types import ToolAnnotations

    def call(project: str, operation: str, **parameters: object) -> dict[str, object]:
        try:
            return client.call(project, operation, **parameters)
        except RestorationClientError as exc:
            raise ToolError(json.dumps(exc.payload, ensure_ascii=False)) from exc

    server = MCPServer(
        "Amiga source restoration",
        instructions="Use state until ready, inspect bounded native facts, then interpret through catalog commands. Mutations require the revision you inspected; never retry a stale write automatically. Timeouts are observations under stated conditions, not proof of unreachability.",
    )
    read = ToolAnnotations(
        read_only_hint=True, destructive_hint=False, open_world_hint=False
    )
    write = ToolAnnotations(
        read_only_hint=False, destructive_hint=False, open_world_hint=False
    )

    @server.tool(annotations=read, structured_output=True)
    def restoration_state(project: str) -> dict[str, object]:
        """Prepare/read current analysis, its revision, readiness and remaining gaps."""
        return call(project, "state")

    @server.tool(annotations=read, structured_output=True)
    def restoration_export(
        project: str, assembler_profile: Literal["vasm", "devpac"] = "vasm",
        binary_assets: bool = False, minimum_asset_size: int = 256,
    ) -> dict[str, object]:
        """Export source or a vasm ZIP package through the shared source-export operation. Export is not verification."""
        return call(project, "export", assembler_profile=assembler_profile,
                    binary_assets=binary_assets, minimum_asset_size=minimum_asset_size)

    @server.tool(annotations=read, structured_output=True)
    def restoration_query(
        project: str,
        kind: Literal[
            "symbols",
            "references",
            "fields",
            "instructions",
            "edges",
            "functions",
            "gaps",
        ],
        expected_revision: str,
        query: str | None = None,
        relation: Literal[
            "callers",
            "callees",
            "ranges",
            "owned_blocks",
            "unresolved_transfers",
            "entry_evidence",
            "name_evidence",
        ]
        | None = None,
        section_index: int | None = None,
        source_offset: int | None = None,
        end_offset: int | None = None,
        symbol: str | None = None,
        struct_name: str | None = None,
        field_offset: int | None = None,
        direction: Literal["incoming", "outgoing", "both"] | None = None,
        limit: int = 25,
        cursor: str | None = None,
    ) -> dict[str, object]:
        """Query compact native facts, with revision-bound pagination (limit 1–100). Unknown indirect transfers remain explicit."""
        parameters = {
            "kind": kind,
            "relation": relation,
            "expected_revision": expected_revision,
            "query": query,
            "section_index": section_index,
            "source_offset": source_offset,
            "end_offset": end_offset,
            "symbol": symbol,
            "struct_name": struct_name,
            "field_offset": field_offset,
            "direction": direction,
            "limit": limit,
            "cursor": cursor,
        }
        return call(
            project,
            "query",
            **{key: value for key, value in parameters.items() if value is not None},
        )

    @server.tool(annotations=read, structured_output=True)
    def restoration_inspect(
        project: str,
        expected_revision: str,
        source_offset: int,
        section_index: int = 0,
        row_kind: Literal["instruction", "label", "data"] | None = None,
    ) -> dict[str, object]:
        """Inspect a canonical source coordinate, related facts and available commands."""
        return call(
            project,
            "inspect",
            expected_revision=expected_revision,
            section_index=section_index,
            source_offset=source_offset,
            **({"row_kind": row_kind} if row_kind else {}),
        )

    @server.tool(annotations=write, structured_output=True)
    def restoration_interpret(
        project: str,
        expected_revision: str,
        command_id: str,
        context: dict,
        parameters: dict,
        question: str,
        reason: str,
        source_evidence_status: Literal["hypothesis", "analysis_proven"],
        source_evidence_refs: list[str],
    ) -> dict[str, object]:
        """Apply a discovered catalog command with evidence. Preserves action history; a stale revision is refused."""
        return call(
            project,
            "interpret",
            expected_revision=expected_revision,
            command_id=command_id,
            context=context,
            parameters=parameters,
            evidence={
                "question": question,
                "reason": reason,
                "source_evidence_status": source_evidence_status,
                "source_evidence_refs": source_evidence_refs,
            },
        )

    @server.tool(annotations=write, structured_output=True)
    def restoration_verify(project: str, expected_revision: str) -> dict[str, object]:
        """Regenerate source and check exact reproduction; record a revision-bound receipt."""
        return call(project, "verify", expected_revision=expected_revision)

    @server.tool(annotations=write, structured_output=True)
    def restoration_probe(
        project: str,
        expected_revision: str,
        question: str,
        scenario: str,
        verification_id: str,
    ) -> dict[str, object]:
        """Run a configured bounded runtime probe associated with an explicit question and exact-build receipt."""
        return call(
            project,
            "probe",
            expected_revision=expected_revision,
            question=question,
            scenario=scenario,
            verification_id=verification_id,
        )

    @server.tool(annotations=write, structured_output=True)
    def restoration_review(
        project: str,
        expected_revision: str,
        action_id: str,
        decision: Literal["accept", "defer", "reject"],
        reason: str,
        verification_id: str | None = None,
        probe_id: str | None = None,
    ) -> dict[str, object]:
        """Append a review decision with supporting verification/probe receipts; never erase earlier work."""
        return call(
            project,
            "review",
            expected_revision=expected_revision,
            action_id=action_id,
            decision=decision,
            reason=reason,
            verification_id=verification_id,
            probe_id=probe_id,
        )

    @server.tool(annotations=write, structured_output=True)
    def restoration_rollback(
        project: str, expected_revision: str, action_id: str, redo: bool = False
    ) -> dict[str, object]:
        """Undo or redo a manual action through existing append-only history semantics."""
        return call(
            project,
            "rollback",
            expected_revision=expected_revision,
            action_id=action_id,
            redo=redo,
        )

    @server.tool(annotations=read, structured_output=True)
    def restoration_history(
        project: str, expected_revision: str, limit: int = 25, cursor: str | None = None
    ) -> dict[str, object]:
        """Read bounded action and evidence history, including superseded interpretations."""
        return call(
            project,
            "history",
            expected_revision=expected_revision,
            limit=limit,
            cursor=cursor,
        )

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", default="http://127.0.0.1:8123")
    args = parser.parse_args()
    create_server(RestorationClient(args.server)).run(transport="stdio")


if __name__ == "__main__":
    main()
