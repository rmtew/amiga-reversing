# Proposal 018: Platform Executable Format Knowledge

Status: open. This proposal defines the single top-down cited executable and
object-format authority that Mac OS, Amiga, and Atari ST parsers should use
before target-specific analysis guesses at code/data boundaries.

## Purpose

Amiga, Atari ST, and Classic Mac OS all have fixed retro executable/container
formats. They are no longer moving targets. The project should capture their
standard file structures as cited knowledge, then generate or validate parser
behavior from that knowledge.

The immediate blocker is Proposal 012: Mac CODE rendering was advanced with a
pattern heuristic for `movea.l (a7)+,a0`. That is not enough. The Mac parser
needs cited Segment Loader, CODE resource, A5 world, jump-table, relocation,
and entrypoint facts before its rendered source can be treated as correct.

018 is knowledge/schema first and parser implementation second. Parser work
must consume or validate against the KB; it must not invent accepted executable
rules directly in target or renderer code.

## Authority Shape

018 has two authority forms:

- `docs/platform-executable-formats.md` is the human-readable narrative
  authority: concepts, citations, parser assertions, conflicts, examples, and
  known limits.
- `knowledge/platform_executable_formats.schema.json` and
  `knowledge/platform_executable_formats.json` are the executable authority for
  validation, generated parser checks, and code generation.

The JSON KB cites source documents and fact ids explained by the markdown. The
markdown does not replace structured facts; it explains the interpretation and
why any parser assertion is acceptable.

## Target Knowledge

Each platform executable-format record should describe:

- format identifiers and file/container signatures;
- container nesting and fork/resource/object relationships;
- code, data, bss, relocation, symbol, and metadata regions;
- standard entrypoint rules by file type;
- loader/runtime metadata and fixup semantics;
- standard compiler/linker outputs for the platform;
- citations for every accepted fact;
- parser assertions only when a document is indirect, with the evidence and
  standard interpretation recorded.

The shared schema should be one top-level model with platform extension blocks,
not unrelated per-platform schemas. Core records contain:

```text
platform
format_id
archetype_id
producer / variant / applies_to
identification
containers
regions
relocations
symbols
entrypoints
loader_model
runtime_model
analysis_model
renderer_expectations
unknowns / conflicts / deferred / unsupported
facts[]
```

Important claims have stable fact ids, status, source policy, and citations.
Tooling should be able to report that parser behavior is backed by a specific
fact id such as `macos.code_resource.nonzero.segment_header`.

## Fact States

Accepted parser behavior may consume only:

- `validated`: directly supported by allowed cited sources.
- `parser_asserted`: indirect source or observed behavior plus explicit
  standard interpretation and review status.

Parser behavior may not consume these as accepted facts:

- `candidate`: research/report only; may produce candidate ranges.
- `deferred`: known but not implemented.
- `unsupported`: intentionally out of current parser scope.

Unknowns and conflicts are first-class records. Each records scope, evidence,
blocked behavior, and required parser action: fail closed, emit candidate, emit
placeholder, ignore safely, or block closeout.

## Source Policy

Allowed source types:

- `old_out_of_print`: old no-longer-sold platform manuals/books used as cited
  reference material.
- `modern_compatible`: modern sources with compatible license.
- `project_observed`: committed fixtures, extracted metadata, and parser drift
  tests.
- `parser_asserted`: project-maintained standard interpretation when direct
  documentation is unavailable or indirect.

Excluded source types:

- modern incompatible sources as KB inputs;
- copied large source text in KB records;
- undocumented facts presented as validated.

Each citation records `source_type`, `license_status`, `citation`, and
`fact_status`. Observed fixture bytes can support candidates and parser
assertions, but observed bytes alone cannot validate a general platform rule.

## Model Split

The KB separates these layers:

- `file_structure`: bytes, headers, regions, tables, symbols, relocations.
- `loader_model`: OS loader behavior for those structures.
- `runtime_entry_model`: stack/register/base-pointer state at entry.
- `analysis_model`: how facts become code/data/bss/symbol ranges.

Entrypoints are also typed:

- `file_entrypoint`
- `segment_entrypoint`
- `runtime_entrypoint`
- `exported_entrypoint`
- `callback_entrypoint`
- `analysis_seed_entrypoint`

The current Mac `movea.l (a7)+,a0` boundary is only an
`analysis_seed_entrypoint` / candidate until 018-002 validates or replaces it.

## Archetypes

The KB defines standard target archetypes, not just byte formats:

- `amiga.executable`, `amiga.object`, `amiga.library`, `amiga.device`,
  `amiga.resident`, `amiga.disk_bootblock`
- `atari_st.prg`, `atari_st.tos`, `atari_st.ttp`
- `macos.application_code_resources`, `macos.mpw_tool_code_resources`

Each archetype defines identification, expected containers/regions, entrypoint
model, standard metadata, parser checks, renderer expectations, and unsupported
or deferred areas.

## Output Locations

Canonical source/spec locations:

```text
docs/platform-executable-formats.md
knowledge/platform_executable_formats.schema.json
knowledge/platform_executable_formats.json
```

Generated runtime/check locations:

```text
src/generated/platform_executable_formats.c
src/generated/platform_executable_formats.h
tests/test_platform_executable_formats.py
```

C tests should follow the existing `src/test_*` pattern where parser checks need
native coverage.

## Platform Scope

Mac OS:

- HFS file metadata and Finder type/creator.
- Resource fork map.
- `CODE 0` and nonzero `CODE` resources.
- Segment Loader behavior, A5 world, jump table, inter-segment calls, entry
  conventions, relocation/fixup model, and MPW Link output.
- MPW object/library formats where local docs or examples support them.

Amiga:

- HUNK executable, object, library, resident, device, and LoadSeg behavior.
- Code/data/bss hunks, relocations, symbols, overlays, resident structures, and
  library/device entry conventions.
- Old out-of-print manuals/books, compatible modern sources, project-observed
  facts, and parser assertions where direct documentation is unavailable.

Atari ST:

- PRG/TOS/TTP/GEMDOS executable header, text/data/bss, relocation table,
  symbol table, basepage/entrypoint conventions, and trap ABI links.
- Devpac/EmuTOS/Hatari or manual sources as citations where they define file
  structure and loader behavior.

## Acceptance Criteria

- A shared schema exists for platform executable-format KB records.
- A thin Mac OS proof record exists with the initial schema so schema decisions
  are tested against the 012 blocker, not only abstract examples.
- Mac OS executable parsing rules are backed by local docs/MD/KB citations
  before Proposal 012 can close.
- Amiga and Atari ST records cover their standard executable-bearing formats
  with citations and parser assertions where needed.
- Parser/check scaffolding consumes the KB or validates C parser output against
  the KB.
- Tests reject heuristic-only executable parsing when no cited or asserted
  platform rule exists.
- Target-specific analysis remains separate from standard platform semantics.
- Renderer expectations are derived obligations: output must expose platform
  code/data/bss/entry/relocation facts and must not present one platform as
  another, but exact formatting remains renderer-owned.

## Issue Seeds

018-001. Executable-format KB schema

```text
Define the shared schema and a thin Mac proof record for cited
platform executable/container format facts: identity, archetypes, sections,
relocations, symbols, entrypoints, loader/runtime/analysis models, citations,
parser assertions, unknowns/conflicts/deferred states, renderer expectations,
and generated checks.
```

018-002. Mac OS executable/CODE model

```text
Extract cited Mac OS Segment Loader, resource fork, CODE resource, A5 world,
jump-table, relocation, and entrypoint facts from local MD/docs/KB and MPW
examples. Proposal 012 is blocked on this slice. It must include a migration
plan that downgrades the current `movea.l (a7)+,a0` heuristic to candidate
evidence until cited facts validate or replace it.
```

018-003. Amiga executable/HUNK model

```text
Capture cited Amiga HUNK executable/object/library/resident/device/LoadSeg
facts, including relocations, symbols, BSS, entry conventions, and version
scope.
```

018-004. Atari ST executable model

```text
Capture cited Atari ST PRG/TOS/TTP/GEMDOS executable facts, including
text/data/bss, relocation table, symbols, basepage, entrypoint, and trap ABI
context.
```

018-005. Generated parser/check scaffolding

```text
Generate or validate parser scaffolding from the executable-format KB so C
parsers enumerate standard code/data/bss/reloc/symbol/metadata regions in a
consistent platform way. Generated checks are blocking for new/adopted
KB-backed parser slices and optional reports for legacy parser areas until they
declare `kb_backed: true`.
```

018-006. Heuristic parsing guardrails

```text
Add tests and review checks that prevent heuristic-only executable parsing from
being marked implemented. Heuristics may produce candidates, but accepted parser
rules require citations or explicit parser assertions.
```

## Relationship To 012

Proposal 012 remains open and blocked for executable/CODE correctness until
018-002 provides cited Mac OS executable-format facts and the Mac parser is
updated to consume or validate against them. Existing 012 work is useful
foundation, but the current CODE entry heuristic is only a candidate boundary,
not accepted platform knowledge.

018 sits above 011 and 012 as the shared executable/container format authority.
It does not absorb all platform knowledge; it owns file structure, loader model,
entrypoints, relocations, symbols, code/data/bss boundaries, and renderer
obligations for executable-bearing formats.
