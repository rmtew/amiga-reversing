from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

from amiga_reversing.disasm.decision_journal import DECISION_JOURNAL_FILE_NAME
from amiga_reversing.disasm.manual_actions import MANUAL_ACTION_LOG_FILE_NAME
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_dir
from amiga_reversing.disasm.target_local_state import (
    OBSOLETE_TARGET_UI_EDITS_FILE_NAME,
    SOURCE_IMPORT_FACT_FILES,
)
from amiga_reversing.disasm.ui_preferences import UI_PREFERENCES_FILE_NAME


class TargetFileClass(StrEnum):
    SOURCE_IMPORT_FACT = "source_import_fact"
    GENERATED_OUTPUT = "generated_output"
    OBSOLETE_UI_STATE = "obsolete_ui_state"
    LOCAL_MANUAL_STATE = "local_manual_state"
    LOCAL_VERIFIER_STATE = "local_verifier_state"
    AGENT_AUDIT = "agent_audit"
    UNKNOWN = "unknown"


class TargetFileAction(StrEnum):
    PRESERVE = "preserve"
    DELETE_ON_CLEAN_RUN = "delete_on_clean_run"
    REGENERATE_ON_CLEAN_RUN = "regenerate_on_clean_run"
    PRESERVE_AGENT_AUDIT = "preserve_agent_audit"
    REVIEW_REQUIRED = "review_required"


GENERATED_OUTPUT_FILE_NAMES = frozenset(
    {
        "reproduction.json",
        "benchmark.json",
    }
)
GENERATED_OUTPUT_SUFFIXES = (".s", ".lst", ".map")
PROJECT_SOURCE_IMPORT_FACT_FILE_NAMES = frozenset(
    {
        "manifest.json",
        "target_state.json",
    }
)
OBSOLETE_UI_STATE_FILE_NAMES = frozenset(
    {
        OBSOLETE_TARGET_UI_EDITS_FILE_NAME,
        UI_PREFERENCES_FILE_NAME,
    }
)
LOCAL_VERIFIER_STATE_FILE_NAMES = frozenset(
    {
        "decision_verifier_artifacts.json",
    }
)


@dataclass(frozen=True, slots=True)
class TargetFileInventoryEntry:
    path: str
    file_class: TargetFileClass
    action: TargetFileAction
    reason: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["class"] = payload.pop("file_class")
        return payload


@dataclass(frozen=True, slots=True)
class TargetHygieneReport:
    target_id: str
    mode: str
    target_dir: str
    files: tuple[TargetFileInventoryEntry, ...]
    unknown_files: tuple[str, ...]
    safe_to_continue: bool
    safe_to_clean_run: bool
    safe_to_reimport: bool
    recommended_modes: tuple[str, ...]

    @property
    def safe_to_run(self) -> bool:
        return self.safe_to_continue and self.safe_to_clean_run

    def to_dict(self) -> dict[str, object]:
        return {
            "target_id": self.target_id,
            "mode": self.mode,
            "target_dir": self.target_dir,
            "files": [entry.to_dict() for entry in self.files],
            "unknown_files": list(self.unknown_files),
            "safe_to_continue": self.safe_to_continue,
            "safe_to_clean_run": self.safe_to_clean_run,
            "safe_to_reimport": self.safe_to_reimport,
            "safe_to_run": self.safe_to_run,
            "recommended_modes": list(self.recommended_modes),
        }


@dataclass(frozen=True, slots=True)
class TargetCleanupReport:
    target_id: str
    mode: str
    status: str
    target_dir: str
    before: TargetHygieneReport
    after: TargetHygieneReport
    deleted_files: tuple[str, ...]
    blocked_reason: str | None
    report_paths: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return {
            "target_id": self.target_id,
            "mode": self.mode,
            "status": self.status,
            "target_dir": self.target_dir,
            "before": self.before.to_dict(),
            "after": self.after.to_dict(),
            "deleted_files": list(self.deleted_files),
            "blocked_reason": self.blocked_reason,
            "report_paths": dict(self.report_paths),
        }


def inspect_target_hygiene(
    target_id: str,
    *,
    mode: str = "inspect",
    project_root: Path = PROJECT_ROOT,
) -> TargetHygieneReport:
    target_dir = resolve_project_dir(target_id, project_root=project_root)
    entries = tuple(_classify_target_files(target_dir))
    unknown_files = tuple(entry.path for entry in entries if entry.file_class is TargetFileClass.UNKNOWN)
    safe_to_continue = not unknown_files
    safe_to_clean_run = not unknown_files
    safe_to_reimport = not unknown_files
    modes = tuple(
        mode_name
        for mode_name, allowed in (
            ("continue", safe_to_continue),
            ("clean-run", safe_to_clean_run),
            ("reimport", safe_to_reimport),
        )
        if allowed
    )
    return TargetHygieneReport(
        target_id=target_id,
        mode=mode,
        target_dir=str(target_dir),
        files=entries,
        unknown_files=unknown_files,
        safe_to_continue=safe_to_continue,
        safe_to_clean_run=safe_to_clean_run,
        safe_to_reimport=safe_to_reimport,
        recommended_modes=modes,
    )


def clean_run_target_workspace(
    target_id: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> TargetCleanupReport:
    before = inspect_target_hygiene(target_id, mode="clean-run", project_root=project_root)
    target_dir = Path(before.target_dir)
    agent_dir = target_dir / "agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    before_path = agent_dir / "clean-run-before.json"
    latest_path = agent_dir / "latest-clean-run-cleanup.json"
    _write_json(before_path, before.to_dict())

    deleted_files: list[str] = []
    blocked_reason = None
    status = "completed"
    if before.unknown_files:
        status = "blocked"
        blocked_reason = "unknown target-local files require review before clean-run"
    else:
        for entry in before.files:
            if entry.action not in {
                TargetFileAction.DELETE_ON_CLEAN_RUN,
                TargetFileAction.REGENERATE_ON_CLEAN_RUN,
            }:
                continue
            path = _target_child(target_dir, entry.path)
            if path.exists() and path.is_file():
                path.unlink()
                deleted_files.append(entry.path)

    after = inspect_target_hygiene(target_id, mode="clean-run", project_root=project_root)
    report = TargetCleanupReport(
        target_id=target_id,
        mode="clean-run",
        status=status,
        target_dir=str(target_dir),
        before=before,
        after=after,
        deleted_files=tuple(deleted_files),
        blocked_reason=blocked_reason,
        report_paths={
            "before": str(before_path),
            "latest": str(latest_path),
        },
    )
    _write_json(latest_path, report.to_dict())
    return report


def _classify_target_files(target_dir: Path) -> list[TargetFileInventoryEntry]:
    entries: list[TargetFileInventoryEntry] = []
    for path in sorted(target_dir.rglob("*")):
        if not path.is_file():
            continue
        rel_path = path.relative_to(target_dir).as_posix()
        entries.append(_classify_file(rel_path))
    return entries


def _classify_file(rel_path: str) -> TargetFileInventoryEntry:
    path = Path(rel_path)
    name = path.name
    if path.parts and path.parts[0] == "agent":
        return TargetFileInventoryEntry(
            rel_path,
            TargetFileClass.AGENT_AUDIT,
            TargetFileAction.PRESERVE_AGENT_AUDIT,
            "agent audit/scratch state is separate from durable target facts",
        )
    nested_target_parts = _nested_target_local_parts(path)
    is_top_level = len(path.parts) == 1
    is_target_local = is_top_level or nested_target_parts is not None
    if (is_top_level and name in PROJECT_SOURCE_IMPORT_FACT_FILE_NAMES) or (
        is_target_local and name in SOURCE_IMPORT_FACT_FILES
    ):
        return TargetFileInventoryEntry(
            rel_path,
            TargetFileClass.SOURCE_IMPORT_FACT,
            TargetFileAction.PRESERVE,
            "known source/import fact file",
        )
    if is_target_local and name in {MANUAL_ACTION_LOG_FILE_NAME, DECISION_JOURNAL_FILE_NAME}:
        return TargetFileInventoryEntry(
            rel_path,
            TargetFileClass.LOCAL_MANUAL_STATE,
            TargetFileAction.DELETE_ON_CLEAN_RUN,
            "durable manual/journal state is preserved for continue and reset only in clean-run",
        )
    if is_target_local and name in LOCAL_VERIFIER_STATE_FILE_NAMES:
        return TargetFileInventoryEntry(
            rel_path,
            TargetFileClass.LOCAL_VERIFIER_STATE,
            TargetFileAction.REGENERATE_ON_CLEAN_RUN,
            "local verifier artifacts are current-state evidence and can be regenerated after clean-run",
        )
    if is_target_local and name in OBSOLETE_UI_STATE_FILE_NAMES:
        return TargetFileInventoryEntry(
            rel_path,
            TargetFileClass.OBSOLETE_UI_STATE,
            TargetFileAction.DELETE_ON_CLEAN_RUN,
            "obsolete or local UI state is not durable reversing intent",
        )
    if is_target_local and (name in GENERATED_OUTPUT_FILE_NAMES or name.endswith(GENERATED_OUTPUT_SUFFIXES)):
        return TargetFileInventoryEntry(
            rel_path,
            TargetFileClass.GENERATED_OUTPUT,
            TargetFileAction.REGENERATE_ON_CLEAN_RUN,
            "generated output can be regenerated through project commands",
        )
    return TargetFileInventoryEntry(
        rel_path,
        TargetFileClass.UNKNOWN,
        TargetFileAction.REVIEW_REQUIRED,
        "not covered by the target hygiene allowlist",
    )


def _nested_target_local_parts(path: Path) -> tuple[str, ...] | None:
    if len(path.parts) < 3 or path.parts[0] != "targets":
        return None
    if any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.parts[2:]


def _target_child(target_dir: Path, rel_path: str) -> Path:
    root = target_dir.resolve()
    path = (target_dir / rel_path).resolve()
    path.relative_to(root)
    return path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
