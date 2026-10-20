"""Shared, revision-bound restoration operations over native facts and histories.

No semantic state is stored here: native artifacts are disposable projections,
manual actions own edits, and the Decision Journal owns review decisions.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import uuid
from contextlib import nullcontext
from datetime import UTC, datetime

from amiga_reversing.disasm.decision_journal import (
    append_decision_records,
    decision_journal_next_prev,
    project_decision_journal,
    read_decision_journal,
)
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_action,
    load_manual_projection,
    manual_action_interpretation,
)
from amiga_reversing.disasm.target_history import history_revision, target_lock

_FUNCTION_CACHE: dict[tuple[str, str], dict] = {}
_QUERY_KEYS = {"kind", "query", "section_index", "source_offset", "end_offset", "symbol",
               "struct_name", "field_offset", "direction", "relation", "exceptions_only"}


def _server():
    from amiga_reversing.disasm import server
    return server


def _paths(target_id):
    server = _server()
    return server.resolve_project_paths(target_id, project_root=server.PROJECT_ROOT)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def revisions(target_id: str) -> dict[str, str]:
    """Call under target_lock when used for optimistic concurrency."""
    directory = _paths(target_id).target_dir
    manual = directory / "manual_actions.jsonl"
    from amiga_reversing.disasm.binary_source import read_binary_source_bytes
    subject = _digest({"analysis": _server()._project_listing_cache_key(target_id),
                       "source_sha256": hashlib.sha256(read_binary_source_bytes(_paths(target_id).binary_source)).hexdigest(),
                       "manual": hashlib.sha256(manual.read_bytes() if manual.exists() else b"").hexdigest()})
    return {"subject_revision": subject,
            "revision": _digest({"subject": subject, "history": history_revision(directory)})}


def require_revision(target_id, expected, *, current=None):
    if current is None:
        current = revisions(target_id)
    if not isinstance(expected, str) or expected != current["revision"]:
        raise ValueError("stale_revision: supply the exact revision from the inspected state; reload before deciding")
    return current


def _artifact(target_id):
    server = _server()
    key = server._project_listing_cache_key(target_id)
    artifact = server._LISTING_PROJECTION_SERVICE.valid_artifact(target_id, key)
    if artifact is None:
        raise ValueError("analysis_not_ready: call restoration state and wait until ready")
    return artifact


def _records(target_id):
    path = _paths(target_id).target_dir / "manual_actions.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()][1:] if path.exists() else []


def _history(target_id, *, subject_revision=None, journal=None):
    records = _records(target_id)
    projection = load_manual_projection(_paths(target_id).target_dir, binary_source=_paths(target_id).binary_source)
    active_ids = set(projection.active_action_ids)
    if journal is None:
        journal = read_decision_journal(_paths(target_id).target_dir)
    if not journal["valid"]:
        raise ValueError("invalid_decision_history: repair history before restoration")
    decisions = journal.get("records", [])
    projected = project_decision_journal(decisions)
    by_action = {}
    for bucket in ("accepted_facts", "deferred_facts", "rejected_facts"):
        for record in projected[bucket]:
            if record.get("fact_type") == "restoration_interpretation":
                action_id = record.get("selected_identity", {}).get("subject_id")
                if action_id in by_action:
                    raise ValueError("conflicting interpretation decisions require explicit supersession")
                by_action[action_id] = record
    subject = subject_revision if subject_revision is not None else revisions(target_id)["subject_revision"]
    result = []
    for record in records:
        action_id = record.get("action_id")
        evidence = manual_action_interpretation(record)
        decision = by_action.get(action_id)
        status = "unassessed" if "interpretation" not in record else "hypothesis"
        if decision:
            status = {"accept_fact": "accepted", "defer_fact": "deferred", "reject_fact": "rejected"}[decision["action"]]
        result.append({"action_id": action_id, "kind": record.get("kind"), "sequence": record.get("sequence"),
                       "active": action_id in active_ids, "interpretation": evidence, "status": status,
                       "decision": decision, "verification_current": bool(decision and decision.get("subject_revision") == subject)})
    return result


def _page(items, offset, limit, scope=None, unknowns=None):
    return {"items": items[offset:offset + limit], "total": len(items), "offset": offset,
            "limit": limit, "has_more": offset + limit < len(items),
            "scope": scope or "current accepted analysis", "unknowns": unknowns or []}


def _pagination(body, revision, filters):
    limit = body.get("limit", 30)
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    offset = 0
    cursor = body.get("cursor")
    if cursor is not None:
        if not isinstance(cursor, str) or not cursor or len(cursor) > 2048:
            raise ValueError("invalid cursor")
        try:
            payload = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            if payload["revision"] != revision or payload["filters"] != _digest(filters):
                raise ValueError("stale_cursor: revision or filters changed")
            offset = payload["offset"]
            if type(offset) is not int or offset < 0:
                raise ValueError("invalid cursor offset")
        except (KeyError, TypeError, UnicodeError, json.JSONDecodeError, binascii.Error) as exc:
            raise ValueError("invalid cursor") from exc
    return offset, limit


def _preview(value, path, truncated):
    if isinstance(value, str) and len(value) > 1024:
        truncated.append(path)
        return value[:1024] + "…"
    if isinstance(value, list):
        if len(value) > 32:
            truncated.append(path)
        return [_preview(v, f"{path}.{i}", truncated) for i, v in enumerate(value[:32])]
    if isinstance(value, dict):
        if len(value) > 32:
            truncated.append(path)
        if path.count(".") > 6:
            truncated.append(path)
            return {"preview_truncated": True}
        return {k[:128]: _preview(v, f"{path}.{k[:128]}", truncated) for k, v in list(value.items())[:32]}
    return value


def _envelope(page, current, filters):
    # Responses have a byte budget as well as an item limit. History may contain
    # arbitrarily long legacy notes; preserve them on disk, expose explicit previews.
    page = dict(page)
    previews = []
    truncated = []
    for index, item in enumerate(page["items"]):
        previews.append(_preview(item, str(index), truncated))
    for index, item in enumerate(previews):
        if len(json.dumps(item).encode()) > 16384:
            identity = {k: item[k] for k in ("action_id", "kind", "section_index", "source_offset", "name") if k in item} if isinstance(item, dict) else {}
            previews[index] = {**identity, "preview_truncated": True,
                               "reason": "Record exceeds the 16 KiB detail preview budget; original history is preserved."}
            truncated.append(f"items.{index}")
    page["items"] = previews
    while len(page["items"]) > 1 and len(json.dumps(page).encode()) > 60000:
        page["items"].pop()
    page["has_more"] = page["offset"] + len(page["items"]) < page["total"]
    if truncated:
        page["truncated_fields"] = [path[:96] for path in truncated[:20]]
        page["truncated_field_count"] = len(truncated)
    page["response_byte_budget"] = 65536
    cursor = None
    if page["has_more"]:
        cursor = base64.urlsafe_b64encode(json.dumps({"revision": current["revision"],
                "filters": _digest(filters), "offset": page["offset"] + len(page["items"])}).encode()).decode()
    return {**page, **current, "next_cursor": cursor}


def _source_identity(value):
    """A source identity requires both concrete coordinates; zero is valid."""
    if not isinstance(value, dict):
        return None
    section, offset = value.get("section_index"), value.get("source_offset")
    if not all(type(coordinate) is int and 0 <= coordinate <= 0xFFFFFFFF
               for coordinate in (section, offset)):
        return None
    return section, offset


def _query(target_id, body, current):
    filters = {k: v for k, v in body.items() if k in _QUERY_KEYS}
    offset, limit = _pagination(body, current["revision"], filters)
    for name in ("query", "symbol", "struct_name", "direction"):
        if name in filters and (not isinstance(filters[name], str) or len(filters[name]) > 256):
            raise ValueError(f"{name} must be a string of at most 256 characters")
    for name in ("section_index", "source_offset", "end_offset"):
        if name in filters and (type(filters[name]) is not int or not 0 <= filters[name] <= 0xFFFFFFFF):
            raise ValueError(f"{name} must be a nonnegative 32-bit integer")
    if "field_offset" in filters and (type(filters["field_offset"]) is not int or not -0x80000000 <= filters["field_offset"] <= 0x7FFFFFFF):
        raise ValueError("field_offset must be a signed 32-bit integer")
    kind = filters.get("kind")
    if "exceptions_only" in filters and kind != "typed_pointers":
        raise ValueError("exceptions_only requires typed_pointers")
    if filters.get("query") and kind in {"references", "fields", "edges", "gaps"}:
        raise ValueError(f"query text is unsupported for {kind}")
    artifact = _artifact(target_id)
    if kind == "functions":
        from amiga_reversing.disasm.function_facts import analysis_function_facts
        key = (target_id, current["subject_revision"])
        facts = _FUNCTION_CACHE.get(key)
        if facts is None:
            analysis, _ = artifact.analysis_payload()
            _FUNCTION_CACHE.clear()  # one disposable projection; no unbounded revision retention
            facts = analysis_function_facts(target_id, analysis)
            _FUNCTION_CACHE[key] = facts
        items = facts["functions"]
        if filters.get("query"):
            items = [i for i in items if filters["query"].lower() in str(i.get("name", "")).lower()]
        if filters.get("section_index") is not None:
            items = [i for i in items if i["section_index"] == filters["section_index"]]
        if filters.get("source_offset") is not None:
            items = [i for i in items if i["source_offset"] == filters["source_offset"]]
        # Relationships have their own paged edge query; a function page cannot embed an unbounded graph.
        compact = [{k: v for k, v in i.items() if k not in {"callers", "callees", "owned_blocks", "ranges", "unresolved_transfers", "entry_evidence", "name_evidence", "shared_block_starts"}} |
                   {"entry_evidence_count": len(i.get("entry_evidence", [])), "range_count": len(i.get("ranges", [])), "caller_count": len(i.get("callers", [])),
                    "callee_count": len(i.get("callees", [])), "unresolved_transfer_count": len(i.get("unresolved_transfers", []))}
                   for i in items]
        relation = filters.get("relation")
        if relation is not None:
            if relation not in {"callers", "callees", "ranges", "owned_blocks", "unresolved_transfers", "entry_evidence", "name_evidence"}:
                raise ValueError("unknown function relation")
            if filters.get("source_offset") is None or filters.get("section_index") is None or len(items) != 1:
                raise ValueError("function relations require one section_index/source_offset candidate")
            page = _page(items[0].get(relation, []), offset, limit,
                         "native CFG function candidate relation", items[0].get("unknowns"))
        else:
            page = _page(compact, offset, limit, unknowns=facts.get("unknowns"))
    elif kind == "typed_pointers":
        from amiga_reversing.disasm.effective_metadata import effective_target_metadata
        from amiga_reversing.disasm.typed_pointer_report import typed_pointer_report
        unsupported = set(filters) - {"kind", "struct_name", "exceptions_only",
                                      "section_index", "source_offset", "end_offset"}
        if unsupported:
            raise ValueError("typed_pointers supports only source interval, struct_name and exceptions_only filtering")
        metadata = effective_target_metadata(_paths(target_id).target_dir)
        if metadata is None:
            raise ValueError("Target metadata is required")
        page = typed_pointer_report(
            metadata, artifact.row_for_source_offset,
            offset=offset, limit=limit, struct_name=filters.get("struct_name"),
            section_index=filters.get("section_index"), source_offset=filters.get("source_offset"),
            end_offset=filters.get("end_offset"),
            exceptions_only=filters.get("exceptions_only", False),
        )
        page.pop("next_offset", None)
        page["scope"] = "canonical bound pointer fields and native render-plan outcomes"
        page["unknowns"] = page.pop("limits")
    elif kind == "memory_regions":
        if set(filters) != {"kind"}:
            raise ValueError("memory_regions currently supports only pagination")
        native = artifact.memory_regions_payload()
        page = _page(native["items"], offset, limit, native["scope"],
                     ["Region definition does not establish access closure or legal placement."])
    elif kind == "gaps":
        items = _server()._cached_analysis_review_items(target_id, artifact)
        page = _page(items, offset, limit, "native analysis review items",
                     ["Review items are candidates, not a complete inventory of semantic unknowns."])
    elif kind in {"symbols", "references", "fields", "instructions", "edges"}:
        page = artifact.query_payload(**filters, offset=offset, limit=limit)
        if kind == "symbols":
            interpretations = _history(target_id, subject_revision=current["subject_revision"])
            for item in page["items"]:
                identity = _source_identity(item)
                matching = [entry for entry in interpretations if identity is not None and entry["active"]
                    and _source_identity(entry["interpretation"].get("subject")) == identity]
                item["interpretations"] = [{"action_id": entry["action_id"], "status": entry["status"],
                    "verification_current": entry["verification_current"], "evidence": entry["interpretation"]}
                    for entry in matching[-4:]]
                if not matching:
                    item["interpretation_status"] = "unassessed"
    else:
        raise ValueError("unknown query kind")
    return _envelope(page, current, filters)


def _inspect(target_id, body, current):
    section, offset = body.get("section_index", 0), body.get("source_offset")
    if type(section) is not int or type(offset) is not int or offset < 0:
        raise ValueError("inspect needs section_index and nonnegative source_offset")
    row = _artifact(target_id).row_for_source_offset(section_index=section, offset=offset)
    if row is None:
        raise ValueError("source location not found")
    if body.get("row_kind") == "label":
        window, _ = _artifact(target_id).window_payload(start=max(0, row.get("row_index", 0) - 2), count=5)
        row = next((candidate for candidate in window["rows"] if candidate.get("kind") == "label"
                    and candidate.get("section_index") == section and candidate.get("start_offset") == offset), None)
        if row is None:
            raise ValueError("no canonical label at source location")
    locator = _server()._LISTING_PROJECTION_SERVICE.locator_for_row(
        target_id=target_id, projection_hash=_server()._project_listing_cache_key(target_id), row=row).to_dict()
    catalog_query = {"context": ["row"], "locator": [json.dumps(locator)]}
    if row.get("kind") == "label":
        from amiga_reversing.disasm.listing_context import listing_element_contexts
        elements = listing_element_contexts(row)
        label = next((element for element in elements if element.get("element_kind") == "label"), None)
        if label is not None:
            catalog_query.update(context=["element"], element_id=[label["element_id"]])
    catalog = _server()._command_catalog_payload(target_id, catalog_query)
    instructions = _query(target_id, {"kind": "instructions", "section_index": section,
                           "source_offset": offset, "end_offset": offset + 128, "limit": 27}, current)
    relationships = {kind: _query(target_id, {"kind": kind, "section_index": section,
                     "source_offset": offset, "limit": 30}, current) for kind in ("references", "edges")}
    key = row.get("stable_key") or row.get("row_key")
    interpretations = [h for h in _history(target_id, subject_revision=current["subject_revision"]) if key in h["interpretation"].get("evidence_refs", [])]
    function = _query(target_id, {"kind": "functions", "section_index": section,
                       "source_offset": offset, "limit": 1}, current)
    return {**current, "locator": locator, "function": function, "instructions": instructions,
            "relationships": relationships, "interpretations": _preview(interpretations[-30:], "interpretations", []), "commands": catalog,
            "unknowns": ["A source name is an interpretation, not evidence of runtime reachability."]}


def _interpretation_body(target_id, body, current, artifact):
    evidence = body.get("evidence")
    if not isinstance(evidence, dict) or not str(evidence.get("reason", "")).strip():
        raise ValueError("interpretation needs a concrete reason and source evidence")
    refs = evidence.get("evidence_refs", evidence.get("source_evidence_refs"))
    if not isinstance(refs, list) or not 1 <= len(refs) <= 32:
        raise ValueError("supply 1..32 canonical source evidence references")
    for ref in refs:
        match = re.fullmatch(r"s(\d+):([0-9A-Fa-f]{8}):[a-z_]+", str(ref))
        if not match:
            raise ValueError("evidence must use canonical source row keys")
        row = artifact.row_for_source_offset(section_index=int(match[1]), offset=int(match[2], 16))
        if row is None or (row.get("stable_key") or row.get("row_key")) != ref:
            raise ValueError("evidence reference is not a current canonical row")
    metadata = {**evidence, "evidence_refs": refs, "subject_revision": current["subject_revision"]}
    context = body.get("context", {})
    locator = context.get("locator", {}) if isinstance(context, dict) else {}
    metadata["subject"] = {"section_index": locator.get("section_index"),
        "source_offset": locator.get("start_offset"), "row_key": locator.get("row_key"),
        "command_id": body.get("command_id")}
    metadata.pop("source_evidence_refs", None)
    metadata.setdefault("source_evidence_status", "hypothesis")
    return {**body, "interpretation": metadata}


def _interpret(target_id, body, current):
    prepared = _interpretation_body(target_id, body, current, _artifact(target_id))
    return _server()._execute_command_unchecked(target_id, prepared)


def _interpret_batch(target_id, body, current):
    entries = body.get("entries")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 100:
        raise ValueError("interpret_batch requires 1..100 entries")
    if any(not isinstance(entry, dict) or "expected_revision" in entry or "operation" in entry
           for entry in entries):
        raise ValueError("batch entries must be interpretation parameters without operation or expected_revision")
    artifact = _artifact(target_id)
    prepared = [_interpretation_body(target_id, entry, current, artifact) for entry in entries]
    return _server()._execute_catalog_commands_unchecked(target_id, prepared)


def _prepare_review_records(target_id, body, current, item, chain):
    action_id, choice, reason = item["action_id"], body["decision"], body["reason"]
    refs = item["interpretation"].get("evidence_refs", [])
    record = {"schema": "evidence-decision/v1", "decision_id": f"restoration-{uuid.uuid4().hex}",
              "created_at": datetime.now(UTC).isoformat(), "actor": {"kind": "tool", "name": "restoration"},
              "action": {"accept": "accept_fact", "defer": "defer_fact", "reject": "reject_fact"}[choice],
              "candidate_id": f"restoration:{action_id}", "selected_identity": {"target_id": target_id,
                 "subject_kind": "action", "subject_id": action_id}, "evidence_refs": refs,
              "conflicts": [], "fact_type": "restoration_interpretation", "scope": {"kind": "manual_action"},
              "reason": reason, "subject_revision": current["subject_revision"],
              "verification_id": body.get("verification_id"), "probe_id": body.get("probe_id"),
              "prev": decision_journal_next_prev(chain)}
    if choice != "accept":
        record[f"{choice}_reason"] = reason
    batch = []
    previous = item.get("decision")
    if previous:
        supersession = {"schema": "evidence-decision/v1", "decision_id": f"restoration-{uuid.uuid4().hex}",
            "created_at": datetime.now(UTC).isoformat(), "actor": {"kind": "tool", "name": "restoration"},
            "action": "supersede_decision", "supersedes_decision_id": previous["decision_id"],
            "replacement_decision_id": record["decision_id"], "reason": reason,
            "prev": decision_journal_next_prev(chain)}
        batch.append(supersession)
        record["prev"] = decision_journal_next_prev([supersession])
    return [*batch, record], record


def _review_many(target_id, body, current, action_ids):
    from amiga_reversing.disasm import restoration_verification as verification
    choice, reason = body.get("decision"), body.get("reason")
    if choice not in {"accept", "defer", "reject"} or not isinstance(reason, str) or not reason.strip():
        raise ValueError("review requires accept/defer/reject and a reason")
    directory = _paths(target_id).target_dir
    journal = read_decision_journal(directory)
    history = _history(target_id, subject_revision=current["subject_revision"], journal=journal)
    by_id = {item["action_id"]: item for item in history}
    items = []
    for action_id in action_ids:
        item = by_id.get(action_id) if isinstance(action_id, str) else None
        if item is None or not item["active"]:
            raise ValueError("review requires a current active manual action")
        if not item["interpretation"].get("evidence_refs", []):
            raise ValueError("legacy action has no evidence; revise it through an evidence-bearing command before review")
        items.append(item)
    proof = None
    if choice == "accept":
        proof = verification.load_receipt(target_id, body.get("verification_id"))
        if proof.get("kind") != "verification" or proof.get("subject_revision") != current["subject_revision"] or proof.get("exact") is not True:
            raise ValueError("accept requires exact rebuild evidence for the current source subject")
    probe = None
    if body.get("probe_id"):
        probe = verification.load_receipt(target_id, body["probe_id"])
        if probe.get("kind") != "probe" or probe.get("subject_revision") != current["subject_revision"]:
            raise ValueError("probe belongs to a stale source subject")
    chain = list(journal.get("records", []))
    additions, decisions = [], []
    for item in items:
        records, decision = _prepare_review_records(target_id, body, current, item, chain)
        additions.extend(records)
        chain.extend(records)
        decisions.append(decision)
    _discard_read_snapshot(target_id)
    result = append_decision_records(directory, additions)
    if result["status"] != "appended":
        raise ValueError(f"decision rejected: {result.get('diagnostics')}")
    return {"decisions": decisions, "verification": proof, "probe": probe}


def _review(target_id, body, current):
    result = _review_many(target_id, body, current, [body.get("action_id")])
    return {"decision": result["decisions"][0], "verification": result["verification"], "probe": result["probe"]}


def _review_batch(target_id, body, current):
    action_ids = body.get("action_ids")
    if not isinstance(action_ids, list) or not 1 <= len(action_ids) <= 100:
        raise ValueError("review_batch requires 1..100 action_ids")
    if any(not isinstance(identity, str) or not identity or len(identity) > 256 for identity in action_ids):
        raise ValueError("review_batch action_ids must be nonempty strings of at most 256 characters")
    if len(set(action_ids)) != len(action_ids):
        raise ValueError("review_batch action_ids must be unique")
    reason = body.get("reason")
    if isinstance(reason, str) and len(reason) > 4096:
        raise ValueError("review_batch reason must contain at most 4096 characters")
    result = _review_many(target_id, body, current, action_ids)
    def receipt_preview(receipt):
        return None if receipt is None else {key: receipt[key] for key in ("receipt_id", "kind", "subject_revision", "exact") if key in receipt}
    return {"decisions": [{"action_id": record["selected_identity"]["subject_id"],
                           "decision_id": record["decision_id"], "action": record["action"]}
                          for record in result["decisions"]],
            "verification": receipt_preview(result["verification"]), "probe": receipt_preview(result["probe"])}


def _discard_read_snapshot(target_id):
    discard = getattr(_server(), "_discard_listing_read_snapshot", None)
    if discard is not None:
        discard(target_id)


def execute(target_id: str, body: dict) -> dict:
    """One shared operation boundary for HTTP, UI, CLI and MCP."""
    operation = body.get("operation")
    directory = _paths(target_id).target_dir
    snapshot = getattr(_server(), "_listing_read_snapshot", nullcontext)
    with target_lock(directory), snapshot():
        current = revisions(target_id)
        if operation in {"interpret", "interpret_batch", "command", "verify", "probe", "behaviour", "review", "review_batch", "rollback", "memory_plan", "memory_build"}:
            current = require_revision(target_id, body.get("expected_revision"), current=current)
        elif body.get("expected_revision") is not None:
            current = require_revision(target_id, body["expected_revision"], current=current)
        if operation == "state":
            server = _server()
            artifact = server._LISTING_PROJECTION_SERVICE.valid_artifact(target_id, server._project_listing_cache_key(target_id))
            job = None if artifact is not None else server._start_listing_job(target_id, retry_failed=False)
            history = _history(target_id, subject_revision=current["subject_revision"])
            return {**current, "ready": artifact is not None, "job": job,
                    "history_summary": {"actions": len(history), "unassessed": sum(i["status"] == "unassessed" for i in history)},
                    "unknowns": ["Semantic interpretations require evidence; exact bytes alone do not validate meaning."]}
        if operation == "query":
            return _query(target_id, body, current)
        if operation == "inspect":
            return _inspect(target_id, body, current)
        if operation == "history":
            filters = {"operation": "history"}
            offset, limit = _pagination(body, current["revision"], filters)
            return _envelope(_page(list(reversed(_history(target_id, subject_revision=current["subject_revision"]))), offset, limit), current, filters)
        if operation == "interpret":
            result = _interpret(target_id, body, current)
        elif operation == "interpret_batch":
            result = _interpret_batch(target_id, body, current)
        elif operation == "command":
            result = _server()._execute_command_unchecked(target_id, body)
        elif operation in {"verify", "probe", "behaviour"}:
            from amiga_reversing.disasm import restoration_verification as verification
            if operation == "verify":
                result = verification.verify(target_id, current["subject_revision"], artifact=_artifact(target_id))
            elif operation == 'behaviour':
                result = verification.run_behaviour(target_id,current['subject_revision'],body)
            else:
                receipt = verification.load_receipt(target_id, body.get("verification_id"))
                result = verification.run_probe(target_id, current["subject_revision"], body.get("question"),
                    body.get("scenario"), receipt)
            if revisions(target_id)["subject_revision"] != current["subject_revision"]:
                raise ValueError("source changed during verification; receipt is not current")
        elif operation in {"memory_plan", "memory_build"}:
            from amiga_reversing.disasm.memory_regions import relocation_plan, build_derived_artifact
            artifact = _artifact(target_id)
            plan = relocation_plan(artifact, body.get("region_id"), body.get("destination"), body.get("memory_class"))
            if operation == "memory_plan":
                result = {"plan": plan}
            else:
                from amiga_reversing.disasm import restoration_verification as verification
                receipt = verification.load_receipt(target_id, body.get("verification_id"))
                verification._verified_receipt(target_id, current["subject_revision"], receipt)
                result = build_derived_artifact(target_id, artifact, plan, current["subject_revision"])
        elif operation == "review":
            result = _review(target_id, body, current)
        elif operation == "review_batch":
            result = _review_batch(target_id, body, current)
        elif operation == "rollback":
            action_id = body.get("action_id")
            records = _records(target_id)
            if not any(r.get("action_id") == action_id and r.get("kind") not in {"undo_action", "redo_action"} for r in records):
                raise ValueError("rollback requires a source action id")
            redo = body.get("redo", False)
            _discard_read_snapshot(target_id)
            action = append_manual_action(directory, kind=ManualActionKind.REDO_ACTION if redo else ManualActionKind.UNDO_ACTION,
                payload={"redoes_action_id" if redo else "undoes_action_id": action_id}, binary_source=_paths(target_id).binary_source)
            _server()._clear_project_listing_cache(target_id, keep_stale_artifact=True)
            result = {"action": action}
        else:
            raise ValueError("unknown restoration operation")
        _discard_read_snapshot(target_id)
        return {**result, **revisions(target_id)}
