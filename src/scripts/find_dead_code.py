from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import sys
import tokenize
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ALWAYS_IGNORED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".uv-cache",
    ".venv",
    ".worktrees",
    "__pycache__",
    "bin",
    "build",
    "ext",
    "resources",
    "targets",
    "tmp",
}
GENERATED_DIRS = {"generated"}
GENERATED_SUFFIXES = ("_runtime.c", "_runtime.h", "_tables.c", "_tables.h")
C_FRAGMENT_SUFFIXES = (".inc.c",)
DEFAULT_CHECKS = (
    "c-static-functions",
    "c-static-prototypes",
    "c-external-functions",
    "c-local-typedefs",
    "c-local-macros",
    "disabled-blocks",
    "py-private-defs",
    "py-unused-imports",
)
CHECKS = set(DEFAULT_CHECKS) | {"grep"}
KNOWN_CONFIG_MACROS = {
    "_CRT_SECURE_NO_WARNINGS",
    "NOMINMAX",
    "PY_SSIZE_T_CLEAN",
    "WIN32_LEAN_AND_MEAN",
}
PY_PRIVATE_DEF_EXEMPTIONS = {
    "__all__",
    "__enter__",
    "__exit__",
    "__init__",
    "__iter__",
    "__len__",
    "__next__",
    "__post_init__",
    "__repr__",
    "__str__",
    "_fields_",
}
PY_IMPORT_EXEMPT_MODULES = {"__future__"}


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    check: str
    name: str
    detail: str


@dataclass
class CFile:
    path: Path
    raw: str
    clean: str


@dataclass(frozen=True)
class CFunction:
    name: str
    start: int
    end: int
    line: int
    is_static: bool


@dataclass(frozen=True)
class CPrototype:
    name: str
    start: int
    end: int
    line: int


@dataclass(frozen=True)
class PythonDef:
    path: Path
    name: str
    line: int
    end_line: int
    kind: str
    exempt: bool = False


@dataclass(frozen=True)
class PythonImport:
    path: Path
    name: str
    line: int
    module: str


STATIC_FUNC_RE = re.compile(r"(?m)^[ \t]*static\s+(?!inline\b)[^;{}=]*?\b([A-Za-z_]\w*)\s*\(")
STATIC_PROTO_RE = re.compile(r"(?ms)^[ \t]*static\s+(?!inline\b)[^;{}=]*?\b([A-Za-z_]\w*)\s*\([^;{}]*?;")
EXTERNAL_FUNC_RE = re.compile(
    r"(?m)^[ \t]*(?!static\b)(?!typedef\b)(?!#)[A-Za-z_][A-Za-z0-9_ \t\*]*\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{"
)
HEADER_DECL_RE = re.compile(
    r"(?ms)^[ \t]*(?:extern\s+)?[A-Za-z_][A-Za-z0-9_ \t\*]*\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*;"
)
TYPEDEF_RE = re.compile(r"(?ms)^[ \t]*typedef\b.*?;\s*(?:\r?\n)?")
MACRO_RE = re.compile(r"(?m)^[ \t]*#[ \t]*define[ \t]+([A-Za-z_]\w*)\b")
IF_ZERO_RE = re.compile(r"(?m)^[ \t]*#[ \t]*if[ \t]+0(?:[ \t]|$)")
IDENT_RE = re.compile(r"\b[A-Za-z_]\w*\b")
LOCAL_C_FRAGMENT_INCLUDE_RE = re.compile(r'(?m)^[ \t]*#[ \t]*include[ \t]+"([^"]+\.inc\.c)"')


def _repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _is_c_fragment_path(path: Path) -> bool:
    return path.name.endswith(C_FRAGMENT_SUFFIXES)


def _is_generated_path(path: Path) -> bool:
    if any(part in GENERATED_DIRS for part in path.parts):
        return True
    return path.name.endswith(GENERATED_SUFFIXES)


def _expand_local_c_fragments(path: Path, text: str, include_generated: bool, seen: set[Path] | None = None) -> str:
    seen = set() if seen is None else set(seen)
    seen.add(path.resolve())

    def replace(match: re.Match[str]) -> str:
        include_path = (path.parent / match.group(1)).resolve()
        if _is_generated_path(include_path) and not include_generated:
            return match.group(0)
        if not _is_c_fragment_path(include_path) or include_path in seen or not include_path.is_file():
            return match.group(0)
        return "\n" + _expand_local_c_fragments(include_path, _read_text(include_path), include_generated, seen) + "\n"

    return LOCAL_C_FRAGMENT_INCLUDE_RE.sub(replace, text)


def _iter_repo_files(include_generated: bool, exclude_tests: bool) -> tuple[list[Path], list[Path], list[Path]]:
    c_files: list[Path] = []
    h_files: list[Path] = []
    py_files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        current = Path(dirpath)
        dirnames[:] = [
            name
            for name in dirnames
            if name not in ALWAYS_IGNORED_DIRS
            and (include_generated or name not in GENERATED_DIRS)
            and not (exclude_tests and name == "tests")
        ]
        if exclude_tests and "tests" in current.parts:
            continue
        for filename in filenames:
            path = current / filename
            if not include_generated and _is_generated_path(path):
                continue
            if _is_c_fragment_path(path):
                continue
            suffix = path.suffix.lower()
            if suffix == ".c":
                c_files.append(path)
            elif suffix == ".h":
                h_files.append(path)
            elif suffix == ".py":
                py_files.append(path)
    return sorted(c_files), sorted(h_files), sorted(py_files)


def _strip_c_comments_and_strings(text: str) -> str:
    out: list[str] = []
    i = 0
    in_block_comment = False
    in_line_comment = False
    in_string = False
    in_char = False
    escape = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                out.append(ch)
            else:
                out.append(" ")
            i += 1
            continue
        if in_block_comment:
            if ch == "*" and nxt == "/":
                out.append(" ")
                out.append(" ")
                in_block_comment = False
                i += 2
            else:
                out.append("\n" if ch == "\n" else " ")
                i += 1
            continue
        if in_string or in_char:
            out.append("\n" if ch == "\n" else " ")
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif (in_string and ch == '"') or (in_char and ch == "'"):
                in_string = False
                in_char = False
            i += 1
            continue
        if ch == "/" and nxt == "/":
            out.append(" ")
            out.append(" ")
            in_line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            out.append(" ")
            out.append(" ")
            in_block_comment = True
            i += 2
            continue
        if ch == '"':
            out.append(" ")
            in_string = True
            i += 1
            continue
        if ch == "'":
            out.append(" ")
            in_char = True
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _find_balanced_body(clean: str, brace_offset: int) -> int | None:
    depth = 0
    for index in range(brace_offset, len(clean)):
        ch = clean[index]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                while end < len(clean) and clean[end] in " \t\r\n":
                    end += 1
                return end
    return None


def _find_static_functions(cfile: CFile) -> list[CFunction]:
    functions: list[CFunction] = []
    for match in STATIC_FUNC_RE.finditer(cfile.clean):
        brace = cfile.clean.find("{", match.end())
        semi = cfile.clean.find(";", match.end())
        if brace < 0 or (semi >= 0 and semi < brace):
            continue
        end = _find_balanced_body(cfile.clean, brace)
        if end is None:
            continue
        functions.append(CFunction(match.group(1), match.start(), end, _line_of(cfile.clean, match.start()), True))
    return functions


def _find_external_functions(cfile: CFile) -> list[CFunction]:
    functions: list[CFunction] = []
    for match in EXTERNAL_FUNC_RE.finditer(cfile.clean):
        name = match.group(1)
        if name in {"if", "for", "while", "switch", "return", "sizeof"}:
            continue
        end = _find_balanced_body(cfile.clean, match.end() - 1)
        if end is None:
            continue
        functions.append(CFunction(name, match.start(), end, _line_of(cfile.clean, match.start()), False))
    return functions


def _find_static_prototypes(cfile: CFile) -> list[CPrototype]:
    prototypes: list[CPrototype] = []
    for match in STATIC_PROTO_RE.finditer(cfile.clean):
        prototypes.append(CPrototype(match.group(1), match.start(), match.end(), _line_of(cfile.clean, match.start())))
    return prototypes


def _find_header_declarations(header_files: list[Path]) -> set[str]:
    declarations: set[str] = set()
    for path in header_files:
        clean = _strip_c_comments_and_strings(_read_text(path))
        for match in HEADER_DECL_RE.finditer(clean):
            if "(*" in match.group(0):
                continue
            declarations.add(match.group(1))
    return declarations


def _identifier_counts(text: str) -> Counter[str]:
    return Counter(IDENT_RE.findall(text))


def _identifier_count(text: str, name: str) -> int:
    return len(re.findall(r"\b" + re.escape(name) + r"\b", text))


def _typedef_alias(text: str) -> str | None:
    pointer_alias = re.search(r"\(\s*\*\s*([A-Za-z_]\w*)\s*\)", text)
    if pointer_alias is not None:
        return pointer_alias.group(1)
    matches = re.findall(r"\b([A-Za-z_]\w*)\b\s*(?=;)", text)
    return matches[-1] if matches else None


def _scan_c_static_functions(cfiles: list[CFile]) -> list[Finding]:
    findings: list[Finding] = []
    for cfile in cfiles:
        counts = _identifier_counts(cfile.clean)
        functions = _find_static_functions(cfile)
        prototypes = _find_static_prototypes(cfile)
        for function in functions:
            proto_spans = [(proto.start, proto.end) for proto in prototypes if proto.name == function.name]
            masked_count = _identifier_count(cfile.clean[function.start:function.end], function.name)
            masked_count += sum(_identifier_count(cfile.clean[start:end], function.name) for start, end in proto_spans)
            if counts[function.name] - masked_count <= 0:
                findings.append(
                    Finding(
                        _repo_path(cfile.path),
                        function.line,
                        "c-static-functions",
                        function.name,
                        "static function has no references in its translation unit",
                    )
                )
    return findings


def _scan_c_static_prototypes(cfiles: list[CFile]) -> list[Finding]:
    findings: list[Finding] = []
    for cfile in cfiles:
        functions = {function.name for function in _find_static_functions(cfile)}
        prototypes = _find_static_prototypes(cfile)
        counts = Counter(proto.name for proto in prototypes)
        for proto in prototypes:
            if proto.name not in functions:
                findings.append(
                    Finding(
                        _repo_path(cfile.path),
                        proto.line,
                        "c-static-prototypes",
                        proto.name,
                        "static prototype has no matching definition",
                    )
                )
            elif counts[proto.name] > 1:
                findings.append(
                    Finding(
                        _repo_path(cfile.path),
                        proto.line,
                        "c-static-prototypes",
                        proto.name,
                        "duplicate static prototype",
                    )
                )
    return findings


def _scan_c_external_functions(cfiles: list[CFile], header_decls: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    all_counts: Counter[str] = Counter()
    for cfile in cfiles:
        all_counts.update(_identifier_counts(cfile.clean))
    for cfile in cfiles:
        for function in _find_external_functions(cfile):
            if function.name == "main" or function.name in header_decls:
                continue
            span_count = _identifier_count(cfile.clean[function.start:function.end], function.name)
            if all_counts[function.name] - span_count <= 0:
                findings.append(
                    Finding(
                        _repo_path(cfile.path),
                        function.line,
                        "c-external-functions",
                        function.name,
                        "non-static function is not declared in a header and has no repo references",
                    )
                )
    return findings


def _scan_c_local_typedefs(cfiles: list[CFile]) -> list[Finding]:
    findings: list[Finding] = []
    for cfile in cfiles:
        counts = _identifier_counts(cfile.clean)
        for match in TYPEDEF_RE.finditer(cfile.clean):
            alias = _typedef_alias(match.group(0))
            if alias is None:
                continue
            span_count = _identifier_count(cfile.clean[match.start():match.end()], alias)
            if counts[alias] - span_count <= 0:
                findings.append(
                    Finding(
                        _repo_path(cfile.path),
                        _line_of(cfile.clean, match.start()),
                        "c-local-typedefs",
                        alias,
                        "file-local typedef is not referenced",
                    )
                )
    return findings


def _scan_c_local_macros(cfiles: list[CFile]) -> list[Finding]:
    findings: list[Finding] = []
    for cfile in cfiles:
        counts = _identifier_counts(cfile.clean)
        for match in MACRO_RE.finditer(cfile.clean):
            name = match.group(1)
            if name in KNOWN_CONFIG_MACROS:
                continue
            line_end = cfile.clean.find("\n", match.start())
            if line_end < 0:
                line_end = len(cfile.clean)
            span_count = _identifier_count(cfile.clean[match.start():line_end], name)
            if counts[name] - span_count <= 0:
                findings.append(
                    Finding(
                        _repo_path(cfile.path),
                        _line_of(cfile.clean, match.start()),
                        "c-local-macros",
                        name,
                        "file-local macro is not referenced after its definition",
                    )
                )
    return findings


def _scan_c_disabled_blocks(cfiles: list[CFile], hfiles: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for cfile in cfiles:
        for match in IF_ZERO_RE.finditer(cfile.clean):
            findings.append(
                Finding(_repo_path(cfile.path), _line_of(cfile.clean, match.start()), "disabled-blocks", "#if 0", "disabled C block")
            )
    for path in hfiles:
        clean = _strip_c_comments_and_strings(_read_text(path))
        for match in IF_ZERO_RE.finditer(clean):
            findings.append(Finding(_repo_path(path), _line_of(clean, match.start()), "disabled-blocks", "#if 0", "disabled C block"))
    return findings


def _python_tokens(path: Path) -> list[tuple[str, int]]:
    tokens: list[tuple[str, int]] = []
    try:
        stream = io.StringIO(_read_text(path))
        for token in tokenize.generate_tokens(stream.readline):
            if token.type == tokenize.NAME:
                tokens.append((token.string, token.start[0]))
    except (OSError, tokenize.TokenError, UnicodeDecodeError):
        return []
    return tokens


def _decorator_is_pytest_fixture(decorator: ast.expr) -> bool:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    return (
        isinstance(target, ast.Attribute)
        and target.attr == "fixture"
        and isinstance(target.value, ast.Name)
        and target.value.id == "pytest"
    ) or (isinstance(target, ast.Name) and target.id == "fixture")


def _parse_python_defs(path: Path) -> tuple[list[PythonDef], list[PythonImport], list[Finding]]:
    findings: list[Finding] = []
    defs: list[PythonDef] = []
    imports: list[PythonImport] = []
    try:
        tree = ast.parse(_read_text(path), filename=str(path))
    except SyntaxError as exc:
        findings.append(Finding(_repo_path(path), exc.lineno or 1, "py-parse", path.name, "unable to parse Python file"))
        return defs, imports, findings
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Constant) and node.test.value is False:
            findings.append(Finding(_repo_path(path), node.lineno, "disabled-blocks", "if False", "disabled Python block"))
        if isinstance(node, ast.If) and isinstance(node.test, ast.Constant) and node.test.value == 0:
            findings.append(Finding(_repo_path(path), node.lineno, "disabled-blocks", "if 0", "disabled Python block"))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            exempt = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                _decorator_is_pytest_fixture(decorator) for decorator in node.decorator_list
            )
            defs.append(PythonDef(path, node.name, node.lineno, getattr(node, "end_lineno", node.lineno), kind, exempt))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in PY_IMPORT_EXEMPT_MODULES:
                    continue
                imports.append(PythonImport(path, alias.asname or alias.name.split(".", 1)[0], node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module in PY_IMPORT_EXEMPT_MODULES:
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                imports.append(PythonImport(path, alias.asname or alias.name, node.lineno, node.module or ""))
    return defs, imports, findings


def _scan_py_private_defs(pyfiles: list[Path]) -> tuple[list[Finding], dict[Path, list[tuple[str, int]]]]:
    findings: list[Finding] = []
    all_defs: list[PythonDef] = []
    tokens_by_file: dict[Path, list[tuple[str, int]]] = {}
    for path in pyfiles:
        defs, _, parse_findings = _parse_python_defs(path)
        findings.extend(parse_findings)
        all_defs.extend(defs)
        tokens_by_file[path] = _python_tokens(path)
    all_tokens = [(path, name, line) for path, tokens in tokens_by_file.items() for name, line in tokens]
    for item in all_defs:
        if not item.name.startswith("_") or item.name.startswith("__") or item.name in PY_PRIVATE_DEF_EXEMPTIONS:
            continue
        if item.exempt:
            continue
        refs = [
            (path, line)
            for path, name, line in all_tokens
            if name == item.name and not (path == item.path and item.line <= line <= item.end_line)
        ]
        if not refs:
            findings.append(
                Finding(
                    _repo_path(item.path),
                    item.line,
                    "py-private-defs",
                    item.name,
                    f"private {item.kind} has no token references in Python files",
                )
            )
    return findings, tokens_by_file


def _scan_py_unused_imports(pyfiles: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in pyfiles:
        _, imports, parse_findings = _parse_python_defs(path)
        findings.extend(parse_findings)
        tokens = _python_tokens(path)
        used_names = {name for name, _ in tokens}
        for imported in imports:
            # The import statement itself contributes one token, so require a second occurrence.
            uses = sum(1 for name, line in tokens if name == imported.name and line != imported.line)
            if imported.name not in used_names or uses == 0:
                findings.append(
                    Finding(
                        _repo_path(path),
                        imported.line,
                        "py-unused-imports",
                        imported.name,
                        f"import from {imported.module!r} is not referenced in this file",
                    )
                )
    return findings


def _scan_grep_patterns(paths: list[Path], patterns: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    compiled = [(pattern, re.compile(pattern)) for pattern in patterns]
    for path in paths:
        try:
            lines = _read_text(path).splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            for pattern, regex in compiled:
                if regex.search(line):
                    findings.append(Finding(_repo_path(path), line_no, "grep", pattern, "custom residue pattern matched"))
    return findings


def _dedupe(findings: list[Finding]) -> list[Finding]:
    return sorted(set(findings), key=lambda finding: (finding.check, finding.path, finding.line, finding.name, finding.detail))


def _print_text(findings: list[Finding]) -> None:
    if not findings:
        print("No dead-code candidates found.")
        return
    counts = Counter(finding.check for finding in findings)
    print("Dead-code candidates:")
    current_check = ""
    for finding in findings:
        if finding.check != current_check:
            current_check = finding.check
            print(f"\n[{current_check}]")
        print(f"{finding.path}:{finding.line}: {finding.name}: {finding.detail}")
    print("\nSummary:")
    for check, count in sorted(counts.items()):
        print(f"  {check}: {count}")
    print(f"  total: {len(findings)}")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Locate likely dead code without third-party dependencies.")
    parser.add_argument("--include-generated", action="store_true", help="scan generated source too")
    parser.add_argument("--exclude-tests", action="store_true", help="skip test directories")
    parser.add_argument("--fail-on-findings", action="store_true", help="exit with status 1 when candidates are found")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--check",
        action="append",
        choices=sorted(CHECKS),
        help="run only this check; may be repeated; defaults to all non-grep checks",
    )
    parser.add_argument("--grep", action="append", default=[], help="extra regex residue pattern to search for")
    parser.add_argument("--list-checks", action="store_true", help="print available checks and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.list_checks:
        for check in sorted(CHECKS):
            print(check)
        return 0
    selected = set(args.check or DEFAULT_CHECKS)
    if args.grep:
        selected.add("grep")
    c_paths, h_paths, py_paths = _iter_repo_files(args.include_generated, args.exclude_tests)
    cfiles: list[CFile] = []
    for path in c_paths:
        raw = _expand_local_c_fragments(path, _read_text(path), args.include_generated)
        cfiles.append(CFile(path, raw, _strip_c_comments_and_strings(raw)))
    findings: list[Finding] = []
    if "c-static-functions" in selected:
        findings.extend(_scan_c_static_functions(cfiles))
    if "c-static-prototypes" in selected:
        findings.extend(_scan_c_static_prototypes(cfiles))
    if "c-external-functions" in selected:
        findings.extend(_scan_c_external_functions(cfiles, _find_header_declarations(h_paths)))
    if "c-local-typedefs" in selected:
        findings.extend(_scan_c_local_typedefs(cfiles))
    if "c-local-macros" in selected:
        findings.extend(_scan_c_local_macros(cfiles))
    if "disabled-blocks" in selected:
        findings.extend(_scan_c_disabled_blocks(cfiles, h_paths))
    if "py-private-defs" in selected:
        py_findings, _ = _scan_py_private_defs(py_paths)
        findings.extend(py_findings)
    if "py-unused-imports" in selected:
        findings.extend(_scan_py_unused_imports(py_paths))
    if "grep" in selected:
        findings.extend(_scan_grep_patterns([*c_paths, *h_paths, *py_paths], args.grep))
    findings = _dedupe(findings)
    if args.format == "json":
        print(json.dumps([asdict(finding) for finding in findings], indent=2, sort_keys=True))
    else:
        _print_text(findings)
    return 1 if findings and args.fail_on_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
