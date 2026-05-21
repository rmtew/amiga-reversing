# Proposal 018: Platform Executable Format Knowledge

Status: open. This proposal defines the cited, per-platform executable and
object-format knowledge layer that Mac OS, Amiga, and Atari ST parsers should
use before target-specific analysis guesses at code/data boundaries.

## Purpose

Amiga, Atari ST, and Classic Mac OS all have fixed retro executable/container
formats. They are no longer moving targets. The project should capture their
standard file structures as cited knowledge, then generate or validate parser
behavior from that knowledge.

The immediate blocker is Proposal 012: Mac CODE rendering was advanced with a
pattern heuristic for `movea.l (a7)+,a0`. That is not enough. The Mac parser
needs cited Segment Loader, CODE resource, A5 world, jump-table, relocation,
and entrypoint facts before its rendered source can be treated as correct.

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
- NDK/RKRM facts plus modern cited manuals such as Thomas Richter's AmigaDOS
  material where appropriate, recording version scope.

Atari ST:

- PRG/TOS/TTP/GEMDOS executable header, text/data/bss, relocation table,
  symbol table, basepage/entrypoint conventions, and trap ABI links.
- Devpac/EmuTOS/Hatari or manual sources as citations where they define file
  structure and loader behavior.

## Acceptance Criteria

- A shared schema exists for platform executable-format KB records.
- Mac OS executable parsing rules are backed by local docs/MD/KB citations
  before Proposal 012 can close.
- Amiga and Atari ST records cover their standard executable-bearing formats
  with citations and parser assertions where needed.
- Parser/check scaffolding consumes the KB or validates C parser output against
  the KB.
- Tests reject heuristic-only executable parsing when no cited or asserted
  platform rule exists.
- Target-specific analysis remains separate from standard platform semantics.

## Issue Seeds

018-001. Executable-format KB schema

```text
Define the shared schema for cited platform executable/container format facts:
identity, sections, relocations, symbols, entrypoints, loader metadata,
runtime conventions, citations, parser assertions, and generated checks.
```

018-002. Mac OS executable/CODE model

```text
Extract cited Mac OS Segment Loader, resource fork, CODE resource, A5 world,
jump-table, relocation, and entrypoint facts from local MD/docs/KB and MPW
examples. Proposal 012 is blocked on this slice.
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
consistent platform way.
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
