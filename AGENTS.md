# Amiga Game Disassembly Project

## Purpose

LLM-assisted reverse engineering of Amiga game binaries. The goal is a fully
reassemblable, documented disassembly with named symbols, typed data, and
cross-references.

## Spec-Driven M68K Tooling

All M68K tooling is generated from structured data extracted from the Motorola
68000 Programmer's Reference Manual PDF.

```text
PDF -> parser -> JSON knowledge base -> generated tools
                                      -> independent oracle checks
```

Rules:

- Never hardcode M68K knowledge in generated tools.
- If generated code is wrong, fix parser/extraction upstream.
- If the JSON cannot express a required fact, extend the schema and re-extract.
- Parser-asserted KB entries are allowed only with comments that cite the PDF,
  explain why the fact cannot be parsed directly, and state the asserted
  standard interpretation.
- Oracles such as vasm and machine68k/Musashi are black boxes used only for
  verification.

## Agentic Reversing Loop

Before agentic target work, read and follow:

- `docs/agents/reversing-loop.md`
- relevant sections of `docs/proposals/010-agentic-reversing-loop.md`

Agentic target work is useful only when it moves the rendered target source
toward human-quality reconstructed source: clearer symbols, typed data,
structured ranges, verified control/data flow, and documented platform/game
semantics. Do not perform proof, fallback, or makework actions just to exercise
the loop.

Prefer structured durable facts over free-form notes: function/data labels,
app/global slot names, type or field facts, code/data/string/table
classification, API/library semantics, and xref-backed propagation. Comments are
valid only for concrete semantic discoveries when no more structured command
exists.

Do not rely on `reversing_loop inspect` alone for arbitrary candidates; it
currently surfaces review items. Do not commit `.project.json` timestamp-only
changes as meaningful progress. `manual_actions.jsonl` is local target state, so
summarize it in reports unless tracked support code or docs also changed.

## Manual Review State

- C analysis facts are the source of truth for discovered code, data, labels,
  cross-references, and range classification.
- User intervention lives in the per-target Manual Action Log.
- Manual Review Items are regenerated from current analysis facts plus Manual
  Action Log projections.
- `entities.jsonl`, entity overrides, and entity verification status are retired.
  Do not add dependencies on them.

## Target Output

- Per-target output lives in `targets/<name>/`.
- Disassembly output is vasm-compatible `.s`.
- Use symbolic names from C analysis facts, target metadata, and accepted manual
  seeds.
- Hardware register accesses must use `knowledge/amiga-hardware.md`.
- OS library calls must use `knowledge/amiga-os.md`.

## Verification

- Round-trip verification is mandatory for output-affecting changes.
- Never mark manual review work clear unless the relevant reproduction or
  type-specific checks pass.
- Original binaries in `bin/` must never be modified.
- Rebuilt binaries go in `bin/rebuilt/` and are gitignored.

## Local Environment

- `rg` may be unavailable in the sandbox PATH. Use PowerShell
  `Get-ChildItem ... | Select-String ...` as the sandbox fallback, or escalated
  Windows `rg` when needed.
- `uv run` may fail in the sandbox with access denied to the uv-managed Python
  shim.
- Prefer escalated Windows for repo commands that need `uv run`, with inline
  cache:
  `$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run ...`

## Knowledge Files

- `knowledge/m68k.md`
- `knowledge/amiga-hardware.md`
- `knowledge/amiga-os.md`
- `knowledge/game-specific.md`

Load knowledge files on demand.

## Analysis Practice

- Check xrefs before naming or classification.
- Propagate naming from functions to referenced data when justified.
- Prefer descriptive names, e.g. `update_player_position`, not `sub_1234`.
- Record cross-references bidirectionally.
