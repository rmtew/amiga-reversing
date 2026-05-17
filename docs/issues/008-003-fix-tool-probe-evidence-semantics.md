# 008-003 Fix Tool Probe Evidence Semantics

Status: Done
Source proposal: `docs/proposals/008-tool-runtime-capability-graph.md`
Created: 2026-05-17

## Problem

Native version probing currently records the first stdout/stderr line as
`version_text` even when the command fails. For example, a tool that rejects
`--version` can be reported with an argparse error as its version.

Probe evidence must distinguish identity evidence from failed probe output.

## Scope

- Make native version probing return structured probe status.
- Record `version_text` only when the probe succeeds and output is actually a
  version/banner.
- Preserve stderr/stdout failure excerpts separately if useful.
- Keep executable stamp as identity evidence even when version probing fails.
- Ensure GenAm remains `hash_only` until emulator-assisted probing exists.

## Acceptance Criteria

- A non-zero `--version` result does not populate `version_text`.
- A failed native probe reports `probe_status=error` or
  `probe_status=unsupported`, with executable stamp still present.
- A successful native probe reports `probe_status=available` and version text.
- CLI/resource payloads expose the corrected evidence.
- Tests cover success, non-zero exit, timeout/OSError, and hash-only tools.

## Verification

```text
focused tool graph probe tests
uv run amiga-tool-registry runtimes
uv run amiga-tool-registry tools
uv run python -m pytest tests\test_tool_graph.py tests\test_tool_registry_cli.py -q
```

## Implementation notes

- Native `--version` probing now records structured `probe_status`.
- Non-zero, timeout, and `OSError` probe results keep `version_text` unset and
  preserve failure excerpts or probe error text separately.
- Executable stamps remain available when the file can be read, even if native
  version probing fails.
- Hash-only tools such as GenAm do not run native version probes.

## Verification result

Passed:

```powershell
uv run python -m pytest tests\test_tool_graph.py tests\test_tool_registry_cli.py -q
uv run ruff check amiga_reversing\disasm\tool_graph.py tests\test_tool_graph.py tests\test_tool_registry_cli.py
uv run amiga-tool-registry runtimes
uv run amiga-tool-registry tools
```
