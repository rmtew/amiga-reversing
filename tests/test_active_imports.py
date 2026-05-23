from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path


def _repo_python_paths(repo_root: Path, roots: tuple[str, ...]) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        base = repo_root / root
        if base.is_file() and base.suffix == ".py":
            paths.append(base)
        elif base.exists():
            paths.extend(path for path in base.rglob("*.py") if "__pycache__" not in path.parts)
    return paths


def test_active_python_imports_stay_inside_package_boundary() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = """
import importlib
import sys

for module_name in (
    "amiga_reversing.disasm.api",
    "amiga_reversing.disasm.server",
    "amiga_reversing.disasm.c_backend",
    "amiga_reversing.disasm.cli",
    "amiga_reversing.tools.analyze_disk",
    "amiga_reversing.tools.benchmark_target",
    "amiga_reversing.tools.genam_roundtrip",
    "amiga_reversing.tools.import_adf",
    "amiga_reversing.tools.vasm_roundtrip",
    "amiga_reversing.tools.validate_target_seeded_metadata",
):
    importlib.import_module(module_name)

active_machine68k_modules = sorted(name for name in sys.modules if name == "machine68k" or name.startswith("machine68k."))
if active_machine68k_modules:
    print("\\n".join(active_machine68k_modules))
    raise SystemExit(1)
"""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repo_root,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_kb_parser_imports_are_limited_to_maintenance_tools() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    allowed = {
        "src/scripts/amiga_hardware_usage.py",
        "src/scripts/generate_amiga_os_runtime.py",
        "src/scripts/sync_amiga_includes.py",
        "tests/test_active_imports.py",
        "tests/test_parse_ndk.py",
        "tests/test_pdf_to_markdown.py",
        "tests/test_sync_amiga_includes.py",
    }
    offenders: list[str] = []
    for path in _repo_python_paths(repo_root, ("amiga_reversing", "tests", "src/scripts")):
        relative = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "from src.scripts.kb" not in text and "import src.scripts.kb" not in text:
            continue
        if relative.startswith("src/scripts/kb/"):
            continue
        if relative not in allowed:
            offenders.append(relative)

    assert offenders == []


def test_active_package_does_not_contain_kb_parser_package() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    assert not (repo_root / "amiga_reversing" / "kb").exists()


def test_active_web_backend_does_not_use_subprocess_or_platform_clis() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    c_backend = repo_root / "amiga_reversing" / "disasm" / "c_backend.py"
    text = c_backend.read_text(encoding="utf-8")
    assert "subprocess" not in text
    assert "platform_file_cli" not in text
    assert "platform_disk_cli" not in text


def test_active_runtime_code_does_not_invoke_platform_clis() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []
    for package in ("amiga_reversing/disasm", "amiga_reversing/amiga_disk"):
        for path in (repo_root / package).rglob("*.py"):
            relative = path.relative_to(repo_root).as_posix()
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "platform_file_cli" in text or "platform_disk_cli" in text:
                offenders.append(relative)

    assert offenders == []


def test_active_runtime_imports_are_current_package_or_standard_library() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    allowed_roots = {
        "__future__",
        "amiga_reversing",
        "argparse",
        "ast",
        "base64",
        "collections",
        "contextlib",
        "ctypes",
        "dataclasses",
        "datetime",
        "difflib",
        "enum",
        "faulthandler",
        "functools",
        "hashlib",
        "html",
        "http",
        "json",
        "logging",
        "operator",
        "os",
        "pathlib",
        "queue",
        "re",
        "shutil",
        "shlex",
        "subprocess",
        "sys",
        "tempfile",
        "threading",
        "time",
        "traceback",
        "typing",
        "urllib",
        "uuid",
        "zipfile",
    }
    offenders: list[str] = []
    for package in ("amiga_reversing/disasm", "amiga_reversing/amiga_disk", "amiga_reversing/tools"):
        for path in (repo_root / package).rglob("*.py"):
            relative = path.relative_to(repo_root).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots = {alias.name.partition(".")[0] for alias in node.names}
                elif isinstance(node, ast.ImportFrom):
                    roots = (
                        set()
                        if node.module is None or node.level > 0
                        else {node.module.partition(".")[0]}
                    )
                else:
                    continue
                invalid_roots = sorted(
                    root
                    for root in roots
                    if root not in allowed_roots
                    and not (relative == "amiga_reversing/disasm/corpus_usage.py" and root == "src")
                )
                if invalid_roots:
                    offenders.append(f"{relative}: {', '.join(invalid_roots)}")
                    break

    assert offenders == []


def test_disk_python_layer_does_not_load_content_classification_kbs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []
    for path in (repo_root / "amiga_reversing" / "amiga_disk").rglob("*.py"):
        relative = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "amiga_hunk_format.json" in text or "amiga_iff_formats.json" in text:
            offenders.append(relative)

    assert offenders == []


def test_adf_adapter_does_not_own_project_materialization() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    text = (repo_root / "amiga_reversing" / "amiga_disk" / "adf.py").read_text(encoding="utf-8")
    assert "def create_disk_project" not in text
    assert "def import_adf" not in text
    assert "write_source_descriptor" not in text
    assert "create_project_at_path" not in text
